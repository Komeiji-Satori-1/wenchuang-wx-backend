from django.db import models
from admin_panel.models import AdminUser
from django.contrib.auth.models import User as AuthUser
from django.utils import timezone
from datetime import timedelta
# Create your models here.

class User(models.Model):

    id = models.AutoField(primary_key=True)
    openid = models.CharField(max_length=64, unique=True, verbose_name='WechatOpenID', help_text='OnlyID')
    nickname = models.CharField(max_length=50, null=True, blank=True, verbose_name='nickname')
    avatar_url = models.CharField(max_length=200, null=True, blank=True, verbose_name='avatarURL')
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created_at')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='last_login')
    points = models.IntegerField(default=0, verbose_name='points')

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

class Address(models.Model):
    """
    用户收货地址表（一个用户可有多个地址）
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    receiver_name = models.CharField(max_length=50)  # 收货人姓名
    phone = models.CharField(max_length=20)          # 手机号
    detail = models.CharField(max_length=200)       # 详细地址

    class Meta:
        db_table = "address"
        managed = False

class Coupon(models.Model):
    """
    优惠券类型表，如满 100 减 20、无门槛 5 元等
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    discount_amount = models.IntegerField()   # 优惠金额（单位：元，整数）
    min_amount = models.IntegerField(default=0)  # 满多少可用（单位：元）
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_exchange = models.BooleanField(default=False)  # 是否允许积分兑换
    cost_points = models.IntegerField(default=0)  # 兑换所需积分
    is_active = models.BooleanField(default=True)  # 是否上架到积分商城
    sort_order = models.IntegerField(default=0)  # 排序（越大越靠后）
    valid_days = models.IntegerField(default=7)
    class Meta:
        db_table = "coupon"
        managed = False

class UserCoupon(models.Model):
    """
    某用户具体拥有的优惠券，例如一个人可有 3 张 “满100减20”
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)
    used_time = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = "user_coupon"
        managed = False

    def save(self, *args, **kwargs):
        # 如果模型是第一次 save，received_at 会是 None，需要手动赋值
        if self.received_at is None:
            self.received_at = timezone.now()

        # 如果首次生成优惠券，则自动设置过期日期
        if not self.expires_at:
            days = self.coupon.valid_days
            self.expires_at = self.received_at + timedelta(days=days)

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def status(self):
        """返回优惠券状态：unused / used / expired"""
        now = timezone.now()
        if self.is_used:
            return "used"
        elif self.expires_at and self.expires_at < now:
            return "expired"
        else:
            return "unused"