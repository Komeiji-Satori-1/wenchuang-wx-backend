from django.db import models
from admin_panel.models import AdminUser
from django.contrib.auth.models import User as AuthUser
from django.utils import timezone
# Create your models here.

class User(models.Model):
    """微信小程序用户的自定义模型，用于存储微信相关数据"""
    id = models.AutoField(primary_key=True)
    openid = models.CharField(max_length=64, unique=True, verbose_name='WechatOpenID', help_text='OnlyID')
    nickname = models.CharField(max_length=50, null=True, blank=True, verbose_name='nickname')
    avatar_url = models.CharField(max_length=200, null=True, blank=True, verbose_name='avatarURL')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created_at')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='last_login')

    # 核心：关联标准的 Django 认证用户。Token 认证必须依赖此字段。
    auth_user = models.OneToOneField(
        AuthUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联认证用户'
    )

    # 历史遗留字段，可忽略或删除
    token = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        db_table = 'user'  # 对应 MySQL 表名
        managed = True  # 数据库表结构由外部手动管理
        verbose_name = 'WechatUser'
        verbose_name_plural = 'WechatUsers'

    def __str__(self):
        return self.nickname or self.openid