from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg
from .utils import get_openai_response
from apps.alunos.models import Aluno, Nota

@login_required
def chatbot(request):
    return render(request, 'chatbot/chatbot.html')

@login_required
def chatbot_response(request):
    if request.method == 'POST':
        user_message = request.POST.get('message').lower()
        
        if 'buscar aluno' in user_message:
            termo_busca = user_message.split('buscar aluno')[-1].strip()
            alunos = Aluno.objects.filter(
                Q(nome__icontains=termo_busca) |
                Q(matricula__icontains=termo_busca) |
                Q(serie__icontains=termo_busca)
            )
            if alunos:
                context = "Alunos encontrados:\n"
                for aluno in alunos:
                    context += f"- {aluno.nome} (Matrícula: {aluno.matricula}, Série: {aluno.serie})\n"
            else:
                context = f"Nenhum aluno encontrado com o termo '{termo_busca}'"
        
        elif 'média da turma' in user_message:
            serie = user_message.split('média da turma')[-1].strip()
            media_turma = Nota.objects.filter(aluno__serie=serie).aggregate(Avg('valor'))['valor__avg']
            context = f"A média da turma {serie} é {media_turma:.2f}" if media_turma else f"Sem dados para a turma {serie}"
        
        elif 'relatório de notas' in user_message:
            nome_aluno = user_message.split('relatório de notas')[-1].strip()
            aluno = Aluno.objects.filter(nome__icontains=nome_aluno).first()
            if aluno:
                notas = Nota.objects.filter(aluno=aluno)
                context = f"Relatório de notas de {aluno.nome}:\n"
                for nota in notas:
                    context += f"- {nota.disciplina}: {nota.valor} ({nota.data})\n"
            else:
                context = f"Aluno '{nome_aluno}' não encontrado"
        
        else:
            context = "Comandos disponíveis:\n- Buscar aluno [nome ou matrícula]\n- Média da turma [série]\n- Relatório de notas [nome do aluno]"

        response = get_openai_response(user_message, context)
        return JsonResponse({'response': response})
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)