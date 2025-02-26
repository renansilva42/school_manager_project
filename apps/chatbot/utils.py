import openai
from django.conf import settings
from apps.alunos.models import Aluno, Nota
from django.db.models import Q
from datetime import datetime
import pytz
from typing import Optional, Dict
import json

def get_current_datetime() -> str:
    """
    Retorna a data e hora atuais no fuso horário de Belém, Pará (GMT-3).
    Formato: DD/MM/YYYY HH:MM:SS
    """
    fuso_belem = pytz.timezone("America/Belem")
    agora = datetime.now(fuso_belem)
    return agora.strftime("%d/%m/%Y %H:%M:%S")

def get_student_info(query: str) -> Optional[Dict]:
    """
    Busca informações de um aluno com base no nome fornecido na query.
    Retorna um dicionário com os dados do aluno, incluindo notas e URL da foto, ou None se não encontrado.
    """
    try:
        if not query or len(query) < 3:
            return None
            
        # Normaliza a query removendo prefixos comuns e ajustando para minúsculas
        query = query.lower().strip()
        
        # Lista de palavras a serem removidas da query
        palavras_para_remover = ["notas do", "notas da", "telefone do", "telefone da", 
                                "foto do", "foto da", "endereço do", "endereço da", 
                                "informações do", "informações da", "dados do", "dados da",
                                "aluno", "aluna", "estudante", "o", "a", "do", "da"]
        
        # Remove as palavras da query
        for palavra in palavras_para_remover:
            query = query.replace(palavra, "").strip()
        
        # Busca por correspondência exata no nome
        aluno = Aluno.objects.filter(nome__iexact=query).first()
        
        # Se não encontrado, busca por correspondências parciais
        if not aluno:
            search_terms = query.split()
            if not search_terms:
                return None
                
            # Cria uma consulta inicial
            q_objects = Q(nome__icontains=search_terms[0])
            
            # Adiciona termos adicionais à consulta
            for term in search_terms[1:]:
                q_objects &= Q(nome__icontains=term)
            
            aluno = Aluno.objects.filter(q_objects).first()
        
        if aluno:
            # Coleta notas do aluno
            notas = Nota.objects.filter(aluno=aluno)
            notas_info = [f"{nota.disciplina}: {nota.valor}" for nota in notas]
            
            # Estrutura os dados do aluno
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
        system_prompt = """
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
        
        # Chamada à API com function calling
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            functions=functions,
            function_call="auto",
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
                student_info = get_student_info(function_args.get("student_name", ""))
                
                # Segunda chamada à API com o resultado da função
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
                
                return second_response.choices[0].message["content"]
                
            elif function_name == "get_student_photo":
                student_info = get_student_info(function_args.get("student_name", ""))
                if student_info and student_info.get("foto_url"):
                    return [
                        f"Aqui está a foto de {student_info['nome']}:",
                        {"type": "image", "url": student_info["foto_url"]}
                    ]
                elif student_info:
                    return f"Desculpe, não encontrei uma foto cadastrada para {student_info['nome']}."
                else:
                    return "Desculpe, não encontrei o aluno mencionado."
        
        # Se não houve chamada de função, retorna a resposta direta
        return message["content"]
        
    except Exception as e:
        print(f"Erro na chamada da API OpenAI: {e}")
        return f"Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3)."

# Exemplo de uso para teste
if __name__ == "__main__":
    queries = [
        "oi",
        "oi, preciso saber as notas do João Pedro",
        "qual é o telefone do João Pedro?",
        "mostre a foto do João Pedro"
    ]
    for q in queries:
        print(f"Usuário: {q}")
        print(f"Assistente: {get_openai_response(q)}\n")