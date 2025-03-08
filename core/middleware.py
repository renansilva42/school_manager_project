import logging
from django.urls import NoReverseMatch
from django.http import HttpResponseServerError
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

class URLErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except NoReverseMatch as e:
            logger.error(f"URL Reverse Error: {str(e)}", exc_info=True, extra={
                'request': request,
                'url': request.path,
                'method': request.method,
                'user': request.user
            })
            
            # Renderizar template de erro personalizado
            context = {
                'error_message': 'Erro na resolução da URL',
                'error_details': str(e)
            }
            content = render_to_string('errors/url_error.html', context)
            return HttpResponseServerError(content)