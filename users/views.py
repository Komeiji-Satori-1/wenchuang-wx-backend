from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.

def user_home(request):
    return HttpResponse("这是用户列表")