from django.urls import path
from . import views

urlpatterns = [
    path('', views.relatorios, name='relatorios'),
    path('media-por-serie/', views.relatorio_media_por_serie, name='relatorio_media_por_serie'),
    path('media-por-serie/pdf/', views.exportar_media_por_serie_pdf, name='exportar_media_por_serie_pdf'),
    path('alunos-por-serie/', views.relatorio_alunos_por_serie, name='relatorio_alunos_por_serie'),
    path('alunos-por-serie/pdf/', views.exportar_alunos_por_serie_pdf, name='exportar_alunos_por_serie_pdf'),
    path('notas-baixas/', views.relatorio_notas_baixas, name='relatorio_notas_baixas'),
    path('notas-baixas/pdf/', views.exportar_notas_baixas_pdf, name='exportar_notas_baixas_pdf'),
]