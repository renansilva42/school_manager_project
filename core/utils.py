from django.core.mail import send_mail
from django.conf import settings
from .models import SiteSettings
import logging

logger = logging.getLogger(__name__)

def send_email_with_site_settings(subject, message, recipient_list, html_message=None):
    """
    Envia um email usando as configurações SMTP definidas nas configurações do site.
    
    Args:
        subject (str): Assunto do email
        message (str): Corpo do email (texto plano)
        recipient_list (list): Lista de destinatários
        html_message (str, optional): Corpo do email em HTML. Defaults to None.
        
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    site_settings = SiteSettings.get_settings()
    
    # Verifica se as configurações de email estão definidas
    if not site_settings.smtp_server or not site_settings.smtp_port:
        logger.warning("Tentativa de envio de email sem configurações SMTP definidas")
        return False
    
    # Define o remetente como o email de contato das configurações do site
    from_email = site_settings.contact_email or settings.DEFAULT_FROM_EMAIL
    
    try:
        # Configura as configurações de email temporariamente para este envio
        email_settings = {
            'EMAIL_HOST': site_settings.smtp_server,
            'EMAIL_PORT': site_settings.smtp_port,
            # Outras configurações podem ser adicionadas conforme necessário
        }
        
        # Salva as configurações originais
        original_host = settings.EMAIL_HOST
        original_port = settings.EMAIL_PORT
        
        # Aplica as configurações temporárias
        settings.EMAIL_HOST = email_settings['EMAIL_HOST']
        settings.EMAIL_PORT = email_settings['EMAIL_PORT']
        
        # Envia o email
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        
        # Restaura as configurações originais
        settings.EMAIL_HOST = original_host
        settings.EMAIL_PORT = original_port
        
        logger.info(f"Email enviado com sucesso para {', '.join(recipient_list)}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
        return False
