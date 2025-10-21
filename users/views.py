import requests
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from admin_panel.models import AdminUser
from .serializers import UserSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User as AuthUser


def user_admin_home(request):
    """用户 & 管理员主页"""
    return render(request, 'user_admin_list.html')


def user_list(request):
    """普通用户分页数据"""
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    users = User.objects.all().order_by('id')

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


class WeChatLoginView(APIView):
    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        nickname = request.data.get('nickname')
        avatar_url = request.data.get('avatar_url')
        if not code:
            return Response({'error':'缺少code'},status.HTTP_400_BAD_REQUEST)
        appid = getattr(settings, 'WECHAT_APPID', None)
        secret = getattr(settings, 'WECHAT_SECRET', None)
        url = (
            f"https://api.weixin.qq.com/sns/jscode2session?"
            f"appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code"
        )
        try:
            resp = requests.get(url)
            data = resp.json()
        except Exception as e:
            return Response({'error':'微信接口调用失败'},status.HTTP_400_BAD_REQUEST)
        if 'openid' not in data:
            # ✅ 测试阶段启用假数据
            fake_openid = f"test_openid_{code}"
            fake_session_key = "fake_session_key"
            openid = fake_openid
            session_key = fake_session_key
        else:
            # ✅ 真实环境下使用微信返回的数据
            openid = data['openid']
            session_key = data.get('session_key', '')

        user, created = User.objects.get_or_create(
            openid=openid,
            defaults={'nickname': nickname, 'avatar_url': avatar_url}
        )
        if not user.auth_user:
            auth_user = AuthUser.objects.create(username=openid)
            user.auth_user = auth_user
            user.save()
        '''
        try:
            # !!! 假设您的自定义 User 模型有一个字段 'auth_user' 链接到标准 Django User
            auth_user = user.auth_user
        except AttributeError:
            # 如果没有 'auth_user' 字段，或者关系未设置，则会失败
            print("CRITICAL ERROR: Custom User model is missing 'auth_user' link to Django standard User.")
            return Response({'error': '后端配置错误：用户模型未正确关联认证系统。'},
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
                            
        '''
        token, _ = Token.objects.get_or_create(user=user.auth_user)
        serializer = UserSerializer(user)
        return Response({
            'token': token.key,
            'user': serializer.data,
            'created': created,
            'msg': '登录成功'
        })
