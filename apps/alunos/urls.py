from django.urls import path
from . import views

urlpatterns = [
    path('', views.AlunoListView.as_view(), name='lista_alunos'),
    path('buscar/', views.AlunoListView.as_view(), name='buscar_alunos'),
    path('aluno/<str:pk>/', views.AlunoDetailView.as_view(), name='detalhe_aluno'),
    path('cadastrar/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('editar/<str:pk>/', views.editar_aluno, name='editar_aluno'),
    path('excluir/<str:pk>/', views.excluir_aluno, name='excluir_aluno'),
    path('adicionar_nota/<str:aluno_pk>/', views.adicionar_nota, name='adicionar_nota'),
    path('aluno/<str:aluno_pk>/exportar_pdf/', views.exportar_detalhes_aluno_pdf, name='exportar_detalhes_aluno_pdf'),
]