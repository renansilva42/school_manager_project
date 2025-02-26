from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg
from apps.alunos.models import Aluno, Nota
from apps.chatbot.utils import get_openai_response, get_student_info
from django.shortcuts import render

@login_required
def chatbot(request):
    """
    View function para renderizar a página principal do chatbot
    """
    return render(request, 'chatbot/chatbot.html')

@login_required
def chatbot_response(request):
    if request.method == 'POST':
        try:
            message = request.POST.get('message', '').strip()
            if not message:
                return JsonResponse({'response': 'Por favor, digite uma mensagem.'})

            # Usa a função otimizada que já trata fotos internamente
            response = get_openai_response(message)
            
            # Verifica se a resposta é uma lista contendo uma imagem
            if isinstance(response, list) and len(response) > 1 and isinstance(response[1], dict) and response[1].get('type') == 'image':
                return JsonResponse({
                    'response': response
                })
            
            return JsonResponse({'response': response})
            
        except Exception as e:
            print(f"Erro no chatbot_response: {e}")
            return JsonResponse({
                'response': 'Desculpe, ocorreu um erro ao processar sua solicitação.'
            })