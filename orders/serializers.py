# orders/serializers.py
from rest_framework import serializers
from .models import Orders, OrderItems
from products.models import Product

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
    product = ProductBriefSerializer()

    class Meta:
        model = OrderItems
        fields = ['id', 'product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Orders
        fields = ['id', 'status', 'total_amount', 'created_at', 'items']
