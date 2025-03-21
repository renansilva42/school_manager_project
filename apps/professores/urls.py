from django.urls import path
from . import views

app_name = 'professores'

urlpatterns = [
    path('', views.ProfessorListView.as_view(), name='professor_list'),
    path('cadastro/', views.ProfessorCreateView.as_view(), name='professor_create'),
    path('atribuicao/', views.AtribuicaoDisciplinaCreateView.as_view(), name='atribuicao_create'),
    path('disponibilidade/', views.DisponibilidadeHorarioCreateView.as_view(), name='disponibilidade_create'),
]