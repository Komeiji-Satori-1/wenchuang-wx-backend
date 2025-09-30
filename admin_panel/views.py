from django.db.models.fields import return_None
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from admin_panel.models import AdminUser
from .decorators import admin_login_required

# Create your views here.

@admin_login_required
def index(request):
    return render(request, 'index.html')
def test(request):
    return render(request, 'test.html')

def login_view(request):
    return render(request, 'login.html')

def check_login(username, password):
    try:
        user = AdminUser.objects.get(username=username, password=password)
        return user
    except AdminUser.DoesNotExist:
        return None


@csrf_exempt
def verification(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = AdminUser.objects.get(username=username, password=password)
            request.session["admin_user_id"] = user.id
            request.session["admin_username"] = user.username
            print("当前 session 数据：", request.session.items())
            return JsonResponse({"success": True})
        except AdminUser.DoesNotExist:
            return JsonResponse({"success": False})

    return HttpResponse("null")

def logout_view(request):
    # 清除所有 session 数据
    request.session.flush()
    # 可选：给出提示
    # messages.success(request, "您已退出登录")  # 如果用 messages 框架的话
    return redirect('/login/')  # 重定向回登录页
