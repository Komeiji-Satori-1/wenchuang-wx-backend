import json
from django.shortcuts import render,get_object_or_404
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth
from .models import Orders, OrderItems, Product
from users.models import User
from decimal import Decimal
from admin_panel.decorators import admin_login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from .serializers import OrderSerializer
from rest_framework.authentication import TokenAuthentication







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
    print(product_monthly_sales.query)
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
    print(product_detail_data)

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
        print(item.subtotal)

    print(items)
    context = {
        'order': order,
        'items': items,
        'payments': payments,
    }
    print(context)
    return render(request, 'order_detail.html', context)

class CreateOrderView(APIView):
    def post(self, request):
        openid = request.data.get('openid')
        items_data = request.data.get('items', [])  # [{"product_id": 1, "quantity": 2}, ...]

        if not openid or not items_data:
            return Response({"error": "参数不完整"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.filter(openid=openid).first()
        except User.DoesNotExist:
            return Response({"error": "用户不存在"}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = Decimal(0)

        order = Orders.objects.create(user=user, total_amount=0, status='pending')

        for item in items_data:
            try:
                product = Product.objects.get(pk=item['product_id'])
            except Product.DoesNotExist:
                continue
            quantity = int(item['quantity'])
            price = product.price
            total_amount += price * quantity
            OrderItems.objects.create(order=order, product=product, quantity=quantity, price=price)


        order.total_amount = total_amount
        order.save()

        return Response({"order_id": order.id, "total_amount": float(total_amount)}, status=status.HTTP_201_CREATED)


class SimulatePayView(APIView):
    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({"success": False, "message": "缺少订单ID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Orders.objects.get(pk=order_id)
            order.status = 'paid'
            order.save()
            return Response({"success": True, "message": "支付成功"})
        except Orders.DoesNotExist:
            return Response({"success": False, "message": "订单不存在"}, status=status.HTTP_404_NOT_FOUND)

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
        print(serializer.data)
        return paginator.get_paginated_response(serializer.data)

