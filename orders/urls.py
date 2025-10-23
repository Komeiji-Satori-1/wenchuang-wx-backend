from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_analysis_home, name='order_home'),
    path('wechat_post_order/', views.CreateOrderView.as_view(), name='wechat_post_order'),
    path('simulate_pay/',views.SimulatePayView.as_view(),name='simulate_pay'),

    path('user-orders/', views.UserOrderListView.as_view(), name='user-orders'),
    path('lists/', views.order_list_view, name='order_list'),
    path('list/<int:order_id>/', views.order_detail_view, name='order_detail'),


]