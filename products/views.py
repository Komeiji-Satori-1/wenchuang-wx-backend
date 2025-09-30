from django.shortcuts import render,HttpResponse
from admin_panel.decorators import admin_login_required

# Create your views here.
@admin_login_required
def product_home(request):
    return HttpResponse("这是产品列表")
@admin_login_required
def product_detail(request):
    return HttpResponse("这是产品明细")