# /apps/alunos/urls.py
from django.urls import path
from . import views
from .constants import URL_NAMES
from django.conf import settings
from django.conf.urls.static import static

app_name = 'alunos'

urlpatterns = [
    # Lista principal e busca de alunos
    path('', 
         views.AlunoListView.as_view(), 
         name=URL_NAMES['LISTA']),
    
    path('buscar/', 
         views.AlunoListView.as_view(), 
         name='buscar_alunos'),
    
    # Visualização detalhada do aluno
    path('aluno/<uuid:pk>/', 
         views.AlunoDetailView.as_view(), 
         name=URL_NAMES['DETALHE']),

    # Operações CRUD (Criar, Atualizar, Deletar)
    path('cadastrar/', 
         views.AlunoCreateView.as_view(), 
         name=URL_NAMES['CADASTRAR']),
    
    path('editar/<uuid:pk>/', 
         views.AlunoUpdateView.as_view(), 
         name=URL_NAMES['EDITAR']),
    
    path('excluir/<uuid:pk>/', 
         views.AlunoDeleteView.as_view(), 
         name=URL_NAMES['EXCLUIR']),
    
    # Gerenciamento de notas
    path('aluno/<uuid:aluno_pk>/notas/adicionar/', 
         views.NotaCreateView.as_view(), 
         name='adicionar_nota'),
    
    path('aluno/<uuid:aluno_pk>/notas/editar/<uuid:pk>/', 
         views.NotaUpdateView.as_view(), 
         name='editar_nota'),
    
    path('aluno/<uuid:aluno_pk>/notas/excluir/<uuid:pk>/', 
         views.NotaDeleteView.as_view(), 
         name='excluir_nota'),

    # Endpoints da API
    path('api/aluno/<uuid:aluno_pk>/notas/', 
         views.AlunoNotasAPIView.as_view(), 
         name='api_notas'),
    
    path('api/aluno/<uuid:aluno_pk>/medias/', 
         views.AlunoMediaAPIView.as_view(), 
         name='api_medias'),
    
    path('api/alunos/', 
         views.AlunoListView.as_view(), 
         name='api_lista_alunos'),

    # Operações de exportação
    path('aluno/<uuid:aluno_pk>/exportar/pdf/', 
         views.AlunoExportPDFView.as_view(), 
         name=URL_NAMES['EXPORTAR_PDF']),

    path('aluno/<uuid:aluno_pk>/exportar/excel/', 
         views.AlunoExportExcelView.as_view(), 
         name=URL_NAMES['EXPORTAR_EXCEL']),

    path('importar/excel/', 
     views.AlunoImportExcelView.as_view(), 
     name='importar_excel'),
     
     path('download/template/', 
          views.DownloadTemplateExcelView.as_view(), 
          name='download_template'),
     
     path('api/<uuid:pk>/foto/', 
         views.AlunoFotoView.as_view(), 
         name='aluno-foto'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)