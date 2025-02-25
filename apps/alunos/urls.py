from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_alunos, name='lista_alunos'),
    path('aluno/<int:pk>/', views.detalhe_aluno, name='detalhe_aluno'),
    path('cadastrar/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('editar/<int:pk>/', views.editar_aluno, name='editar_aluno'),
    path('excluir/<int:pk>/', views.excluir_aluno, name='excluir_aluno'),  # Adicione esta linha
    path('adicionar_nota/<int:aluno_pk>/', views.adicionar_nota, name='adicionar_nota'),
    path('aluno/<int:aluno_pk>/exportar_pdf/', views.exportar_detalhes_aluno_pdf, name='exportar_detalhes_aluno_pdf'),
]