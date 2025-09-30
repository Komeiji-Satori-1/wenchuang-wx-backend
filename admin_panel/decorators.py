from functools import wraps
from django.shortcuts import redirect

def admin_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 检查 session 里有没有 user_id
        if not request.session.get("admin_user_id"):
            # 如果没有，重定向到登录页面
            return redirect("/login/")
        return view_func(request, *args, **kwargs)
    return wrapper
