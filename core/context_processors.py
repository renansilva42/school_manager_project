from .models import SiteSettings

def site_settings(request):
    """
    Adiciona as configurações do site ao contexto global de todos os templates.
    """
    return {
        'site_settings': SiteSettings.get_settings()
    }
