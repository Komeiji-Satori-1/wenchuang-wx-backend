from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_analysis_home, name='order_home'),
]