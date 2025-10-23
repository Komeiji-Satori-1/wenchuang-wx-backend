from django.db import models
from admin_panel.models import AdminUser
from django.contrib.auth.models import User as AuthUser
from django.utils import timezone
# Create your models here.

class User(models.Model):

    id = models.AutoField(primary_key=True)
    openid = models.CharField(max_length=64, unique=True, verbose_name='WechatOpenID', help_text='OnlyID')
    nickname = models.CharField(max_length=50, null=True, blank=True, verbose_name='nickname')
    avatar_url = models.CharField(max_length=200, null=True, blank=True, verbose_name='avatarURL')
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created_at')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='last_login')


    auth_user = models.OneToOneField(
        AuthUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联认证用户'
    )

    token = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        db_table = 'user'
        managed = True
        verbose_name = 'WechatUser'
        verbose_name_plural = 'WechatUsers'

    def __str__(self):
        return self.nickname or self.openid