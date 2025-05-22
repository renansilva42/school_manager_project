# /apps/professores/admin.py
from django.contrib import admin
from .models import Professor, AtribuicaoDisciplina, DisponibilidadeHorario, Disciplina

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'formacao', 'especialidade')
    search_fields = ('nome', 'email', 'formacao', 'especialidade')
    list_filter = ('formacao', 'especialidade')

@admin.register(AtribuicaoDisciplina)
class AtribuicaoDisciplinaAdmin(admin.ModelAdmin):
    list_display = ('professor', 'disciplina', 'turma', 'ano_letivo')
    search_fields = ('professor__nome', 'disciplina__nome', 'turma')
    list_filter = ('ano_letivo',)
    autocomplete_fields = ['professor', 'disciplina']

@admin.register(DisponibilidadeHorario)
class DisponibilidadeHorarioAdmin(admin.ModelAdmin):
    list_display = ('professor', 'dia_semana', 'hora_inicio', 'hora_fim')
    list_filter = ('dia_semana', 'professor')
    search_fields = ('professor__nome',)

# @admin.register(SiteSettings)
# class SiteSettingsAdmin(admin.ModelAdmin):
#     list_display = ('__str__', 'school_name', 'contact_email')
    
#     def has_add_permission(self, request):
#         return SiteSettings.objects.count() == 0


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'carga_horaria_iniciais', 'carga_horaria_finais', 'ativo')
    search_fields = ('nome',)
    list_filter = ('ativo',)
