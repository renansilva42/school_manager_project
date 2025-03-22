# /apps/professores/admin.py
from django.contrib import admin
# from .models import Professor, AtribuicaoDisciplina, DisponibilidadeHorario, SiteSettings

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'formacao', 'especialidade', 'ativo')
    search_fields = ('nome', 'email')
    list_filter = ('ativo', 'formacao')

@admin.register(AtribuicaoDisciplina)
class AtribuicaoDisciplinaAdmin(admin.ModelAdmin):
    list_display = ('professor', 'disciplina', 'turma', 'ano_letivo')
    search_fields = ('professor__nome', 'disciplina', 'turma')
    list_filter = ('ano_letivo',)

@admin.register(DisponibilidadeHorario)
class DisponibilidadeHorarioAdmin(admin.ModelAdmin):
    list_display = ('professor', 'dia_semana', 'hora_inicio', 'hora_fim')
    list_filter = ('dia_semana',)

# @admin.register(SiteSettings)
# class SiteSettingsAdmin(admin.ModelAdmin):
#     list_display = ('__str__', 'school_name', 'contact_email')
    
#     def has_add_permission(self, request):
#         return SiteSettings.objects.count() == 0