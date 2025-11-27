from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from admin_panel.decorators import admin_login_required
from .models import Product, Category, ProductLog,ProductImage
from users.models import UserCoupon, User,Coupon
from django.views.decorators.csrf import csrf_exempt
import json
from .serializers import ProductSerializer,CouponSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import status
from django.db import transaction
@admin_login_required
def product_home(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'product_home.html', {'products': products, 'categories': categories})

def product_search(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'product_home.html', {'products': products, 'categories': categories})



@csrf_exempt
def add_product(request):
    if request.method == "POST":
        name = request.POST['name']
        price = request.POST['price']
        category_id = request.POST['category']
        stock = request.POST['stock']
        description = request.POST['description']
        image = request.FILES.get('image')
        try:
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(
                name=name,
                price=price,
                category=category,
                stock=stock,
                description=description,
                image=image,
            )
            images = request.FILES.getlist('images')
            for index, img in enumerate(images, start=1):
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    order=index,
                )
            new_data = {
                "name": product.name,
                "price": str(product.price),
                "stock": product.stock,
                "category": str(product.category) if product.category else None,
            }
            ProductLog.objects.create(
                product=product,
                action="create",
                old_value={},
                new_value=json.dumps(new_data,ensure_ascii=False),
                change_amount=int(stock),
                admin_id=request.session.get('admin_user_id'),
            )

            return JsonResponse({'success': True, "id": product.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "无效请求"})



@admin_login_required
def product_detail(request):
    product_id = request.GET.get("productId")
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})



@csrf_exempt
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        old_stock = product.stock
        old_data = {
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
            "category": str(product.category) if product.category else None,
        }

        product.name = request.POST.get("name", product.name)
        product.price = request.POST.get("price", product.price)
        product.stock = int(request.POST.get("stock", product.stock))
        product.category_id = request.POST.get("category", product.category_id)
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        images = request.FILES.getlist("images")
        if images:
            # 1. 删除旧图片
            ProductImage.objects.filter(product=product).delete()

            # 2. 保存新图片
            for index, img in enumerate(images, start=1):
                ProductImage.objects.create(
                    product=product,
                    image_url=img,
                    order=index,
                )
        change_amount = product.stock - old_stock
        action = request.POST.get("action_choice", "update")
        new_data = {
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
            "category": str(product.category) if product.category else None,
            }

        ProductLog.objects.create(
            product=product,
            action=action,
            old_value=json.dumps(old_data, ensure_ascii=False),
            new_value=json.dumps(new_data, ensure_ascii=False),
            change_amount=change_amount,
            admin_id=request.session.get('admin_user_id'),
        )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})


# ------------------ 删除产品 ------------------
@csrf_exempt
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        old_data = {
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
        }
        new_data = {"status": "已删除"}

        ProductLog.objects.create(
            product=product,
            action="delete",
            old_value=json.dumps(old_data, ensure_ascii=False),
            new_value=json.dumps(new_data, ensure_ascii=False),
            change_amount=0,
            admin_id=request.session.get('admin_user_id'),
        )

        product.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})


# ------------------ 操作日志页面 ------------------
@admin_login_required
def product_log(request):
    logs = ProductLog.objects.select_related("product", "admin").order_by("-created_at")

    formatted_logs = []
    for entry in logs:

        try:
            old_val = json.loads(entry.old_value) if entry.old_value else {}
        except json.JSONDecodeError:
            old_val = entry.old_value or {}

        try:
            new_val = json.loads(entry.new_value) if entry.new_value else {}
        except json.JSONDecodeError:
            new_val = entry.new_value or {}

        formatted_logs.append({
            "product_name": entry.product.name if entry.product else "（已删除）",
            "action": entry.action,
            "old_value": old_val,
            "new_value": new_val,
            "change_amount": entry.change_amount,
            "admin": entry.admin.username if entry.admin else "系统",
            "created_at": entry.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return render(request, "product_log.html", {"logs": formatted_logs})



class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True, context={'request': request})
        print(serializer.data)
        return Response(serializer.data)

class ProductDetailAPIView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data)

def coupon_page(request):
    return render(request,'coupon_management.html')


class CouponListView(APIView):
    """优惠券列表"""
    def get(self, request):
        openid = request.GET.get('openid')
        user = User.objects.get(openid=openid)
        user_points = user.points
        coupons = Coupon.objects.all().order_by("-sort_order", "-id")
        ser = CouponSerializer(coupons, many=True)


        return Response({"code": 200, "data": ser.data,"user_points": user_points})


class CouponAddView(APIView):
    """新增优惠券"""
    def post(self, request):
        ser = CouponSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response({"code": 200, "msg": "created", "data": ser.data})
        return Response({"code": 400, "msg": ser.errors})

class CouponDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            coupon = Coupon.objects.get(id=pk)
        except Coupon.DoesNotExist:
            return Response({"success": False, "error": "Coupon not found"}, status=404)
        data = {
            "id": coupon.id,
            "name": coupon.name,
            "discount_amount": coupon.discount_amount,
            "min_amount": coupon.min_amount,
            "is_exchange": coupon.is_exchange,
            "cost_points": coupon.cost_points,
            "is_active": coupon.is_active,
            "sort_order": coupon.sort_order,
            # 时间格式转成前端可直接使用的字符串
            "start_time": coupon.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": coupon.end_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        return Response({"success": True, **data}, status=200)
class CouponUpdateView(APIView):
    """编辑优惠券"""
    def post(self, request, *args, **kwargs):
        coupon_id = request.data.get("id")
        try:
            coupon = Coupon.objects.get(id=coupon_id)
        except Coupon.DoesNotExist:
            return Response({"code": 404, "msg": "优惠券不存在"})

        ser = CouponSerializer(coupon, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response({"code": 200, "msg": "updated", "data": ser.data})
        return Response({"code": 400, "msg": ser.errors})

class CouponDeleteView(APIView):
    """删除优惠券"""
    def post(self, request):
        coupon_id = request.data.get("id")
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon.delete()
            return Response({"code": 200, "msg": "deleted"})
        except Coupon.DoesNotExist:
            return Response({"code": 404, "msg": "优惠券不存在"})

class CouponExchangeAPIView(APIView):
    def post(self, request):
        openid = request.data.get("openid")
        coupon_id = request.data.get('coupon_id')

        if not coupon_id or not openid:
            return Response({
                "code": 400,
                "msg": "缺少 coupon_id 或 openid"
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(openid=openid)
        except User.DoesNotExist:
            return Response({"code": 404, "msg": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)

        try:
            coupon = Coupon.objects.get(id=coupon_id, is_active=True)
        except Coupon.DoesNotExist:
            return Response({"code": 404, "msg": "优惠券不存在或已失效"}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()

        if not coupon.is_exchange:
            return Response({"code": 400, "msg": "该优惠券不支持积分兑换"})

        if coupon.start_time and now < coupon.start_time:
            return Response({"code": 400, "msg": "优惠券尚未开始兑换"})

        if coupon.end_time and now > coupon.end_time:
            return Response({"code": 400, "msg": "优惠券兑换已结束"})

        if user.points < coupon.cost_points:
            return Response({"code": 400, "msg": "积分不足"})

        try:
            with transaction.atomic():
                # 加锁，防止并发扣积分
                user_locked = User.objects.select_for_update().get(id=user.id)

                if user_locked.points < coupon.cost_points:
                    return Response({"code": 400, "msg": "积分不足"})

                # 扣积分
                user_locked.points -= coupon.cost_points
                user_locked.save()

                # 创建 UserCoupon
                UserCoupon.objects.create(
                    user=user_locked,
                    coupon=coupon,
                )

        except Exception as e:
            import traceback
            print("兑换异常:", e)
            traceback.print_exc()  # 打印详细堆栈
            return Response(
                {"code": 500, "msg": "兑换失败，请稍后重试"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response({'code': 200, 'msg': '兑换成功'})