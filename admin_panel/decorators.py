from functools import wraps
from django.shortcuts import redirect

def admin_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("admin_user_id"):
            return redirect("/login/")
        return view_func(request, *args, **kwargs)
    return wrapper
