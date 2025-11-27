# orders/serializers.py
from rest_framework import serializers
from .models import Orders, OrderItems
from products.models import Product
from users.models import User

class ProductBriefSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'price','image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return ''

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItems
        fields = [
            'id',
            'product',
            'product_name',
            'product_image',
            'quantity',
            'price',
        ]

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product and obj.product.image:
            if request:
                return request.build_absolute_uri(obj.product.image.url)
            return obj.product.image.url
        return ''


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Orders
        fields = ['encrypted_id', 'status', 'total_amount', 'created_at', 'items','id']

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_text = serializers.SerializerMethodField()

    receiver_name = serializers.CharField(source='address.receiver_name', read_only=True)
    receiver_phone = serializers.CharField(source='address.phone', read_only=True)
    receiver_address = serializers.CharField(source='address.detail', read_only=True)

    coupon_name = serializers.CharField(source='user_coupon.coupon.name', read_only=True)
    coupon_discount_amount = serializers.CharField(
        source='user_coupon.coupon.discount_amount',
        read_only=True
    )
    class Meta:
        model = Orders
        fields = [
            'id',
            'encrypted_id',       # 小程序展示用订单号
            'user',
            'total_amount',
            'shipping_fee',
            'discount_amount',
            'pay_amount',
            'receiver_name',
            'receiver_phone',
            'receiver_address',
            'coupon_name',
            'coupon_discount_amount',
            'status',
            'status_text',
            'created_at',
            'items',
        ]

    def get_status_text(self, obj):
        mapping = dict(Orders.STATUS_CHOICES)
        return mapping.get(obj.status, obj.status)