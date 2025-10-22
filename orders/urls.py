from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_analysis_home, name='order_home'),
    #path('wechat_post_order/', views.CreateOrder.as_view(), name='wechat_post_order'),
]