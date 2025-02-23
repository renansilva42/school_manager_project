from django.contrib import admin
from django.urls import path, include
from apps.usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', usuarios_views.home, name='home'),
    path('accounts/login/', usuarios_views.login_view, name='login'),
    path('accounts/logout/', usuarios_views.logout_view, name='logout'),
]