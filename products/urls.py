from django.urls import path
from . import views
from .views import (
    CouponListView, CouponAddView, CouponUpdateView, CouponDeleteView,CouponDetailAPIView,CouponExchangeAPIView
)

urlpatterns = [
    path('', views.product_home, name='product_home'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('detail/', views.product_detail, name='product_detail'),
    path('log/', views.product_log, name='product_log'),
    path('get_product/<int:product_id>', views.product_search, name='product_search'),
    path('wechat_get_product/', views.ProductListView.as_view(), name='wechat_get_product_api'),
    path('wechat_get_detail/<int:pk>/', views.ProductDetailAPIView.as_view(), name='wechat_get_detail_api'),
    path('coupon/',views.coupon_page,name="coupon"),
    path('coupon/get/<int:pk>/', CouponDetailAPIView.as_view(), name='coupon_detail_api'),
    path("coupon/list/", CouponListView.as_view(),name="coupon_list"),
    path("coupon/add/", CouponAddView.as_view(),name="coupon_add_api"),
    path("coupon/update/", CouponUpdateView.as_view(),name="coupon_update_api"),
    path("coupon/delete/", CouponDeleteView.as_view(),name="coupon_delete_api"),
    path('coupon/exchange/', views.CouponExchangeAPIView.as_view(), name='coupon_exchange'),
]
