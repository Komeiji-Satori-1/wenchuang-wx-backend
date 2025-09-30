from django.urls import path
from . import views


urlpatterns = [
    path('index/',views.index),
    path('test/',views.test),
    path('login/',views.login_view),
    path('login/verification/',views.verification),
    path('index/logout/', views.logout_view, name='logout'),

]