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
                          "aluno", "aluna", "estudante", "o", "a", "do", "da",
                          "responsável do", "responsável da", "responsável",
                          "série do", "série da", "série", "turma do", "turma da", "turma",
                          "email do", "email da", "email", "e-mail do", "e-mail da", "e-mail"]
        
        # Remove words from the query
        normalized_query = original_query
        for word in words_to_remove:
            normalized_query = normalized_query.replace(word, "").strip()
        
        # If normalization removed too much, use the original query
        if len(normalized_query) < 2:
            normalized_query = original_query
            
        print(f"Query normalizada: '{normalized_query}'")
        
        # Store both the normalized and original query for searching
        search_queries = [normalized_query]
        if normalized_query != original_query:
            search_queries.append(original_query)
            
        # Add individual words from the query for better matching
        words = normalized_query.split()
        for word in words:
            if len(word) >= 3 and word not in search_queries:  # Only add words with 3+ characters
                search_queries.append(word)
                
        print(f"Search queries: {search_queries}")
        
        # Try different search strategies
        aluno = None
        
        # 1. Try exact match with any of the search queries
        for query_term in search_queries:
            aluno = Aluno.objects.filter(nome__iexact=query_term).first()
            if aluno:
                break
        
        # 2. Try first name match for single name queries
        if not aluno:
            for query_term in search_queries:
                if len(query_term.split()) == 1 and len(query_term) >= 2:
                    # Look for students whose first name matches the query
                    for student in Aluno.objects.all():
                        student_first_name = student.nome.split()[0].lower()
                        if student_first_name == query_term.lower():
                            aluno = student
                            break
                if aluno:
                    break
        
        # 3. Try contains match with any part of the name
        if not aluno:
            for query_term in search_queries:
                if len(query_term) >= 2:
                    aluno = Aluno.objects.filter(nome__icontains=query_term).first()
                    if aluno:
                        break
        
        # 4. Try fuzzy matching as a last resort
        if not aluno:
            best_match = None
            highest_score = 0
            
            for student in Aluno.objects.all():
                for query_term in search_queries:
                    # Simple similarity score: count of matching characters / max length
                    student_name_lower = student.nome.lower()
                    query_lower = query_term.lower()
                    
                    # Count matching characters
                    matches = sum(1 for c in query_lower if c in student_name_lower)
                    score = matches / max(len(query_lower), len(student_name_lower))
                    
                    if score > highest_score and score > 0.5:  # Threshold of 50% similarity
                        highest_score = score
                        best_match = student
            
            if best_match:
                aluno = best_match
        
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
                "serie": aluno.serie if aluno.serie else "Não informado",
                "nivel": aluno.get_nivel_display() if hasattr(aluno, 'get_nivel_display') else "Não informado",
                "ano": aluno.get_ano_display() if hasattr(aluno, 'get_ano_display') else "Não informado",
                "turno": aluno.get_turno_display() if hasattr(aluno, 'get_turno_display') else "Não informado",
                "email": aluno.email if aluno.email else "Não informado",
                "telefone": aluno.telefone if aluno.telefone else "Não informado",
                "endereco": aluno.endereco if aluno.endereco else "Não informado",
                "notas": notas_info if notas_info else ["Nenhuma nota registrada"],
                "responsavel": aluno.dados_adicionais if aluno.dados_adicionais else "Não informado",
                "foto_url": aluno.foto.url if aluno.foto else None
            }
            return aluno_info
        else:
            print(f"Nenhum aluno encontrado para as queries: {search_queries}")
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
        5. IMPORTANTE: Quando receber dados de um aluno, SEMPRE inclua as informações específicas solicitadas pelo usuário (como data de nascimento, responsável, etc.) na sua resposta.
        6. Se você receber informações de um aluno através da função, SEMPRE use essas informações na sua resposta, não diga que está buscando informações que já foram encontradas.
        7. Termine suas respostas com: "Estou à disposição para mais perguntas!"
        8. NÃO use asteriscos (**) para formatação. Use formatação simples como "Nome: valor".
        9. NÃO inclua a data e hora atuais nas suas respostas.
        """
        
        # Verificar se a mensagem do usuário parece estar solicitando informações de um aluno
        aluno_keywords = ["aluno", "estudante", "nota", "notas", "informações", "dados", "foto", "telefone", "endereço", "responsável", "responsavel", "data de nascimento", "série", "serie", "turma", "ano", "turno"]
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
                
                # Adicionar log para depuração
                if student_info:
                    print(f"Informações encontradas para o aluno: {json.dumps(student_info, ensure_ascii=False)}")
                else:
                    print(f"Nenhuma informação encontrada para o aluno: {student_name}")
                
                if not student_info:
                    return f"Olá! Desculpe, não consegui encontrar informações para o aluno '{student_name}'. Por favor, verifique se o nome está correto e tente novamente. Estou à disposição para mais perguntas!"
                
                # Segunda chamada à API com o resultado da função
                try:
                    # Adicionar instruções específicas para não usar asteriscos e não incluir data/hora
                    specific_instruction = """
                    IMPORTANTE:
                    1. NÃO use asteriscos (**) para formatação. Use formatação simples como "Nome: valor".
                    2. NÃO inclua a data e hora atuais na sua resposta.
                    """
                    
                    second_response = openai.ChatCompletion.create(
                        model="gpt-4o-mini-2024-07-18",
                        messages=[
                            {"role": "system", "content": system_prompt + specific_instruction},
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
                            {"role": "system", "content": system_prompt + specific_instruction},
                            {"role": "user", "content": user_message},
                            {"role": "function", "name": function_name, "content": json.dumps(student_info)}
                        ],
                        temperature=0.7,
                        max_tokens=500,
                        top_p=0.9
                    )
                
                # Verificar se a resposta contém as informações do aluno
                response_content = second_response.choices[0].message["content"]
                
                # Remover qualquer menção a data e hora
                response_content = remove_datetime_references(response_content)
                
                # Remover asteriscos da formatação
                response_content = response_content.replace("**", "")
                
                # Se a resposta não menciona o nome do aluno, adicione as informações manualmente
                if student_info["nome"] not in response_content:
                    # Determinar qual informação foi solicitada
                    info_requested = ""
                    if "responsável" in user_message.lower() or "responsavel" in user_message.lower():
                        info_requested = f"O responsável por {student_info['nome']} é {student_info['responsavel']}."
                    elif "data de nascimento" in user_message.lower() or "nascimento" in user_message.lower():
                        info_requested = f"A data de nascimento de {student_info['nome']} é {student_info['data_nascimento']}."
                    elif "telefone" in user_message.lower():
                        info_requested = f"O telefone de {student_info['nome']} é {student_info['telefone']}."
                    elif "endereço" in user_message.lower() or "endereco" in user_message.lower():
                        info_requested = f"O endereço de {student_info['nome']} é {student_info['endereco']}."
                    elif "email" in user_message.lower():
                        info_requested = f"O email de {student_info['nome']} é {student_info['email']}."
                    elif "nota" in user_message.lower():
                        notas_str = ", ".join(student_info['notas'])
                        info_requested = f"As notas de {student_info['nome']} são: {notas_str}."
                    elif "série" in user_message.lower() or "serie" in user_message.lower() or "turma" in user_message.lower():
                        info_requested = f"A série de {student_info['nome']} é {student_info['serie']}."
                    elif "ano" in user_message.lower():
                        info_requested = f"O ano de {student_info['nome']} é {student_info['ano']}."
                    elif "turno" in user_message.lower():
                        info_requested = f"O turno de {student_info['nome']} é {student_info['turno']}."
                    else:
                        info_requested = f"Informações de {student_info['nome']}: Matrícula: {student_info['matricula']}, Data de Nascimento: {student_info['data_nascimento']}, Série: {student_info['serie']}, Responsável: {student_info['responsavel']}."
                    
                    # Adicionar a informação à resposta
                    response_content = f"Olá! {info_requested}\n\nEstou à disposição para mais perguntas!"
                
                return response_content
                
            elif function_name == "get_student_photo":
                student_name = function_args.get("student_name", "")
                print(f"Buscando foto para o aluno: {student_name}")
                student_info = get_student_info(student_name)
                
                if student_info and student_info.get("foto_url"):
                    # Remover menção a data e hora
                    return [
                        f"Aqui está a foto de {student_info['nome']}. Estou à disposição para mais perguntas!",
                        {"type": "image", "url": student_info["foto_url"]}
                    ]
                elif student_info:
                    return f"Olá! Desculpe, não encontrei uma foto cadastrada para {student_info['nome']}. Estou à disposição para mais perguntas!"
                else:
                    return f"Olá! Desculpe, não encontrei o aluno '{student_name}'. Por favor, verifique se o nome está correto e tente novamente. Estou à disposição para mais perguntas!"
        
        # Se não houve chamada de função, retorna a resposta direta
        # Remover qualquer menção a data e hora
        response_content = message["content"]
        response_content = remove_datetime_references(response_content)
        
        return response_content
        
    except Exception as e:
        print(f"Erro na chamada da API OpenAI: {e}")
        return f"Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente. Estou à disposição para mais perguntas!"

def remove_datetime_references(text):
    """
    Remove referências a data e hora do texto.
    """
    # Padrões comuns de data e hora
    patterns = [
        r"Data e hora atuais: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\.",
        r"Data e hora: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\.",
        r"A data e hora atuais são: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}.*",
        r"A data e hora atuais são: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",
        r"\(horário de Belém, Pará - GMT-3\)",
        r"Data e hora atuais: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",
        r"Data e hora: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}"
    ]
    
    result = text
    for pattern in patterns:
        import re
        result = re.sub(pattern, "", result)
    
    # Remover linhas vazias extras que podem ter sido criadas
    result = re.sub(r'\n\s*\n', '\n\n', result)
    
    # Remover espaços em branco no final
    result = result.strip()
    
    return result