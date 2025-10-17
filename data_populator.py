import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.models import F

# 假设您的模型导入路径如下，请根据您的实际应用结构进行修改
try:
    from orders.models import Orders, OrderItems, Product
except ImportError:
    # 如果是在 manage.py shell 中运行，可能需要使用实际的应用名称
    from orders.models import Orders, OrderItems, Product


@transaction.atomic
def populate_test_data(months_to_populate=4, orders_per_month=40):
    """
    生成跨越指定月数的随机订单数据。
    """
    print("--- 开始生成测试数据 ---")

    # --- 1. 清理旧数据（可选，但推荐） ---
    # Orders.objects.all().delete()
    # OrderItems.objects.all().delete()
    # Product.objects.all().delete()
    # print("旧的订单和产品数据已清除。")

    # --- 2. 创建测试产品 ---
    product_names = [
        "A. 智能降噪耳机",
        "B. 4K高清显示器",
        "C. 便携式充电宝",
        "D. 机械键盘"
    ]
    products_to_create = [Product(name=name) for name in product_names]

    # 确保 Product 表中有数据
    if Product.objects.count() == 0:
        Product.objects.bulk_create(products_to_create)
        print(f"创建了 {len(products_to_create)} 个测试产品。")
    else:
        # 如果已有产品，则获取它们
        products_to_create = list(Product.objects.filter(name__in=product_names))
        if len(products_to_create) < len(product_names):
            print("警告：数据库中未找到所有预期的测试产品，请确保数据库已同步。")

    products = products_to_create

    # --- 3. 生成历史订单和订单项 ---
    today = timezone.now()
    all_order_items = []

    # 遍历要填充的月数
    for month in range(months_to_populate):
        # 计算该月的开始日期（例如：3个月前的月初）
        month_start_date = today.replace(day=1) - timedelta(days=30 * month)
        month_end_date = month_start_date + timedelta(days=30)

        # 在该月生成指定数量的订单
        for _ in range(orders_per_month):

            # a. 随机选择该月的一个日期作为订单创建时间
            days_in_month = (month_end_date - month_start_date).days
            random_day_offset = random.randint(0, days_in_month)
            order_date = month_start_date + timedelta(days=random_day_offset, hours=random.randint(0, 23),
                                                      minutes=random.randint(0, 59))

            # b. 创建 Orders 实例 (total_amount 先给个占位符，后面会更新)
            order = Orders.objects.create(
                status='paid',
                total_amount=Decimal('0.00'),
                create_at=order_date
            )

            # c. 为该订单创建随机数量的 OrderItems (1到3个不同产品)
            num_items = random.randint(1, 3)
            selected_products = random.sample(products, num_items)

            order_total = Decimal('0.00')

            for product in selected_products:
                quantity = random.randint(1, 10)
                # 随机生成一个价格基础，以便计算总金额
                base_price = Decimal(random.randint(10, 500)) / Decimal('1.00')
                price = base_price + Decimal(random.randint(0, 99)) / Decimal('100.00')

                item_total = price * quantity
                order_total += item_total

                all_order_items.append(
                    OrderItems(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=price,
                        create_at=order_date  # OrderItem 的时间与 Order 保持一致
                    )
                )

            # d. 更新 Order 的 total_amount
            order.total_amount = order_total
            order.save()

    # d. 批量插入所有 OrderItems
    OrderItems.objects.bulk_create(all_order_items)

    print(f"成功创建了 {orders_per_month * months_to_populate} 个订单。")
    print(f"成功创建了 {len(all_order_items)} 个订单项。")
    print("--- 数据生成完成，请重新启动服务器测试图表 ---")


# 运行函数
if __name__ == "__main__":
    populate_test_data()
