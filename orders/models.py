from django.db import models
from users.models import User
# Create your models here.

class Orders(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_user'  # 对应 MySQL 表名
        managed = False           # Django 不管理该表（表已存在）

    def __str__(self):
        return f"订单 {self.id} - 用户 {self.user.openid}:{self.user.nickname} - 金额 {self.total_amount}"