from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_home, name='product_home'),
    path('detail/', views.product_detail, name='product_detail'),
]