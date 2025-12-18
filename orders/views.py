import time
import json
import uuid
import logging
import traceback
from decimal import Decimal

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from .models import Orders, OrderItems, Product,Payment
from users.models import User, Address, Coupon, UserCoupon
from admin_panel.decorators import admin_login_required

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from .serializers import OrderSerializer, OrderDetailSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework import permissions

from orders.wechat_pay.utils import (
    wechat_post,
    build_jsapi_pay_params
)
from orders.wechat_pay.notify import decrypt_wechat_resource

logger = logging.getLogger(__name__)


def _get_monthly_revenue_data():
    monthly_revenue = Orders.objects.filter(
        status='paid'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_revenue=Sum('total_amount')
    ).order_by('month')

    labels = []
    data = []

    for entry in monthly_revenue:
        labels.append(entry['month'].strftime('%Y-%m'))
        data.append(float(entry['total_revenue'] or 0))

    return {'labels': labels, 'data': data}


def _get_product_monthly_sales_data():
    product_monthly_sales = OrderItems.objects.filter(
        order__status='paid'
    ).annotate(
        month=TruncMonth('create_at')
    ).values(
        'month',
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('month', 'product__name')

    processed_data = []
    for entry in product_monthly_sales:
        processed_data.append({
            'month': entry['month'].strftime('%Y-%m'),
            'product_name': entry['product__name'] or '未知产品',
            'quantity': float(entry['total_quantity'] or 0)
        })
    return processed_data


@admin_login_required
def order_analysis_home(request):
    sales_trend_data = _get_monthly_revenue_data()
    product_detail_data = _get_product_monthly_sales_data()

    context = {
        'sales_labels_json': json.dumps(sales_trend_data['labels']),
        'sales_data_json': json.dumps(sales_trend_data['data']),
        'product_detail_json': json.dumps(product_detail_data),
    }

    return render(request, 'order_home.html', context)


@admin_login_required
def order_list_view(request):
    orders = Orders.objects.select_related('user').all().order_by('-created_at')
    return render(request, 'order_list.html', {'orders': orders})


@admin_login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Orders, pk=order_id)

    # 正确获取 items（不会报错）
    items = order.items.select_related('product').all()

    # 正确获取 payments（关键点）
    payment = get_object_or_404(Payment,order=order)
    print(payment.transaction_id)
    # 计算小计
    for item in items:
        item.subtotal = item.quantity * item.price

    return render(request, 'order_detail.html', {
        'order': order,
        'items': items,
        'payments': payment,
    })

# ---------------------------
# API helpers
# ---------------------------
def json_ok(data=None, msg="ok"):
    payload = {"success": True, "code": 200, "msg": msg}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status.HTTP_200_OK)


def json_error(msg="error", code=400, http_status=status.HTTP_400_BAD_REQUEST, extra=None):
    payload = {"success": False, "code": code, "msg": msg}
    if extra:
        payload.update(extra)
    return Response(payload, status=http_status)


def get_user_by_openid(openid):
    try:
        return User.objects.get(openid=openid)
    except User.DoesNotExist:
        return None


# ---------------------------
# CreateOrderView: 创建未支付订单（不加积分、不扣库存）
# ---------------------------
class CreateOrderView(APIView):
    def post(self, request):
        try:
            openid = request.data.get("openid")
            method = request.data.get("method")
            items_data = request.data.get("items", [])

            if not openid or not items_data:
                return json_error("参数不完整", code=400)

            user = get_user_by_openid(openid)
            if not user:
                return json_error("用户不存在", code=400)

            shipping_fee = Decimal(12) if method == "delivery" else Decimal(0)
            total_amount = Decimal(0)

            # 先创建未支付订单
            order = Orders.objects.create(
                user=user,
                method=method,
                total_amount=0,
                shipping_fee=shipping_fee,
                discount_amount=0,
                pay_amount=0,
                status="pending",
            )
            order.encrypted_id = uuid.uuid4().hex
            order.save()

            # 创建订单商品项（不扣库存）
            for item in items_data:
                product = Product.objects.get(pk=item["product_id"])
                quantity = int(item["quantity"])
                total_amount += product.price * quantity

                OrderItems.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                )

            # 更新订单金额（不含优惠）
            order.total_amount = total_amount
            order.pay_amount = total_amount + shipping_fee
            order.save()

            return json_ok({
                "order_id": order.id,
                "encrypted_id": order.encrypted_id,
                "total_amount": float(order.total_amount),
                "shipping_fee": float(order.shipping_fee),
                "discount_amount": float(order.discount_amount),
                "pay_amount": float(order.pay_amount),
            }, msg="创建订单成功")

        except Product.DoesNotExist:
            return json_error("商品不存在", code=404)
        except Exception:
            logger.error("CreateOrderView error: %s", traceback.format_exc())
            return json_error("服务器内部错误", code=500, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------
# ConfirmOrderView: 绑定地址/优惠券并由后端重新计算金额
# ---------------------------
class ConfirmOrderView(APIView):
    def post(self, request):
        try:
            # 前端可以传 encrypted_id 或 order_id，优先使用 encrypted_id（更安全）
            encrypted_id = request.data.get("encrypted_id")
            order_id = request.data.get("order_id")
            address_id = request.data.get("address_id")
            coupon_id = request.data.get("coupon_id")
            openid = request.data.get("openid")

            if not openid:
                return json_error("缺少 openid", code=401)

            user = get_user_by_openid(openid)
            if not user:
                return json_error("用户不存在", code=404)

            # 获取订单
            if encrypted_id:
                try:
                    order = Orders.objects.get(encrypted_id=encrypted_id)
                except Orders.DoesNotExist:
                    return json_error("订单不存在", code=404)
            else:
                try:
                    order = Orders.objects.get(id=order_id)
                except Orders.DoesNotExist:
                    return json_error("订单不存在", code=404)

            # 验证订单归属
            if order.user_id != user.id:
                return json_error("订单不属于该用户", code=403, http_status=status.HTTP_403_FORBIDDEN)

            # 绑定地址（验证地址属于用户）
            if address_id:
                try:
                    addr = Address.objects.get(pk=address_id, user=user)
                    order.address = addr
                except Address.DoesNotExist:
                    return json_error("地址不存在或不属于当前用户", code=400)

            # 优惠券验证
            discount_amount = Decimal(0)
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(pk=coupon_id, is_active=True)
                except Coupon.DoesNotExist:
                    return json_error("优惠券不存在或已失效", code=400)

                user_coupon = UserCoupon.objects.filter(user=user, coupon=coupon, is_used=False).first()
                print("user_coupon",user_coupon)
                if not user_coupon:
                    return json_error("该优惠券不可用", code=400)

                # 检查最小消费金额门槛（若有）
                if coupon.min_amount and order.total_amount < Decimal(coupon.min_amount):
                    return json_error("不满足优惠券最低消费条件", code=400)

                discount_amount = Decimal(coupon.discount_amount or 0)

                order.user_coupon = user_coupon
                print("order.user_coupon:", order.user_coupon)

            # 重新计算订单金额（由后端决定）
            total_amount = Decimal(order.total_amount or 0)
            shipping_fee = Decimal(order.shipping_fee or 0)
            pay_amount = total_amount + shipping_fee - discount_amount
            if pay_amount < 0:
                pay_amount = Decimal(0)

            order.discount_amount = discount_amount
            order.pay_amount = pay_amount
            order.save()

            return json_ok({
                "pay_amount": float(pay_amount),
                "discount_amount": float(discount_amount)
            }, msg="计算成功")

        except Exception:
            logger.error("ConfirmOrderView error: %s", traceback.format_exc())
            return json_error("服务器内部错误", code=500, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------
# SimulatePayView: 安全的模拟支付（事务、校验、扣库存、标记优惠券、加积分）
# ---------------------------
class SimulatePayView(APIView):
    @transaction.atomic
    def post(self, request):

        try:
            encrypted_id = request.data.get("encrypted_id")
            order_id = request.data.get("order_id")
            openid = request.data.get("openid")
            coupon_id = request.data.get("couponId")  # 前端保留的 key，不信任

            if not openid:
                return json_error("缺少 openid", code=401)

            user = get_user_by_openid(openid)
            if not user:
                return json_error("用户不存在", code=404)

            # 获取并锁定订单（优先 encrypted_id）
            try:
                if encrypted_id:
                    order = Orders.objects.select_for_update().get(encrypted_id=encrypted_id)
                else:
                    order = Orders.objects.select_for_update().get(pk=order_id)
            except Orders.DoesNotExist:
                return json_error("订单不存在", code=404)

            # 验证订单归属
            if order.user_id != user.id:
                return json_error("订单不属于当前用户", code=403, http_status=status.HTTP_403_FORBIDDEN)

            if order.status == "paid":
                return json_ok({"order_id": order.id, "msg": "订单已支付"})

            # 后端重新确认最终金额（防篡改）
            total_amount = Decimal(order.total_amount or 0)
            shipping_fee = Decimal(order.shipping_fee or 0)
            discount_amount = Decimal(order.discount_amount or 0)

            # 如果前端传了 coupon_id，必须再次核验并确认为本用户所有
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(pk=coupon_id, is_active=True)
                except Coupon.DoesNotExist:
                    return json_error("优惠券不存在或已失效", code=400)
                user_coupon = UserCoupon.objects.filter(user=user, coupon=coupon, is_used=False).first()
                print("user_coupon",user_coupon)
                if not user_coupon:
                    return json_error("该优惠券不可用", code=400)
                # 检查门槛
                if coupon.min_amount and total_amount < Decimal(coupon.min_amount):
                    return json_error("不满足优惠券最低消费条件", code=400)
                # 使用后覆盖 discount_amount（以 coupon 为准）
                discount_amount = Decimal(coupon.discount_amount or 0)

            pay_amount = total_amount + shipping_fee - discount_amount
            if pay_amount < 0:
                pay_amount = Decimal(0)

            # 再次检查库存并扣减（在事务内）
            for item in order.items.select_related('product').all():
                product = item.product
                if product.stock < item.quantity:
                    return json_error(f"库存不足：{product.name}", code=400)
                product.stock = product.stock - item.quantity
                product.save()

            # 标记优惠券为已用（如果有）
            if coupon_id and discount_amount > 0:
                user_coupon.is_used = True
                # 若模型有记录使用时间字段，则记录
                if hasattr(user_coupon, 'used_at'):
                    user_coupon.used_at = timezone.now()
                user_coupon.save()

            # 更新订单状态与金额
            order.discount_amount = discount_amount
            order.pay_amount = pay_amount
            order.status = "paid"
            # 如果前端传 address_id，在这里验证并绑定
            address_id = request.data.get("address_id")
            if address_id:
                try:
                    addr = Address.objects.get(pk=address_id, user=user)
                    order.address = addr
                except Address.DoesNotExist:
                    return json_error("地址不存在或不属于当前用户", code=400)

            order.save()
            Payment.objects.create(
                order=order,
                payment_method="wechat",  # 模拟微信支付
                amount=order.pay_amount,
                status="paid",
                transaction_id=f"wx_{uuid.uuid4().hex[:18]}",  # 自动生成交易号
                paid_at=timezone.now()
            )
            # 赠送积分（在事务内，再次锁用户记录以防并发）
            try:
                user_locked = User.objects.select_for_update().get(pk=user.id)
                # 如果 points 是 Integer/Decimal — 保持类型一致
                points = (order.pay_amount or Decimal(0)) * Decimal(2)
                user_locked.points = (user_locked.points or Decimal(0)) + points
                user_locked.save()
            except Exception:
                # 如果用户积分更新失败，记录日志但不回滚前面已经完成的扣库存/订单状态
                # 可根据业务决定是否回滚：此处选择回滚事务以保证原子性
                logger.error("给用户加积分失败，回滚事务: %s", traceback.format_exc())
                raise

            return Response({
                "success": True,
                "code": 200,
                "msg": "支付成功",
                "data": {
                    "order_id": order.id,
                    "pay_amount": float(pay_amount),
                    "points_gained": float(points)
                }
            })

        except Orders.DoesNotExist:
            return json_error("订单不存在", code=404)
        except Product.DoesNotExist:
            return json_error("商品不存在", code=404)
        except Exception:
            logger.error("SimulatePayView error: %s", traceback.format_exc())
            return json_error("服务器内部错误", code=500, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------
# Pagination / List / Detail / Pay / Cancel Views
# ---------------------------
class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20


class UserOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        # request.user 是 Django auth user，需要映射到 User 表
        try:
            user = User.objects.get(auth_user=request.user)
        except User.DoesNotExist:
            return json_error("用户不存在", code=404)
        paginator = OrderPagination()
        orders = Orders.objects.filter(user=user.id).order_by('-created_at')
        page = paginator.paginate_queryset(orders, request)
        serializer = OrderSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class OrderDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, encrypted_id):
        try:
            order = Orders.objects.get(encrypted_id=encrypted_id)
        except Orders.DoesNotExist:
            return Response({"error": "订单不存在"}, status=404)

        serializer = OrderDetailSerializer(order, context={'request': request})
        return Response(serializer.data)


class OrderPayAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, encrypted_id):
        # 这里仍然是简易支付（供后台用户使用），保持现状
        order = get_object_or_404(Orders, encrypted_id=encrypted_id, user=request.user)

        if order.status != "pending":
            return Response({"detail": "该订单不需要支付"}, status=400)

        order.status = "paid"
        order.save()

        return Response({"message": "支付成功"})


class OrderCancelAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, encrypted_id):
        order = get_object_or_404(Orders, encrypted_id=encrypted_id)

        if order.status != "pending":
            return Response({"detail": "订单当前状态不可取消"}, status=400)

        order.status = "cancelled"
        order.save()

        return Response({"message": "订单已取消"})


class WechatPayCreateView(APIView):
    """
    微信支付 JSAPI 下单
    """

    @transaction.atomic
    def post(self, request):
        try:
            openid = request.data.get("openid")
            encrypted_id = request.data.get("encrypted_id")
            order_id = request.data.get("order_id")

            if not openid:
                return json_error("缺少 openid", code=401)

            user = get_user_by_openid(openid)
            if not user:
                return json_error("用户不存在", code=404)

            # 1️⃣ 获取订单（加锁，防止并发）
            try:
                if encrypted_id:
                    order = Orders.objects.select_for_update().get(
                        encrypted_id=encrypted_id
                    )
                else:
                    order = Orders.objects.select_for_update().get(pk=order_id)
            except Orders.DoesNotExist:
                return json_error("订单不存在", code=404)

            # 2️⃣ 校验订单归属
            if order.user_id != user.id:
                return json_error("订单不属于当前用户", code=403)

            # 3️⃣ 校验订单状态
            if order.status != "pending":
                return json_error("订单状态不可支付", code=400)

            # 4️⃣ 计算最终支付金额（以数据库为准）
            pay_amount = Decimal(order.pay_amount or 0)
            if pay_amount <= 0:
                return json_error("支付金额异常", code=400)

            total_fee = int(pay_amount * 100)  # 单位：分
            if not order.out_trade_no:
                order.out_trade_no = order.encrypted_id
                order.save(update_fields=["out_trade_no"])
            body = {
                "appid": settings.WX_APPID,
                "mchid": settings.WX_MCHID,
                "description": f"订单 {order.id}",
                "out_trade_no": order.out_trade_no,
                "notify_url": settings.WX_NOTIFY_URL,
                "amount": {
                    "total": total_fee,
                    "currency": "CNY"
                },
                "payer": {
                    "openid": openid
                }
            }

            resp = wechat_post(
                "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi",
                body
            )

            prepay_id = resp.get("prepay_id")
            if not prepay_id:
                return json_error("微信下单失败", code=500)

            # 7️⃣ 构造前端支付参数
            pay_params = build_jsapi_pay_params(prepay_id)

            return json_ok({
                "order_id": order.id,
                "out_trade_no": order.out_trade_no,
                "pay_amount": float(pay_amount),
                "pay_params": pay_params
            })

        except Exception as e:
            return json_error(
                f"微信支付下单异常: {str(e)}",
                code=500,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class WechatPayNotifyView(APIView):
    """
    微信支付成功回调
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            body = request.data

            # 1️⃣ 只处理成功事件
            if body.get("event_type") != "TRANSACTION.SUCCESS":
                return Response({"code": "SUCCESS"})

            # 2️⃣ 解密 resource
            resource = body.get("resource")
            data = decrypt_wechat_resource(resource)

            out_trade_no = data.get("out_trade_no")
            transaction_id = data.get("transaction_id")
            payer_openid = data.get("payer", {}).get("openid")
            total_fee = data.get("amount", {}).get("total")  # 分

            if not out_trade_no or not transaction_id:
                logger.error("微信回调数据缺失: %s", data)
                return Response({"code": "SUCCESS"})

            with transaction.atomic():

                # 3️⃣ 锁订单（幂等核心）
                try:
                    order = Orders.objects.select_for_update().get(
                        out_trade_no=out_trade_no
                    )
                except Orders.DoesNotExist:
                    logger.error("订单不存在 out_trade_no=%s", out_trade_no)
                    return Response({"code": "SUCCESS"})

                # 4️⃣ 已支付直接返回（幂等）
                if order.status == "paid":
                    return Response({"code": "SUCCESS"})

                # 5️⃣ 校验金额
                pay_amount = Decimal(order.pay_amount or 0)
                if int(pay_amount * 100) != total_fee:
                    logger.error("金额不一致 order=%s wechat=%s", pay_amount, total_fee)
                    return Response({"code": "SUCCESS"})

                # 6️⃣ 扣库存
                for item in order.items.select_related("product").all():
                    product = item.product
                    if product.stock < item.quantity:
                        raise Exception(f"库存不足：{product.name}")
                    product.stock -= item.quantity
                    product.save()

                # 7️⃣ 标记优惠券
                if order.user_coupon:
                    user_coupon = order.user_coupon
                    user_coupon.is_used = True
                    if hasattr(user_coupon, "used_at"):
                        user_coupon.used_at = timezone.now()
                    user_coupon.save()

                # 8️⃣ 更新订单
                order.status = "paid"
                order.save(update_fields=["status"])

                # 9️⃣ 创建支付记录
                Payment.objects.create(
                    order=order,
                    payment_method="wechat",
                    amount=order.pay_amount,
                    status="paid",
                    transaction_id=transaction_id,
                    paid_at=timezone.now()
                )

                # 🔟 送积分
                user = order.user
                user_locked = User.objects.select_for_update().get(pk=user.id)
                points = Decimal(order.pay_amount) * Decimal(2)
                user_locked.points = (user_locked.points or Decimal(0)) + points
                user_locked.save()

            # 微信要求：无论你内部发生什么，只要处理过就返回 SUCCESS
            return Response({"code": "SUCCESS"})

        except Exception:
            logger.error("WechatPayNotifyView error: %s", traceback.format_exc())
            return Response({"code": "SUCCESS"})