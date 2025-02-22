from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.alunos.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('relatorios/', include('apps.relatorios.urls')),
    path('chatbot/', include('apps.chatbot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)