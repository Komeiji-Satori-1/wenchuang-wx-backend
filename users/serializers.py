from rest_framework import serializers
from .models import User,Address

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'openid', 'nickname', 'avatar_url', 'created_at']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'receiver_name', 'phone', 'detail']