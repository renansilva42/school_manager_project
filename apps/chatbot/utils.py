# apps/chatbot/utils.py
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import openai
from django.conf import settings
from django.db.models import Avg
from apps.alunos.models import Aluno, Nota
from decimal import Decimal

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
    try:
        # Verificar se pelo menos um parâmetro foi fornecido
        if student_id is None and (name is None or name.strip() == ""):
            return {"error": "É necessário fornecer o ID ou o nome do aluno"}
        
        # Buscar o aluno
        if student_id is not None:
            aluno = Aluno.objects.get(id=student_id)
        else:
            # Busca por nome (pode retornar múltiplos resultados)
            alunos = Aluno.objects.filter(nome__icontains=name)
            if not alunos.exists():
                return {"error": f"Nenhum aluno encontrado com o nome '{name}'"}
            elif alunos.count() > 1:
                # Se houver múltiplos resultados, retornar uma lista
                return {
                    "message": f"Encontrados {alunos.count()} alunos com o nome '{name}'",
                    "alunos": [{"id": a.id, "nome": a.nome} for a in alunos]
                }
            aluno = alunos.first()
        
        # Calcular média das notas
        media = aluno.notas.aggregate(Avg('valor'))['valor__avg'] or 0
        
        # Construir a resposta
        response = {
            "id": aluno.id,
            "nome": aluno.nome,
            "email": aluno.email or "Não informado",
            "data_nascimento": aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else "Não informada",
            "media_notas": float(media),
            "foto_url": aluno.foto.url if aluno.foto else None
        }
        
        return response
    except Aluno.DoesNotExist:
        return {"error": f"Aluno com ID {student_id} não encontrado"}
    except Exception as e:
        return {"error": f"Erro ao buscar informações do aluno: {str(e)}"}

# And modify the get_student_grades function
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
            # Convert Decimal to float for JSON serialization
            valor = float(nota.valor) if isinstance(nota.valor, Decimal) else nota.valor
            
            resultado.append({
                "disciplina": nota.disciplina,
                "valor": valor,
                "data": nota.data.strftime("%d/%m/%Y") if nota.data else "Não informada"
            })
        
        return resultado
    except Aluno.DoesNotExist:
        return "Aluno não encontrado."
    except Exception as e:
        return f"Erro ao buscar notas do aluno: {str(e)}"
