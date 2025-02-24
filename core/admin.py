from django.contrib import admin
from .models import Aluno, Professor

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'email')
    search_fields = ('nome', 'matricula')

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'disciplina', 'email')
    search_fields = ('nome', 'disciplina')