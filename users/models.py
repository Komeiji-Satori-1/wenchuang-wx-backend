from django.db import models

# Create your models here.

class User(models.Model):
    id = models.AutoField(primary_key=True)
    openid = models.CharField(max_length=64, unique=True)
    nickname = models.CharField(max_length=50,null=True, blank=True)
    avatar_url = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'admin_user'  # 对应 MySQL 表名
        managed = False
