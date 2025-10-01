from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_home, name='product_home'),
    path('add/', views.add_product, name='add_product'),
    path('detail/', views.product_detail, name='product_detail'),
]