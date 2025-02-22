from django.urls import path
from . import views

urlpatterns = [
    path('alunos/', views.lista_alunos, name='lista_alunos'),
    path('alunos/<int:pk>/', views.detalhe_aluno, name='detalhe_aluno'),
    path('alunos/cadastrar/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('alunos/<int:pk>/editar/', views.editar_aluno, name='editar_aluno'),
    path('alunos/<int:aluno_pk>/adicionar_nota/', views.adicionar_nota, name='adicionar_nota'),
]