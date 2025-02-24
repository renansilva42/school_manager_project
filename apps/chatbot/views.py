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
        message = request.POST.get('message')
        
        # Busca de aluno
        if "buscar aluno" in message.lower():
            search_term = message.lower().replace("buscar aluno", "").strip()
            alunos = Aluno.objects.filter(
                Q(nome__icontains=search_term) |
                Q(matricula__icontains=search_term)
            )
            if alunos:
                response = "Alunos encontrados:\n"
                for aluno in alunos:
                    response += f"Nome: {aluno.nome}, Matrícula: {aluno.matricula}\n"
            else:
                response = "Nenhum aluno encontrado."

        # Média da turma
        elif "média da turma" in message.lower():
            serie = message.lower().replace("média da turma", "").strip()
            media = Nota.objects.filter(aluno__serie=serie).aggregate(media=Avg('valor'))
            if media['media']:
                response = f"A média da turma {serie} é {media['media']:.2f}"
            else:
                response = f"Não há notas registradas para a turma {serie}"

        # Relatório de notas
        elif "relatório de notas" in message.lower():
            nome_aluno = message.lower().replace("relatório de notas", "").strip()
            aluno = Aluno.objects.filter(nome__icontains=nome_aluno).first()
            if aluno:
                notas = Nota.objects.filter(aluno=aluno)
                response = f"Relatório de notas de {aluno.nome}:\n"
                for nota in notas:
                    response += f"{nota.disciplina}: {nota.valor}\n"
            else:
                response = "Aluno não encontrado."

        # Resposta padrão
        else:
            response = """
            Comandos disponíveis:
            - buscar aluno [nome ou matrícula]
            - média da turma [série]
            - relatório de notas [nome do aluno]
            """

        # Integração com OpenAI
        context = f"Dados do sistema:\n{response}"
        final_response = get_openai_response(message, context)
        
        return JsonResponse({'response': final_response})
