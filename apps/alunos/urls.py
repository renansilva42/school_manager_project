from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_alunos, name='lista_alunos'),
    path('buscar/', views.lista_alunos, name='buscar_alunos'),
    # Altere esta linha para aceitar UUID
    path('aluno/<str:pk>/', views.detalhe_aluno, name='detalhe_aluno'),
    path('cadastrar/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('editar/<str:pk>/', views.editar_aluno, name='editar_aluno'),
    path('excluir/<str:pk>/', views.excluir_aluno, name='excluir_aluno'),
    path('adicionar_nota/<str:aluno_pk>/', views.adicionar_nota, name='adicionar_nota'),
    path('aluno/<str:aluno_pk>/exportar_pdf/', views.exportar_detalhes_aluno_pdf, name='exportar_detalhes_aluno_pdf'),
]