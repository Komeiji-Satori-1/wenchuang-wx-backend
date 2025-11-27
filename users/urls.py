from django.urls import path
from . import views
from .views import WeChatLoginView, AvailableCouponAPIView
from .views import UserInfoView
from .views import GetUserPhoneNumberView,AddressListAPIView,AddressDetailAPIView

app_name = 'users'

urlpatterns = [
    path('home', views.user_admin_home, name='user_admin_home'),
    path('home/', views.user_admin_home, name='user_admin_home'),
    path('home/user_list/', views.user_list, name='user_list'),
    path('home/admin_list/', views.admin_list, name='admin_list'),

    path('wechat_login/', WeChatLoginView.as_view(), name='wechat_login_api'),
    path('user_info/', UserInfoView.as_view(), name='user_info'),
    path('get_user_phone/', GetUserPhoneNumberView.as_view(), name='get_user_phone'),
    path('address/<str:user_openid>/', AddressListAPIView.as_view()),
    path('address/detail/<int:pk>/', AddressDetailAPIView.as_view()),
    path('coupon/available/', AvailableCouponAPIView.as_view()),

]
