from rest_framework import serializers
from .models import Product, Category,ProductImage
from users.models import Coupon,UserCoupon,User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'order']

class ProductSerializer(serializers.ModelSerializer):
    # 嵌套分类信息（仅展示 id 和 name）
    category = CategorySerializer(read_only=True)

    # 自动生成完整图片 URL，例如 https://xduwenchuang.cn/media/products/xxx.jpg
    image_url = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'price',
            'stock',
            'image_url',
            'images',
            'created_at',
            'category',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')

        # 图片为空
        if not obj.image:
            return None

        # request 为空
        if request is None:
            return obj.image.url  # 返回相对路径

        # 正常情况返回完整 URL
        return request.build_absolute_uri(obj.image.url)

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id", "name", "discount_amount", "min_amount",
            "is_exchange", "cost_points", "is_active",
            "start_time", "end_time", "sort_order","valid_days"
        ]