from django.urls import path
from . import views

app_name = 'professores'

urlpatterns = [
    path('', views.ProfessorListView.as_view(), name='professor_list'),
    path('cadastro/', views.ProfessorCreateView.as_view(), name='professor_create'),
    path('atribuicao/', views.AtribuicaoDisciplinaCreateView.as_view(), name='atribuicao_create'),
    path('disponibilidade/', views.DisponibilidadeHorarioCreateView.as_view(), name='disponibilidade_create'),
    # Using DisciplinaCreateView for the disciplina_list URL pattern
    # since DisciplinaListView doesn't appear to exist
    path('disciplinas/', views.DisciplinaCreateView.as_view(), name='disciplina_list'),
    path('disciplinas/criar/', views.DisciplinaCreateView.as_view(), name='disciplina_create'),
    path('professor/<int:pk>/desativar/', views.desativar_professor, name='professor_desativar'),
]
