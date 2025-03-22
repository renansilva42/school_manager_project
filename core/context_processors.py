# /core/context_processors.py
from apps.professores.models import SiteSettings  # Update this import

def site_settings(request):
    """
    Adiciona as configurações do site ao contexto global de todos os templates.
    """
    return {
        'site_settings': SiteSettings.get_settings()
    }