from django.urls import path
from . import views

app_name = 'alunos'

urlpatterns = [
    # List and Search Views
    path('', 
         views.AlunoListView.as_view(), 
         name='lista'),
    
    
    path('buscar/', 
         views.AlunoListView.as_view(), 
         name='buscar_alunos'),
    # ... other URLs


    # Detail View
    path('aluno/<uuid:pk>/', 
         views.AlunoDetailView.as_view(), 
         name='detalhe'),

    # CRUD Operations
    path('cadastrar/', 
         views.AlunoCreateView.as_view(), 
         name='cadastrar'),
    
    path('editar/<uuid:pk>/', 
         views.AlunoUpdateView.as_view(), 
         name='editar'),
    
    path('excluir/<uuid:pk>/', 
         views.AlunoDeleteView.as_view(), 
         name='excluir'),

    # Grade Management
    path('aluno/<uuid:aluno_pk>/notas/adicionar/', 
         views.NotaCreateView.as_view(), 
         name='adicionar_nota'),

    # API Endpoints
    path('api/aluno/<uuid:aluno_pk>/notas/', 
         views.AlunoNotasAPIView.as_view(), 
         name='api_notas'),
    
    path('api/aluno/<uuid:aluno_pk>/medias/', 
         views.AlunoMediaAPIView.as_view(), 
         name='api_medias'),

    # Export Operations
    path('aluno/<uuid:aluno_pk>/exportar/pdf/', 
         views.AlunoExportPDFView.as_view(), 
         name='exportar_pdf'),
    
    path('aluno/<uuid:aluno_pk>/exportar/excel/', 
         views.AlunoExportExcelView.as_view(), 
         name='exportar_excel'),
]