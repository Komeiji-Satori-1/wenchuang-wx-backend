import json
from django.shortcuts import render,get_object_or_404
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

# 假设 Orders, OrderItems 和 Product 都在当前应用的 models.py 中
from .models import Orders, OrderItems, Product
from users.models import User
from decimal import Decimal
from admin_panel.decorators import admin_login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status








def _get_monthly_revenue_data():
    """获取按月分组的销售总额数据（用于趋势图）。"""

    # 1. ORM 查询：按 Orders 的 created_at 字段按月分组
    monthly_revenue = Orders.objects.filter(
        status='paid'  # 仅统计已支付订单
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_revenue=Sum('total_amount')
    ).order_by('month')

    labels = []
    data = []

    # 2. 格式化数据
    for entry in monthly_revenue:
        # 格式化日期：datetime.date -> 'YYYY-MM' 字符串
        labels.append(entry['month'].strftime('%Y-%m'))
        # 转换 Decimal 为 float，确保 JSON 序列化和 JS 解析不出错
        data.append(float(entry['total_revenue'] or 0))

    return {'labels': labels, 'data': data}


def _get_product_monthly_sales_data():
    """获取所有历史月份，按月按产品分组的销量明细（用于前端 Top 5 动态计算）。"""

    # 1. ORM 查询：从 OrderItems 开始，按 created_at 按月分组，并按 product_name 再次分组
    product_monthly_sales = OrderItems.objects.filter(
        order__status='paid'  # 仅统计已支付订单项
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
            # 格式化月份标签
            'month': entry['month'].strftime('%Y-%m'),
            'product_name': entry['product__name'] or '未知产品',  # 处理可能的空值
            # 确保数量为 float 或 int
            'quantity': float(entry['total_quantity'] or 0)
        })


    # 返回扁平化的列表结构：[{'month': '2024-01', 'product_name': 'A', 'quantity': 150}, ...]
    return processed_data


def order_analysis_home(request):
    """主视图：获取所有图表所需的数据并渲染模板。"""

    # --- 1. 获取数据 ---
    # 图表1：月销售额趋势
    sales_trend_data = _get_monthly_revenue_data()

    # 图表2：月度产品销售明细
    product_detail_data = _get_product_monthly_sales_data()

    # --- 2. JSON 序列化（为前端传递做准备）---
    # 使用 json.dumps() 将 Python 数据结构转换为 JSON 字符串

    context = {
        # 销售额趋势数据
        'sales_labels_json': json.dumps(sales_trend_data['labels']),
        'sales_data_json': json.dumps(sales_trend_data['data']),

        # 产品明细数据（用于前端 Top 5 动态计算）
        'product_detail_json': json.dumps(product_detail_data),
    }
    print(product_detail_data)
    # 3. 渲染模板
    return render(request, 'order_home.html', context)


def order_list_view(request):
    orders = Orders.objects.select_related('user').all().order_by('-created_at')
    return render(request, 'order_list.html', {'orders': orders})

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
    """创建订单接口（模拟）"""
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

        # 创建订单
        order = Orders.objects.create(user=user, total_amount=0, status='pending')

        # 创建订单明细
        for item in items_data:
            try:
                product = Product.objects.get(pk=item['product_id'])
            except Product.DoesNotExist:
                continue
            quantity = int(item['quantity'])
            price = product.price
            total_amount += price * quantity
            OrderItems.objects.create(order=order, product=product, quantity=quantity, price=price)

        # 更新订单总金额
        order.total_amount = total_amount
        order.save()

        return Response({"order_id": order.id, "total_amount": float(total_amount)}, status=status.HTTP_201_CREATED)


class SimulatePayView(APIView):
    """模拟支付接口：直接把订单状态改为 paid"""
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

