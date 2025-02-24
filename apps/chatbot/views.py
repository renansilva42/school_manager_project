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

            # Verifica se a mensagem contém pedido de foto
            if 'foto' in message.lower() or 'imagem' in message.lower():
                info_aluno = None
                palavras = message.lower().split()
                for palavra in palavras:
                    info_aluno = get_student_info(palavra)
                    if info_aluno and info_aluno.get('foto_url'):
                        return JsonResponse({
                            'response': [
                                f"Aqui está a foto de {info_aluno['nome']}:",
                                {'type': 'image', 'url': info_aluno['foto_url']}
                            ]
                        })
                    elif info_aluno:
                        return JsonResponse({
                            'response': f"Desculpe, não encontrei uma foto cadastrada para {info_aluno['nome']}."
                        })
                return JsonResponse({
                    'response': "Desculpe, não encontrei o aluno mencionado."
                })

            response = get_openai_response(message)
            return JsonResponse({'response': response})
            
        except Exception as e:
            print(f"Erro no chatbot_response: {e}")
            return JsonResponse({
                'response': 'Desculpe, ocorreu um erro ao processar sua solicitação.'
            })