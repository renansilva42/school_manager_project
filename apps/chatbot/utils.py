# apps/chatbot/utils.py
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import openai
from django.conf import settings
from django.db.models import Avg
from apps.alunos.models import Aluno, Nota

# Verifica a versão do openai para definir a forma correta de uso
try:
    openai_version = openai.__version__
    use_legacy_api = openai_version.startswith("0.")
except AttributeError:
    use_legacy_api = True

def get_openai_response(messages, tools=None, tool_choice="auto"):
    """
    Obtém resposta da API OpenAI com suporte a function calling.
    """

    if use_legacy_api:
        openai.api_key = settings.OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice=tool_choice
        )
    else:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice=tool_choice
        )
    
    return response.choices[0].message

def get_student_info(student_id=None, name=None):
    """
    Busca informações de um aluno pelo ID ou nome.
    """
    try:
        if student_id:
            aluno = Aluno.objects.get(id=student_id)
        elif name:
            aluno = Aluno.objects.filter(nome__icontains=name).first()
        else:
            return "É necessário fornecer um ID ou nome de aluno."
        
        notas = Nota.objects.filter(aluno=aluno)
        media = notas.aggregate(Avg('valor'))['valor__avg'] or 0
        
        return {
            "id": aluno.id,
            "nome": aluno.nome,
            "email": aluno.email,
            "data_nascimento": aluno.data_nascimento.strftime("%d/%m/%Y") if aluno.data_nascimento else "Não informada",
            "media_notas": round(media, 2),
            "numero_notas": notas.count()
        }
    except Aluno.DoesNotExist:
        return "Aluno não encontrado."
    except Exception as e:
        return f"Erro ao buscar informações do aluno: {str(e)}"

def get_student_grades(student_id=None, name=None):
    """
    Busca as notas de um aluno pelo ID ou nome.
    """
    try:
        if student_id:
            aluno = Aluno.objects.get(id=student_id)
        elif name:
            aluno = Aluno.objects.filter(nome__icontains=name).first()
        else:
            return "É necessário fornecer um ID ou nome de aluno."
        
        notas = Nota.objects.filter(aluno=aluno)
        
        if not notas:
            return f"O aluno {aluno.nome} não possui notas registradas."
        
        resultado = []
        for nota in notas:
            resultado.append({
                "disciplina": nota.disciplina,
                "valor": nota.valor,
                "data": nota.data.strftime("%d/%m/%Y") if nota.data else "Não informada"
            })
        
        return resultado
    except Aluno.DoesNotExist:
        return "Aluno não encontrado."
    except Exception as e:
        return f"Erro ao buscar notas do aluno: {str(e)}"
