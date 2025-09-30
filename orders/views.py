from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.

def order_home(request):
    return HttpResponse("这是订单列表")