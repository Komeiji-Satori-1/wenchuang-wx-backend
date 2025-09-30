from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from admin_panel.models import AdminUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
import json
from django.contrib.auth import login, authenticate

# Create your views here.

def index(request):
    if not request.session.get("is_logged_in"):
        return render(request, "login.html")  # 没登录跳回登录
    return render(request, "index.html")
def test(request):
    return render(request, 'test.html')

def login(request):
    return render(request, 'login.html')

def check_login(username, password):
    try:
        user = AdminUser.objects.get(username=username, password=password)
        return True
    except AdminUser.DoesNotExist:
        return False


@csrf_exempt
def verification(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if check_login(username, password):
            request.session['is_logged_in'] = True
            request.session['username'] = username
            return JsonResponse({"success": True})

        else:
            return JsonResponse({"success": False})
    return HttpResponse("null")

'''

@csrf_exempt
def verification(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # ✅ 标记用户已登录
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False})
    return HttpResponse("null")
'''