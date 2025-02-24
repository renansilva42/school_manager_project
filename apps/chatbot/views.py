from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg
from apps.alunos.models import Aluno, Nota  # Ajuste o caminho conforme necessário
from apps.chatbot.utils import get_openai_response  # Ajuste conforme a localização da função
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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

            response = get_openai_response(message)
            return JsonResponse({'response': response})
            
        except Exception as e:
            print(f"Erro no chatbot_response: {e}")
            return JsonResponse({
                'response': 'Desculpe, ocorreu um erro ao processar sua solicitação.'
            })