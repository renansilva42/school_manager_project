from django.urls import path
from . import views

app_name = 'alunos'

urlpatterns = [
    # Lista principal e busca de alunos
    path('', 
         views.AlunoListView.as_view(), 
         name='lista'),
    
    path('buscar/', 
         views.AlunoListView.as_view(), 
         name='buscar_alunos'),
    
    # Visualização detalhada do aluno
    path('aluno/<uuid:pk>/', 
         views.AlunoDetailView.as_view(), 
         name='detalhe'),

    # Operações CRUD (Criar, Atualizar, Deletar)
    path('cadastrar/', 
         views.AlunoCreateView.as_view(), 
         name='cadastrar'),
    
    path('editar/<uuid:pk>/', 
         views.AlunoUpdateView.as_view(), 
         name='editar'),
    
    path('excluir/<uuid:pk>/', 
         views.AlunoDeleteView.as_view(), 
         name='excluir'),

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
         name='exportar_pdf'),
    
    path('aluno/<uuid:aluno_pk>/exportar/excel/', 
         views.AlunoExportExcelView.as_view(), 
         name='exportar_excel'),
    
    # Importação de dados
    path('importar/excel/', 
         views.AlunoImportExcelView.as_view(), 
         name='importar_excel'),
]