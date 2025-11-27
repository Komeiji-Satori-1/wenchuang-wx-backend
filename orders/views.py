import json
import uuid
from django.shortcuts import render,get_object_or_404
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth
from .models import Orders, OrderItems, Product
from users.models import User, Address, Coupon, UserCoupon
from decimal import Decimal
from admin_panel.decorators import admin_login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from .serializers import OrderSerializer,OrderDetailSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework import permissions







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
    # 2. 格式化数据
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
    items = order.items.select_related('product').all()  # 订单明细
    payments = order.payments.all()  # 支付信息
    for item in items:
        item.subtotal = item.quantity * item.price

    context = {
        'order': order,
        'items': items,
        'payments': payments,
    }
    return render(request, 'order_detail.html', context)

class CreateOrderView(APIView):
    def post(self, request):
        openid = request.data.get("openid")
        method = request.data.get("method")
        items_data = request.data.get("items", [])

        if not openid or not items_data:
            return Response({"code": 400, "msg": "参数不完整"})

        user = User.objects.filter(openid=openid).first()
        if not user:
            return Response({"code": 400, "msg": "用户不存在"})

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

        # 创建订单商品项
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

        return Response({
            "code": 200,
            "order_id": order.id,
            "encrypted_id": order.encrypted_id,
            "total_amount": total_amount,
            "shipping_fee": shipping_fee,
            "discount_amount": order.discount_amount,
            "pay_amount": order.pay_amount,
        })

class ConfirmOrderView(APIView):
    def post(self, request):
        order_id = request.data.get("order_id")
        address_id = request.data.get("address_id")
        coupon_id = request.data.get("coupon_id")
        print(coupon_id)
        order = Orders.objects.get(id=order_id)

        # 绑定地址
        if address_id:
            order.address_id = address_id

        # 优惠券验证
        discount_amount = Decimal(0)
        if coupon_id:
            user_coupon = UserCoupon.objects.filter(
                user=order.user,
                coupon_id=coupon_id,
                is_used=False
            ).first()
            if not user_coupon:
                return Response({"code": 400, "msg": "优惠券不可用"})

            discount_amount = user_coupon.coupon.discount_amount
            print("折扣：",discount_amount)
        #重新计算订单金额
        pay_amount = order.total_amount + order.shipping_fee - discount_amount
        print("订单总额：",pay_amount)
        order.discount_amount = discount_amount
        order.pay_amount = pay_amount
        order.save()

        return Response({
            "code": 200,
            "pay_amount": float(pay_amount)
        })



from django.db import transaction

class SimulatePayView(APIView):
    @transaction.atomic
    def post(self, request):
        order_id = request.data.get("order_id")
        openid = request.data.get("openid")
        coupon_id = request.data.get("couponId")
        order = Orders.objects.select_for_update().get(id=order_id)

        if order.status == "paid":
            return Response({"code": 200, "msg": "订单已支付"})

        # 1. 扣库存
        for item in order.items.all():
            product = item.product
            if product.stock < item.quantity:
                return Response({"code": 400, "msg": f"{product.name} 库存不足"})
            product.stock -= item.quantity
            product.save()

        # 2. 标记优惠券使用
        if order.discount_amount > 0:
            user_coupon = UserCoupon.objects.filter(
                user=order.user,
                coupon_id=coupon_id,
                is_used=False
            ).first()
            if user_coupon:
                user_coupon.is_used = True
                user_coupon.save()

        # 3. 设置订单状态
        order.status = "paid"
        order.save()

        # 4. 付款成功 → 赠送积分
        user = User.objects.get(openid=openid)
        points = order.pay_amount * 2
        user.points += points
        user.save()

        return Response({"code": 200, "msg": "支付成功","success": True})


class OrderPagination(PageNumberPagination):
    page_size = 5  # 每页 5 条
    page_size_query_param = 'page_size'
    max_page_size = 20

class UserOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    def get(self, request):
        user = User.objects.get(auth_user=request.user)
        paginator = OrderPagination()
        user_info=User.objects.get(openid=user.openid)
        uid=user_info.id
        orders = Orders.objects.filter(user=uid).order_by('-created_at')
        page = paginator.paginate_queryset(orders, request)
        serializer = OrderSerializer(page, many=True,context={'request': request})
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
        order = get_object_or_404(Orders, encrypted_id=encrypted_id, user=request.user)

        if order.status != "pending":
            return Response({"detail": "该订单不需要支付"}, status=400)

        # 简易支付模拟 —— 你的 Payment 表也可在此创建记录
        order.status = "paid"
        order.save()

        return Response({"message": "支付成功"})

class OrderCancelAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, encrypted_id):
        order = get_object_or_404(Orders, encrypted_id=encrypted_id, user=request.user)

        if order.status != "pending":
            return Response({"detail": "订单当前状态不可取消"}, status=400)

        order.status = "cancelled"
        order.save()

        return Response({"message": "订单已取消"})
