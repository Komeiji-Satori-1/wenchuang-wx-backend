from django.db import models
from admin_panel.models import AdminUser

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'category'
        managed = False

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        null=True, blank=True
    )

    class Meta:
        db_table = 'product'
        managed = False

    def __str__(self):
        return self.name


class ProductLog(models.Model):
    ACTION_CHOICES = [
        ("create", "创建"),
        ("update", "修改"),
        ("delete", "删除"),
        ("stock_in", "进货"),
        ("stock_out", "售出"),
    ]

    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="logs")
    admin = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='product_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    change_amount = models.IntegerField(default=0)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_log"
        managed = False

    def __str__(self):
        return f"{self.product.name} - {self.action}"
