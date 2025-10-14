from django.urls import path
from . import views


urlpatterns = [
    path('', views.product_home, name='product_home'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('detail/', views.product_detail, name='product_detail'),
    path('log/', views.product_log, name='product_log'),
    path('get_product/<int:product_id>', views.product_search, name='product_search'),
]
