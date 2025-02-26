# apps/chatbot/utils.py
import openai
from django.conf import settings
from apps.alunos.models import Aluno, Nota
from django.db.models import Q
from datetime import datetime
import pytz
from typing import Optional, Dict, List
import json

def get_current_datetime() -> str:
    """
    Retorna a data e hora atuais no fuso horário de Belém, Pará (GMT-3).
    Formato: DD/MM/YYYY HH:MM:SS
    """
    fuso_belem = pytz.timezone("America/Belem")
    agora = datetime.now(fuso_belem)
    return agora.strftime("%d/%m/%Y %H:%M:%S")

def get_all_students() -> List[Dict]:
    """
    Retorna uma lista com todos os alunos cadastrados no sistema.
    """
    try:
        alunos = Aluno.objects.all().order_by('nome')
        if not alunos.exists():
            return []
            
        alunos_list = []
        for aluno in alunos:
            alunos_list.append({
                "nome": aluno.nome,
                "matricula": aluno.matricula,
                "serie": aluno.serie,
                "ano": aluno.get_ano_display(),
                "turno": aluno.get_turno_display()
            })
        return alunos_list
    except Exception as e:
        print(f"Erro ao buscar lista de alunos: {e}")
        return []

def get_student_info(query: str) -> Optional[Dict]:
    try:
        if not query or len(query) < 2:  # Minimum 2 characters
            return None
            
        # Normalize the query by removing common prefixes and converting to lowercase
        original_query = query.lower().strip()
        
        # List of words to be removed from the query
        words_to_remove = ["notas do", "notas da", "telefone do", "telefone da", 
                          "foto do", "foto da", "endereço do", "endereço da", 
                          "informações do", "informações da", "dados do", "dados da",
                          "aluno", "aluna", "estudante", "o", "a", "do", "da"]
        
        # Remove words from the query
        normalized_query = original_query
        for word in words_to_remove:
            normalized_query = normalized_query.replace(word, "").strip()
        
        # If normalization removed too much, use the original query
        if len(normalized_query) < 2:
            normalized_query = original_query
            
        print(f"Query normalizada: '{normalized_query}'")
        
        # Try different search strategies
        
        # 1. First try exact match
        aluno = Aluno.objects.filter(nome__iexact=normalized_query).first()
        
        # 2. Try first name match
        if not aluno:
            first_name = normalized_query.split()[0] if normalized_query.split() else normalized_query
            if len(first_name) >= 2:
                aluno = Aluno.objects.filter(nome__istartswith=first_name).first()
        
        # 3. Try partial match at the beginning
        if not aluno:
            aluno = Aluno.objects.filter(nome__istartswith=normalized_query).first()
        
        # 4. Try contains match
        if not aluno:
            aluno = Aluno.objects.filter(nome__icontains=normalized_query).first()
        
        # 5. Try with original query if normalized query failed
        if not aluno and normalized_query != original_query:
            aluno = Aluno.objects.filter(
                Q(nome__iexact=original_query) | 
                Q(nome__istartswith=original_query) | 
                Q(nome__icontains=original_query)
            ).first()
        
        if aluno:
            print(f"Aluno encontrado: {aluno.nome}")
            # Collect student grades
            notas = Nota.objects.filter(aluno=aluno)
            notas_info = [f"{nota.disciplina}: {nota.valor}" for nota in notas]
            
            # Structure student data
            aluno_info = {
                "nome": aluno.nome,
                "matricula": aluno.matricula,
                "data_nascimento": aluno.data_nascimento.strftime("%d/%m/%Y") if aluno.data_nascimento else "Não informado",
                "serie": aluno.serie,
                "email": aluno.email if aluno.email else "Não informado",
                "telefone": aluno.telefone if aluno.telefone else "Não informado",
                "endereco": aluno.endereco if aluno.endereco else "Não informado",
                "notas": notas_info if notas_info else ["Nenhuma nota registrada"],
                "responsavel": aluno.dados_adicionais if aluno.dados_adicionais else "Não informado",
                "foto_url": aluno.foto.url if aluno.foto else None
            }
            return aluno_info
        else:
            print(f"Nenhum aluno encontrado para a query: '{normalized_query}'")
            return None
    except Exception as e:
        print(f"Erro ao buscar informações do aluno: {e}")
        return None

def get_openai_response(user_message: str, context: str = "") -> str:
    try:
        # Verificação da chave API
        if not settings.OPENAI_API_KEY:
            return "Erro: Chave da API OpenAI não configurada. Por favor, contate o administrador."
        
        openai.api_key = settings.OPENAI_API_KEY
        
        # Definição das funções disponíveis para o modelo
        functions = [
            {
                "name": "get_student_info",
                "description": "Busca informações detalhadas sobre um aluno pelo nome",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "student_name": {
                            "type": "string",
                            "description": "Nome do aluno a ser buscado"
                        }
                    },
                    "required": ["student_name"]
                }
            },
            {
                "name": "get_student_photo",
                "description": "Busca a foto de um aluno pelo nome",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "student_name": {
                            "type": "string",
                            "description": "Nome do aluno cuja foto será buscada"
                        }
                    },
                    "required": ["student_name"]
                }
            }
        ]
        
        # Prompt do sistema
        system_prompt = f"""
        Você é um assistente escolar amigável e prestativo da Escola Manager, com acesso aos dados dos alunos.
        Regras importantes:
        1. Sempre mantenha um tom amigável, acolhedor e profissional.
        2. Comece suas respostas com uma saudação apropriada, como "Olá!" ou "Oi!".
        3. Se o usuário pedir informações sobre um aluno, use a função get_student_info para buscar os dados.
        4. Se o usuário pedir a foto de um aluno, use a função get_student_photo.
        5. Termine suas respostas com: "Estou à disposição para mais perguntas!"
        6. Inclua a data e hora atuais (horário de Belém, Pará - GMT-3) em todas as respostas.

        A data e hora atuais são: {get_current_datetime()}.
        """
        
        # Verificar se a mensagem do usuário parece estar solicitando informações de um aluno
        aluno_keywords = ["aluno", "estudante", "nota", "notas", "informações", "dados", "foto", "telefone", "endereço"]
        is_student_query = any(keyword in user_message.lower() for keyword in aluno_keywords)
        
        # Chamada à API com function calling
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                functions=functions if is_student_query else None,
                function_call="auto" if is_student_query else None,
                temperature=0.7,
                max_tokens=500,
                top_p=0.9
            )
        except Exception as api_error:
            print(f"Erro na chamada da API OpenAI, tentando modelo alternativo: {api_error}")
            # Tentar com um modelo alternativo se o primeiro falhar
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                functions=functions if is_student_query else None,
                function_call="auto" if is_student_query else None,
                temperature=0.7,
                max_tokens=500,
                top_p=0.9
            )
        
        # Processamento da resposta
        message = response.choices[0].message
        
        # Verifica se o modelo decidiu chamar uma função
        if message.get("function_call"):
            function_name = message["function_call"]["name"]
            function_args = json.loads(message["function_call"]["arguments"])
            
            # Executa a função apropriada
            if function_name == "get_student_info":
                student_name = function_args.get("student_name", "")
                print(f"Buscando informações para o aluno: {student_name}")
                student_info = get_student_info(student_name)
                
                if not student_info:
                    return f"Desculpe, não consegui encontrar informações para o aluno '{student_name}'. Por favor, verifique se o nome está correto e tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3)."
                
                # Segunda chamada à API com o resultado da função
                try:
                    second_response = openai.ChatCompletion.create(
                        model="gpt-4o-mini-2024-07-18",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                            {"role": "function", "name": function_name, "content": json.dumps(student_info)}
                        ],
                        temperature=0.7,
                        max_tokens=500,
                        top_p=0.9
                    )
                except Exception as api_error:
                    print(f"Erro na segunda chamada da API OpenAI, tentando modelo alternativo: {api_error}")
                    second_response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                            {"role": "function", "name": function_name, "content": json.dumps(student_info)}
                        ],
                        temperature=0.7,
                        max_tokens=500,
                        top_p=0.9
                    )
                
                return second_response.choices[0].message["content"]
                
            elif function_name == "get_student_photo":
                student_name = function_args.get("student_name", "")
                print(f"Buscando foto para o aluno: {student_name}")
                student_info = get_student_info(student_name)
                
                if student_info and student_info.get("foto_url"):
                    return [
                        f"Aqui está a foto de {student_info['nome']}. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3).",
                        {"type": "image", "url": student_info["foto_url"]}
                    ]
                elif student_info:
                    return f"Desculpe, não encontrei uma foto cadastrada para {student_info['nome']}. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3)."
                else:
                    return f"Desculpe, não encontrei o aluno '{student_name}'. Por favor, verifique se o nome está correto e tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3)."
        
        # Se não houve chamada de função, retorna a resposta direta
        return message["content"]
        
    except Exception as e:
        print(f"Erro na chamada da API OpenAI: {e}")
        return f"Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3)."