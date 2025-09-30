from django.shortcuts import render,HttpResponse
from admin_panel.decorators import admin_login_required


# Create your views here.
@admin_login_required
def user_home(request):
    return HttpResponse("这是用户列表")