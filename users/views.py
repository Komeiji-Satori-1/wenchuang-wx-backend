import requests
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User,Address,UserCoupon,Coupon
from orders.models import Orders
from admin_panel.models import AdminUser
from .serializers import UserSerializer,AddressSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User as AuthUser
from admin_panel.decorators import admin_login_required
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone


@admin_login_required
def user_admin_home(request):

    return render(request, 'user_admin_list.html')


def user_list(request):

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
        'phone': u.phone or '(未绑定)',
    } for u in page_obj]

    return JsonResponse({
        'data': data,
        'total': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })


def admin_list(request):

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
        openid = request.data.get('openid')
        nickname = request.data.get('nickname')
        avatar_url = request.data.get('avatar_url')

        if not openid or not nickname:
            return Response({'error': '缺少openid或昵称'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(openid=openid)
            user.nickname = nickname
            user.avatar_url = avatar_url
            user.save()
            created = False
        except User.DoesNotExist:
            user = User.objects.create(
                openid=openid,
                nickname=nickname,
                avatar_url=avatar_url
            )
            created = True
        if not user.auth_user:
            auth_user = AuthUser.objects.create(username=openid)
            user.auth_user = auth_user
            user.save()

        token, _ = Token.objects.get_or_create(user=user.auth_user)
        serializer = UserSerializer(user)

        return Response({
            'token': token.key,
            'user': serializer.data,
            'created': created,
            'msg': '登录成功'
        })

def get_access_token():
    appid = getattr(settings, 'WECHAT_APPID', None)
    secret = getattr(settings, 'WECHAT_SECRET', None)
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
    r = requests.get(url)
    data = r.json()
    return data.get('access_token')
class UserInfoView(APIView):
        permission_classes = [IsAuthenticated]

        def get(self, request):
            user = request.user.user  # 假设 request.user 是 AuthUser

            # 用户信息
            user_info = {
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "phone": user.phone,
                "points": user.points,
            }

            # 可用优惠券
            now = timezone.now()
            coupons = UserCoupon.objects.filter(user=user, is_used=False, coupon__start_time__lte=now,
                                                coupon__end_time__gte=now)
            coupon_list = [
                {
                    "name": uc.coupon.name,
                    "discount_amount": uc.coupon.discount_amount,
                    "min_amount": uc.coupon.min_amount,
                    "received_at": uc.received_at
                } for uc in coupons
            ]

            # 收货地址列表
            addresses = Address.objects.filter(user=user)
            address_list = [
                {
                    "id": addr.id,
                    "receiver_name": addr.receiver_name,
                    "phone": addr.phone,
                    "detail": addr.detail
                } for addr in addresses
            ]

            return Response({
                "user_info": user_info,
                "coupons": coupon_list,
                "addresses": address_list
            })

def get_openid_from_login_code(login_code):
    appid = getattr(settings, 'WECHAT_APPID', None)
    secret = getattr(settings, 'WECHAT_SECRET', None)
    url = (
        f"https://api.weixin.qq.com/sns/jscode2session?"
        f"appid={appid}&secret={secret}&js_code={login_code}&grant_type=authorization_code"
    )
    try:
        resp = requests.get(url)
        data = resp.json()
        return data.get('openid'), data.get('session_key')
    except Exception:
        # 实际项目中应记录错误日志
        return None, None

class GetUserPhoneNumberView(APIView):
    """
    处理手机号授权，并返回手机号和 OpenID
    前端请求参数：{'code': phone_code, 'login_code': wx_login_code}
    """

    def post(self, request):
        phone_code = request.data.get('code')
        login_code = request.data.get('login_code')  # 接收前端的 tempLoginCode

        if not phone_code or not login_code:
            return Response({'error': '缺少 code 或 login_code'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. 使用 login_code 换取 OpenID
        openid, _ = get_openid_from_login_code(login_code)
        if not openid:
            # 如果 OpenID 换取失败，则无法进行后续绑定，直接返回错误
            return Response({'error': '静默登录凭证无效或过期'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 使用 phone_code 换取手机号
        access_token = get_access_token()
        url = f'https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}'
        r = requests.post(url, json={'code': phone_code})
        data = r.json()

        if 'errcode' in data and data['errcode'] != 0:
            return Response({'error': data.get('errmsg', '手机号获取失败')}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = data.get('phone_info', {}).get('phoneNumber')
        if not phone_number:
            return Response({'error': '未能获取到手机号'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. 手机号获取成功，更新/创建用户记录并绑定手机号
        user, created = User.objects.get_or_create(
            openid=openid,
            defaults={'phone': phone_number, 'nickname': '微信用户'}  # 初始昵称
        )
        user.phone = phone_number  # 确保更新手机号
        user.save()

        # 4. 返回手机号和 OpenID 给前端
        return Response({
            'phoneNumber': phone_number,
            'openid': openid  # <-- 关键：返回 OpenID
        })

class AddressListAPIView(APIView):
    def get(self, request, user_openid):
        addresses = Address.objects.filter(user__openid=user_openid)
        print(addresses)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request, user_openid):
        # 通过 openid 找到用户
        user = User.objects.filter(openid=user_openid).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['user'] = user.id

        serializer = AddressSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class AddressDetailAPIView(APIView):
    def get(self, request, pk):
        """
        获取单个地址详情
        """
        try:
            address = Address.objects.get(id=pk)
        except Address.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddressSerializer(address)
        return Response(serializer.data)

    def put(self, request, pk):
        address = Address.objects.get(id=pk)
        serializer = AddressSerializer(address, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        address = Address.objects.get(id=pk)
        address.delete()
        return Response({"message": "删除成功"})

class AvailableCouponAPIView(APIView):
    def get(self, request):
        openid = request.query_params.get("openid")
        encrypted_id = request.query_params.get("encrypted_id")
        try:
            user = User.objects.get(openid=openid)
        except User.DoesNotExist:
            return Response({"code": 404, "msg": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 获取可用优惠券
        coupons = UserCoupon.objects.filter(
            user=user,
            is_used=False,
        )

        # 可根据订单金额或商品限制筛选
        order = Orders.objects.get(encrypted_id=encrypted_id)
        available = []
        for uc in coupons:
            if order.pay_amount >= uc.coupon.min_amount:  # 满足最低消费
                available.append({
                    "id": uc.coupon_id,
                    "name": uc.coupon.name,
                    "discount": str(uc.coupon.discount_amount),
                    "min_amount": str(uc.coupon.min_amount)
                })

        return Response({"code": 200, "msg": "获取成功", "data": available})