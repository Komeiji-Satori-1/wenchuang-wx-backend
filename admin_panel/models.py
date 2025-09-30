from django.db import models

# Create your models here.

class AdminUser(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_user'  # 对应 MySQL 表名
        managed = False           # Django 不管理该表（表已存在）

    def __str__(self):
        return self.username