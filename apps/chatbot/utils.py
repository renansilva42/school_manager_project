# apps/chatbot/utils.py
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import openai
from django.conf import settings
from django.db.models import Avg, Max, Min
from apps.alunos.models import Aluno, Nota
from decimal import Decimal
from django.urls import reverse

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
    Busca informações detalhadas sobre um aluno pelo ID ou nome.
    Inclui URL da foto se disponível.
    """
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
            "matricula": aluno.matricula,
            "email": aluno.email or "Não informado",
            "data_nascimento": aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else "Não informada",
            "serie": aluno.serie,
            "nivel": aluno.get_nivel_display(),
            "turno": aluno.get_turno_display(),
            "ano": aluno.get_ano_display(),
            "telefone": aluno.telefone or "Não informado",
            "endereco": aluno.endereco or "Não informado",
            "media_notas": float(media),
            "tem_foto": aluno.foto and True or False
        }
        
        # Adicionar URL da foto se disponível
        if aluno.foto:
            # Obter URL completa da foto
            response["foto_url"] = aluno.foto.url
            # Adicionar markdown para exibir a imagem
            response["foto_markdown"] = f"![Foto de {aluno.nome}]({aluno.foto.url})"
        
        return response
    except Aluno.DoesNotExist:
        return {"error": f"Aluno com ID {student_id} não encontrado"}
    except Exception as e:
        return {"error": f"Erro ao buscar informações do aluno: {str(e)}"}

def get_student_grades(student_id=None, name=None):
    """
    Busca as notas de um aluno pelo ID ou nome.
    """
    try:
        # Verificar se pelo menos um parâmetro foi fornecido
        if student_id is None and (name is None or name.strip() == ""):
            return {"error": "É necessário fornecer o ID ou o nome do aluno"}
            
        if student_id:
            aluno = Aluno.objects.get(id=student_id)
        elif name:
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
        
        notas = Nota.objects.filter(aluno=aluno)
        
        if not notas:
            return {
                "aluno": {
                    "id": aluno.id,
                    "nome": aluno.nome
                },
                "message": f"O aluno {aluno.nome} não possui notas registradas."
            }
        
        resultado = {
            "aluno": {
                "id": aluno.id,
                "nome": aluno.nome
            },
            "notas": []
        }
        
        for nota in notas:
            # Convert Decimal to float for JSON serialization
            valor = float(nota.valor) if isinstance(nota.valor, Decimal) else nota.valor
            
            resultado["notas"].append({
                "disciplina": nota.disciplina,
                "valor": valor,
                "data": nota.data.strftime("%d/%m/%Y") if nota.data else "Não informada"
            })
        
        # Calcular média geral
        media = sum(n["valor"] for n in resultado["notas"]) / len(resultado["notas"])
        resultado["media_geral"] = round(media, 2)
        
        return resultado
    except Aluno.DoesNotExist:
        return {"error": f"Aluno com ID {student_id} não encontrado"}
    except Exception as e:
        return {"error": f"Erro ao buscar notas do aluno: {str(e)}"}

def analyze_student_performance(student_id=None, name=None):
    """
    Analisa o desempenho de um aluno com base em suas notas.
    """
    try:
        # Verificar se pelo menos um parâmetro foi fornecido
        if student_id is None and (name is None or name.strip() == ""):
            return {"error": "É necessário fornecer o ID ou o nome do aluno"}
            
        if student_id:
            aluno = Aluno.objects.get(id=student_id)
        elif name:
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
        
        notas = Nota.objects.filter(aluno=aluno)
        
        if not notas:
            return {
                "aluno": {
                    "id": aluno.id,
                    "nome": aluno.nome
                },
                "message": f"O aluno {aluno.nome} não possui notas registradas para análise."
            }
        
        # Agrupar notas por disciplina
        disciplinas = {}
        for nota in notas:
            valor = float(nota.valor) if isinstance(nota.valor, Decimal) else nota.valor
            if nota.disciplina not in disciplinas:
                disciplinas[nota.disciplina] = []
            disciplinas[nota.disciplina].append(valor)
        
        # Calcular estatísticas por disciplina
        analise_disciplinas = []
        for disciplina, valores in disciplinas.items():
            media = sum(valores) / len(valores)
            analise_disciplinas.append({
                "disciplina": disciplina,
                "media": round(media, 2),
                "maior_nota": max(valores),
                "menor_nota": min(valores),
                "quantidade_notas": len(valores),
                "situacao": "Aprovado" if media >= 6 else "Em recuperação" if media >= 4 else "Reprovado"
            })
        
        # Calcular média geral
        todas_notas = [nota for notas_disc in disciplinas.values() for nota in notas_disc]
        media_geral = sum(todas_notas) / len(todas_notas)
        
        # Determinar disciplinas com melhor e pior desempenho
        disciplinas_ordenadas = sorted(analise_disciplinas, key=lambda x: x["media"], reverse=True)
        melhor_disciplina = disciplinas_ordenadas[0] if disciplinas_ordenadas else None
        pior_disciplina = disciplinas_ordenadas[-1] if disciplinas_ordenadas else None
        
        resultado = {
            "aluno": {
                "id": aluno.id,
                "nome": aluno.nome,
                "serie": aluno.serie,
                "turno": aluno.get_turno_display()
            },
            "media_geral": round(media_geral, 2),
            "situacao_geral": "Aprovado" if media_geral >= 6 else "Em recuperação" if media_geral >= 4 else "Reprovado",
            "disciplinas": analise_disciplinas,
            "melhor_desempenho": melhor_disciplina,
            "pior_desempenho": pior_disciplina
        }
        
        return resultado
    except Aluno.DoesNotExist:
        return {"error": f"Aluno com ID {student_id} não encontrado"}
    except Exception as e:
        return {"error": f"Erro ao analisar desempenho do aluno: {str(e)}"}

def compare_students(student_names=None, student_ids=None):
    """
    Compara o desempenho de dois ou mais alunos.
    """
    try:
        alunos = []
        
        # Buscar alunos por ID
        if student_ids:
            for id in student_ids:
                try:
                    aluno = Aluno.objects.get(id=id)
                    alunos.append(aluno)
                except Aluno.DoesNotExist:
                    pass
        
        # Buscar alunos por nome
        if student_names:
            for nome in student_names:
                aluno = Aluno.objects.filter(nome__icontains=nome).first()
                if aluno and aluno not in alunos:
                    alunos.append(aluno)
        
        if not alunos:
            return {"error": "Nenhum aluno encontrado para comparação"}
        
        if len(alunos) < 2:
            return {"error": "É necessário pelo menos dois alunos para fazer uma comparação"}
        
        # Coletar dados de cada aluno
        dados_alunos = []
        for aluno in alunos:
            notas = Nota.objects.filter(aluno=aluno)
            
            if not notas:
                dados_alunos.append({
                    "id": aluno.id,
                    "nome": aluno.nome,
                    "serie": aluno.serie,
                    "turno": aluno.get_turno_display(),
                    "sem_notas": True
                })
                continue
            
            # Calcular média geral
            media = notas.aggregate(Avg('valor'))['valor__avg'] or 0
            media = float(media) if isinstance(media, Decimal) else media
            
            # Agrupar notas por disciplina
            disciplinas = {}
            for nota in notas:
                valor = float(nota.valor) if isinstance(nota.valor, Decimal) else nota.valor
                if nota.disciplina not in disciplinas:
                    disciplinas[nota.disciplina] = []
                disciplinas[nota.disciplina].append(valor)
            
            # Calcular médias por disciplina
            medias_disciplinas = {}
            for disciplina, valores in disciplinas.items():
                medias_disciplinas[disciplina] = round(sum(valores) / len(valores), 2)
            
            dados_alunos.append({
                "id": aluno.id,
                "nome": aluno.nome,
                "serie": aluno.serie,
                "turno": aluno.get_turno_display(),
                "media_geral": round(media, 2),
                "medias_disciplinas": medias_disciplinas,
                "sem_notas": False
            })
        
        # Encontrar disciplinas em comum
        todas_disciplinas = set()
        for dados in dados_alunos:
            if not dados.get("sem_notas"):
                todas_disciplinas.update(dados["medias_disciplinas"].keys())
        
        disciplinas_comuns = list(todas_disciplinas)
        
        # Preparar comparação por disciplina
        comparacao_disciplinas = {}
        for disciplina in disciplinas_comuns:
            comparacao_disciplinas[disciplina] = []
            for dados in dados_alunos:
                if not dados.get("sem_notas") and disciplina in dados["medias_disciplinas"]:
                    comparacao_disciplinas[disciplina].append({
                        "aluno": dados["nome"],
                        "media": dados["medias_disciplinas"][disciplina]
                    })
            # Ordenar por média (maior para menor)
            comparacao_disciplinas[disciplina] = sorted(
                comparacao_disciplinas[disciplina], 
                key=lambda x: x["media"], 
                reverse=True
            )
        
        # Determinar aluno com melhor desempenho geral
        alunos_com_notas = [a for a in dados_alunos if not a.get("sem_notas")]
        if alunos_com_notas:
            melhor_aluno = max(alunos_com_notas, key=lambda x: x["media_geral"])
        else:
            melhor_aluno = None
        
        resultado = {
            "alunos": dados_alunos,
            "disciplinas_comuns": disciplinas_comuns,
            "comparacao_disciplinas": comparacao_disciplinas,
            "melhor_desempenho_geral": melhor_aluno
        }
        
        return resultado
    except Exception as e:
        return {"error": f"Erro ao comparar alunos: {str(e)}"}