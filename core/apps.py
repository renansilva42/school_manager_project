from django.apps import AppConfig

def ready(self):
    import os
    from django.conf import settings
    
    # Criar diretórios necessários
    media_dirs = [
        settings.MEDIA_ROOT,
        os.path.join(settings.MEDIA_ROOT, 'alunos'),
        os.path.join(settings.MEDIA_ROOT, 'alunos', 'fotos')
    ]
    
    for directory in media_dirs:
        os.makedirs(directory, exist_ok=True)
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'  # não é apps.core
    
    