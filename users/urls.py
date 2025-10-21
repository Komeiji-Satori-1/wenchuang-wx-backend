from django.urls import path
from . import views
from .views import WeChatLoginView

app_name = 'users'

urlpatterns = [
    path('home', views.user_admin_home, name='user_admin_home'),
    path('home/', views.user_admin_home, name='user_admin_home'),
    path('home/user_list/', views.user_list, name='user_list'),
    path('home/admin_list/', views.admin_list, name='admin_list'),

    path('wechat_login/', WeChatLoginView.as_view(), name='wechat_login_api'),
]
