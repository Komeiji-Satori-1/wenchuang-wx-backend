from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from .models import User
from admin_panel.models import AdminUser


def user_admin_home(request):
    """用户 & 管理员主页"""
    return render(request, 'user_admin_list.html')


def user_list(request):
    """普通用户分页数据"""
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    users = User.objects.all().order_by('-created_at')

    paginator = Paginator(users, per_page)
    page_obj = paginator.get_page(page)

    data = [{
        'id': u.id,
        'nickname': u.nickname or '(未命名)',
        'openid': u.openid,
        'avatar_url': u.avatar_url,
        'created_at': u.created_at.strftime('%Y-%m-%d %H:%M'),
    } for u in page_obj]

    return JsonResponse({
        'data': data,
        'total': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })


def admin_list(request):
    """管理员分页数据"""
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    admins = AdminUser.objects.all().order_by('-created_at')

    paginator = Paginator(admins, per_page)
    page_obj = paginator.get_page(page)

    data = [{
        'id': a.id,
        'username': a.username,
        'created_at': a.created_at.strftime('%Y-%m-%d %H:%M'),
    } for a in page_obj]

    return JsonResponse({
        'data': data,
        'total': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })
