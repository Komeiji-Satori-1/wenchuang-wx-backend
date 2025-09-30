from django.shortcuts import render,HttpResponse
from admin_panel.decorators import admin_login_required

# Create your views here.
@admin_login_required
def product_home(request):
    return render(request,'product_home.html')
@admin_login_required
def product_detail(request):
    return render(request,'product_detail.html')