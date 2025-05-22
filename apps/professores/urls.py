from django.urls import path
from . import views

app_name = 'professores'

urlpatterns = [
    path('', views.ProfessorListView.as_view(), name='professor_list'),
    path('cadastro/', views.ProfessorCreateView.as_view(), name='professor_create'),
    path('atribuicao/', views.AtribuicaoDisciplinaCreateView.as_view(), name='atribuicao_create'),
    path('atribuicao/<int:pk>/delete/', views.AtribuicaoDisciplinaDeleteView.as_view(), name='atribuicao_delete'),
    path('disponibilidade/', views.DisponibilidadeHorarioCreateView.as_view(), name='disponibilidade_create'),
    path('disciplinas/', views.DisciplinaListView.as_view(), name='disciplina_list'),
    path('disciplinas/criar/', views.DisciplinaCreateView.as_view(), name='disciplina_create'),
    path('disciplinas/<int:pk>/editar/', views.DisciplinaUpdateView.as_view(), name='disciplina_edit'),
    path('professor/<int:pk>/desativar/', views.desativar_professor, name='professor_desativar'),
]
