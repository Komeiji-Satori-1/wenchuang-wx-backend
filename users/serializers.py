from rest_framework import serializers
from .models import User,Address,UserCoupon

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'openid', 'nickname', 'avatar_url', 'created_at']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'receiver_name', 'phone', 'detail']

class UserCouponSerializer(serializers.ModelSerializer):
    discount = serializers.IntegerField(source="coupon.discount_amount")
    min_amount = serializers.IntegerField(source="coupon.min_amount")
    name = serializers.CharField(source="coupon.name")
    expires_at = serializers.DateTimeField(format="%Y-%m-%d")
    status = serializers.CharField(read_only=True)

    class Meta:
        model = UserCoupon
        fields = ["id", "name", "discount", "min_amount", "expires_at", "status"]