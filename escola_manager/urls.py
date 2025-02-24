from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('alunos/', include('apps.alunos.urls')),
    path('chatbot/', include('apps.chatbot.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('relatorios/', include('apps.relatorios.urls')),  # Adicione esta linha
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)