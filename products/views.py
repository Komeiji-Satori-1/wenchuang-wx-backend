from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.

def product_home(request):
    return HttpResponse("这是产品列表")
def product_detail(request):
    return HttpResponse("这是产品明细")