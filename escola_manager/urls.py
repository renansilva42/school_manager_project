from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('alunos/', include('apps.alunos.urls')),
    path('chatbot/', include('apps.chatbot.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('relatorios/', include('apps.relatorios.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('professores/', include('apps.professores.urls', namespace='professores')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('api/alunos/<uuid:pk>/foto/', 
         views.AlunoFotoView.as_view(), 
         name='aluno-foto'),
]

# Configuração para servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Configuração para produção
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)