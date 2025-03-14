from django.contrib import admin
from .models import Professor, SiteSettings


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'disciplina', 'email')
    search_fields = ('nome', 'disciplina')


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'school_name', 'contact_email')
    
    def has_add_permission(self, request):
        # Impede a criação de múltiplas instâncias
        return SiteSettings.objects.count() == 0
