from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='usuarios_home'),
    path('users/', views.user_management, name='user_management'),
    path('settings/', views.settings_view, name='settings'),
]