from django.db import models

# Create your models here.
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50,null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'category'
        managed = False

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)  # 商品名称
    description = models.TextField(blank=True, null=True)  # 商品描述
    price = models.DecimalField(max_digits=10, decimal_places=2)  # 商品价格
    stock = models.IntegerField(default=0)  # 库存数量
    image_url = models.CharField(max_length=200, null=True, blank=True)  # 商品图片 URL
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",  # 反向查询用 category.products.all()
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
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    change_amount = models.IntegerField(default=0)  # 库存变化量
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_log"
        managed = True

    def __str__(self):
        return f"{self.product.name} - {self.action}"