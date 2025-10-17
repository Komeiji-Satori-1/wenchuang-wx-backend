from django.db import models
from users.models import User
from products.models import Product
# Create your models here.

class Orders(models.Model):
    STATUS_CHOICES = [
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'  # 对应 MySQL 表名
        managed = False           # Django 不管理该表（表已存在）

    def __str__(self):
        return f"订单 {self.id} - 用户 {self.user.openid}:{self.user.nickname} - 金额 {self.total_amount}"

class OrderItems(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Orders, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    create_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'order_item'
        managed = False

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (¥{self.price})"

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('wechat', '微信支付'),
        ('alipay', '支付宝'),
        ('card', '银行卡'),
    ]

    order = models.ForeignKey(Orders, related_name='payments', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='unpaid')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'payment'
        managed = False

    def __str__(self):
        return f"{self.payment_method} - {self.status}"