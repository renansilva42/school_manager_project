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
        3. Se o usuário pedir QUALQUER informação sobre um aluno, use a função get_student_info para buscar os dados.
        4. Se o usuário pedir a foto de um aluno, use a função get_student_photo.
        5. IMPORTANTE: Quando receber dados de um aluno, SEMPRE inclua as informações específicas solicitadas pelo usuário na sua resposta.
        6. Se você receber informações de um aluno através da função, SEMPRE use essas informações na sua resposta, não diga que está buscando informações que já foram encontradas.
        7. Termine suas respostas com: "Estou à disposição para mais perguntas!"
        8. Inclua a data e hora atuais (horário de Belém, Pará - GMT-3) em todas as respostas.

        A data e hora atuais são: {get_current_datetime()}.
        """
        
        # Expandir a lista de palavras-chave para detectar mais tipos de consultas sobre alunos
        aluno_keywords = [
            "aluno", "estudante", "nota", "notas", "informações", "dados", "foto", 
            "telefone", "endereço", "responsável", "responsavel", "data de nascimento",
            "série", "serie", "turma", "ano", "nível", "nivel", "email", "e-mail",
            "matrícula", "matricula", "turno", "classe", "sala", "professor", "professora",
            "disciplina", "matéria", "materia", "curso", "escola", "colégio", "colegio",
            "quem é", "onde está", "onde mora", "quando nasceu", "qual", "quais"
        ]
        
        # Verificar se a mensagem do usuário parece estar solicitando informações de um aluno
        # Primeiro, verificamos se há alguma palavra-chave
        is_student_query = any(keyword in user_message.lower() for keyword in aluno_keywords)
        
        # Se não encontramos palavras-chave, verificamos se há algum nome próprio na mensagem
        # que possa ser um nome de aluno (primeira letra maiúscula seguida de minúsculas)
        if not is_student_query:
            words = user_message.split()
            for word in words:
                if len(word) > 2 and word[0].isupper() and word[1:].islower():
                    is_student_query = True
                    break
        
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
                    return f"Olá! Desculpe, não consegui encontrar informações para o aluno '{student_name}'. Por favor, verifique se o nome está correto e tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3). Estou à disposição para mais perguntas!"
                
                # Determinar qual informação foi solicitada para garantir que seja incluída na resposta
                requested_info = []
                
                # Mapear palavras-chave para campos no student_info
                info_mapping = {
                    "responsável": "responsavel",
                    "responsavel": "responsavel",
                    "data de nascimento": "data_nascimento",
                    "nascimento": "data_nascimento",
                    "telefone": "telefone",
                    "endereço": "endereco",
                    "endereco": "endereco",
                    "email": "email",
                    "e-mail": "email",
                    "nota": "notas",
                    "notas": "notas",
                    "série": "serie",
                    "serie": "serie",
                    "turma": "serie",
                    "ano": "ano",
                    "nível": "nivel",
                    "nivel": "nivel",
                    "turno": "turno",
                    "matrícula": "matricula",
                    "matricula": "matricula"
                }
                
                # Identificar quais informações foram solicitadas
                for keyword, field in info_mapping.items():
                    if keyword in user_message.lower():
                        requested_info.append(field)
                
                # Se nenhuma informação específica foi solicitada, incluir todas
                if not requested_info:
                    requested_info = list(info_mapping.values())
                
                # Garantir que não há duplicatas
                requested_info = list(set(requested_info))
                
                # Segunda chamada à API com o resultado da função
                try:
                    # Adicionar uma instrução específica para incluir as informações solicitadas
                    specific_instruction = f"O usuário solicitou informações sobre {student_info['nome']}. "
                    specific_instruction += f"Certifique-se de incluir os seguintes campos na sua resposta: {', '.join(requested_info)}. "
                    specific_instruction += "Não diga que está buscando informações, pois elas já foram encontradas."
                    
                    second_response = openai.ChatCompletion.create(
                        model="gpt-4o-mini-2024-07-18",
                        messages=[
                            {"role": "system", "content": system_prompt + "\n\n" + specific_instruction},
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
                            {"role": "system", "content": system_prompt + "\n\n" + specific_instruction},
                            {"role": "user", "content": user_message},
                            {"role": "function", "name": function_name, "content": json.dumps(student_info)}
                        ],
                        temperature=0.7,
                        max_tokens=500,
                        top_p=0.9
                    )
                
                # Verificar se a resposta contém as informações do aluno
                response_content = second_response.choices[0].message["content"]
                
                # Se a resposta não menciona o nome do aluno ou as informações solicitadas, adicione as informações manualmente
                missing_info = []
                for field in requested_info:
                    if field in student_info and str(student_info[field]) not in response_content:
                        missing_info.append(field)
                
                if student_info["nome"] not in response_content or missing_info:
                    # Construir uma resposta manual com as informações solicitadas
                    info_parts = []
                    
                    # Adicionar as informações solicitadas
                    for field in requested_info:
                        if field in student_info:
                            field_display_name = field.replace("_", " ").capitalize()
                            
                            # Formatação especial para alguns campos
                            if field == "notas":
                                if isinstance(student_info[field], list) and student_info[field]:
                                    notas_str = ", ".join(student_info[field])
                                    info_parts.append(f"**Notas**: {notas_str}")
                            else:
                                info_parts.append(f"**{field_display_name}**: {student_info[field]}")
                    
                    # Construir a resposta final
                    info_text = "\n".join(info_parts)
                    response_content = f"Olá! \n\nAqui estão as informações de {student_info['nome']}:\n\n{info_text}\n\nEstou à disposição para mais perguntas! \n\nData e hora atuais: {get_current_datetime()}."
                
                return response_content
                
            elif function_name == "get_student_photo":
                student_name = function_args.get("student_name", "")
                print(f"Buscando foto para o aluno: {student_name}")
                student_info = get_student_info(student_name)
                
                if student_info and student_info.get("foto_url"):
                    return [
                        f"Aqui está a foto de {student_info['nome']}. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3). Estou à disposição para mais perguntas!",
                        {"type": "image", "url": student_info["foto_url"]}
                    ]
                elif student_info:
                    return f"Olá! Desculpe, não encontrei uma foto cadastrada para {student_info['nome']}. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3). Estou à disposição para mais perguntas!"
                else:
                    return f"Olá! Desculpe, não encontrei o aluno '{student_name}'. Por favor, verifique se o nome está correto e tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3). Estou à disposição para mais perguntas!"
        
        # Se não houve chamada de função, retorna a resposta direta
        return message["content"]
        
    except Exception as e:
        print(f"Erro na chamada da API OpenAI: {e}")
        return f"Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3). Estou à disposição para mais perguntas!"