from django.contrib import admin
from .models import Professor



@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'disciplina', 'email')
    search_fields = ('nome', 'disciplina')