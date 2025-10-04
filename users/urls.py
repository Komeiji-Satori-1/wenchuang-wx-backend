from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('home', views.user_admin_home, name='user_admin_home'),
    path('user_list/', views.user_list, name='user_list'),
    path('admin_list/', views.admin_list, name='admin_list'),
]
