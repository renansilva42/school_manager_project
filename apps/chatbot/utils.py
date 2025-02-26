# apps/chatbot/utils.py
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

import openai
import pytz
from django.conf import settings
from django.db.models import Q

from apps.alunos.models import Aluno, Nota


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
        alunos = Aluno.objects.all().order_by("nome")
        if not alunos.exists():
            return []

        alunos_list = []
        for aluno in alunos:
            alunos_list.append({
                "nome": aluno.nome,
                "matricula": aluno.matricula,
                "serie": aluno.serie,
                "ano": aluno.get_ano_display(),
                "turno": aluno.get_turno_display(),
            })
        return alunos_list
    except Exception as e:
        print(f"Erro ao buscar lista de alunos: {e}")
        return []


def get_student_info(query: str) -> Optional[Dict]:
    """
    Busca informações detalhadas sobre um aluno pelo nome.
    """
    try:
        if not query or len(query) < 2:  # Verifica se a query tem pelo menos 2 caracteres
            return None

        # Normaliza a query removendo prefixos comuns e convertendo para minúsculas
        original_query = query.lower().strip()

        # Lista de palavras a serem removidas da query
        words_to_remove = [
            "notas do", "notas da", "telefone do", "telefone da",
            "foto do", "foto da", "endereço do", "endereço da",
            "informações do", "informações da", "dados do", "dados da",
            "aluno", "aluna", "estudante", "o", "a", "do", "da",
            "responsável do", "responsável da", "responsável",
            "série do", "série da", "série", "turma do", "turma da", "turma",
            "email do", "email da", "email", "e-mail do", "e-mail da", "e-mail",
        ]

        # Remove palavras da query
        normalized_query = original_query
        for word in words_to_remove:
            normalized_query = normalized_query.replace(word, "").strip()

        # Se a normalização removeu muito, usa a query original
        if len(normalized_query) < 2:
            normalized_query = original_query

        print(f"Query normalizada: '{normalized_query}'")

        # Armazena ambas as queries (normalizada e original) para busca
        search_queries = [normalized_query]
        if normalized_query != original_query:
            search_queries.append(original_query)

        # Adiciona palavras individuais da query para melhor correspondência
        words = normalized_query.split()
        for word in words:
            if len(word) >= 3 and word not in search_queries:
                search_queries.append(word)

        print(f"Search queries: {search_queries}")

        # Tenta diferentes estratégias de busca
        aluno = None

        # 1. Tenta correspondência exata com qualquer uma das queries
        for query_term in search_queries:
            aluno = Aluno.objects.filter(nome__iexact=query_term).first()
            if aluno:
                break

        # 2. Tenta correspondência com o primeiro nome para queries de nome único
        if not aluno:
            for query_term in search_queries:
                if len(query_term.split()) == 1 and len(query_term) >= 2:
                    for student in Aluno.objects.all():
                        student_first_name = student.nome.split()[0].lower()
                        if student_first_name == query_term.lower():
                            aluno = student
                            break
                if aluno:
                    break

        # 3. Tenta correspondência parcial com qualquer parte do nome
        if not aluno:
            for query_term in search_queries:
                if len(query_term) >= 2:
                    aluno = Aluno.objects.filter(nome__icontains=query_term).first()
                    if aluno:
                        break

        # 4. Usa correspondência aproximada como último recurso
        if not aluno:
            best_match = None
            highest_score = 0

            for student in Aluno.objects.all():
                for query_term in search_queries:
                    student_name_lower = student.nome.lower()
                    query_lower = query_term.lower()

                    # Calcula pontuação de similaridade simples
                    matches = sum(1 for c in query_lower if c in student_name_lower)
                    score = matches / max(len(query_lower), len(student_name_lower))

                    if score > highest_score and score > 0.5:  # Limiar de 50%
                        highest_score = score
                        best_match = student

            if best_match:
                aluno = best_match

        if aluno:
            print(f"Aluno encontrado: {aluno.nome}")
            # Coleta as notas do aluno
            notas = Nota.objects.filter(aluno=aluno)
            notas_info = [f"{nota.disciplina}: {nota.valor}" for nota in notas]

            # Estrutura os dados do aluno
            aluno_info = {
                "nome": aluno.nome,
                "matricula": aluno.matricula,
                "data_nascimento": (aluno.data_nascimento.strftime("%d/%m/%Y")
                                    if aluno.data_nascimento else "Não informado"),
                "serie": aluno.serie if aluno.serie else "Não informado",
                "nivel": (aluno.get_nivel_display()
                          if hasattr(aluno, "get_nivel_display")
                          else "Não informado"),
                "ano": (aluno.get_ano_display()
                        if hasattr(aluno, "get_ano_display")
                        else "Não informado"),
                "turno": (aluno.get_turno_display()
                          if hasattr(aluno, "get_turno_display")
                          else "Não informado"),
                "email": aluno.email if aluno.email else "Não informado",
                "telefone": aluno.telefone if aluno.telefone else "Não informado",
                "endereco": aluno.endereco if aluno.endereco else "Não informado",
                "notas": notas_info if notas_info else ["Nenhuma nota registrada"],
                "responsavel": (aluno.dados_adicionais
                                if aluno.dados_adicionais
                                else "Não informado"),
                "foto_url": aluno.foto.url if aluno.foto else None,
            }
            return aluno_info
        else:
            print(f"Nenhum aluno encontrado para as queries: {search_queries}")
            return None
    except Exception as e:
        print(f"Erro ao buscar informações do aluno: {e}")
        return None


def get_openai_response(user_message: str, context: str = "") -> str:
    """
    Obtém uma resposta da API OpenAI baseada na mensagem do usuário.
    """
    try:
        # Verifica a chave da API
        if not settings.OPENAI_API_KEY:
            return ("Erro: Chave da API OpenAI não configurada. "
                    "Por favor, contate o administrador.")

        openai.api_key = settings.OPENAI_API_KEY

        # Define as funções disponíveis para o modelo
        functions = [
            {
                "name": "get_student_info",
                "description": "Busca informações detalhadas sobre um aluno pelo nome",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "student_name": {
                            "type": "string",
                            "description": "Nome do aluno a ser buscado",
                        },
                    },
                    "required": ["student_name"],
                },
            },
            {
                "name": "get_student_photo",
                "description": "Busca a foto de um aluno pelo nome",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "student_name": {
                            "type": "string",
                            "description": "Nome do aluno cuja foto será buscada",
                        },
                    },
                    "required": ["student_name"],
                },
            },
            {
                "name": "get_students_by_filter",
                "description": "Busca uma lista de alunos com base em critérios",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter_type": {
                            "type": "string",
                            "description": "Tipo de filtro (ano, serie, turno, nivel, turma)",
                            "enum": ["ano", "serie", "turno", "nivel", "turma"],
                        },
                        "filter_value": {
                            "type": "string",
                            "description": "Valor do filtro (ex: '6', 'M')",
                        },
                    },
                    "required": ["filter_type", "filter_value"],
                },
            },
        ]

        # Prompt do sistema
        system_prompt = """
        Você é um assistente escolar amigável e prestativo da Escola Manager,
        com acesso aos dados dos alunos.
        Regras importantes:
        1. Sempre mantenha um tom amigável, acolhedor e profissional.
        2. Comece suas respostas com uma saudação como "Olá!" ou "Oi!".
        3. Use a função get_student_info para informações de um aluno específico.
        4. Use a função get_student_photo para a foto de um aluno.
        5. Use a função get_students_by_filter para listas de alunos por filtros.
        6. Inclua as informações solicitadas na resposta quando receber dados.
        7. Use os dados recebidos das funções na resposta, sem buscar novamente.
        8. Termine com: "Estou à disposição para mais perguntas!"
        9. Use formatação simples (ex: "Nome: valor"), sem asteriscos (**).
        10. Não inclua data e hora atuais nas respostas.
        """

        # Verifica se a mensagem solicita informações de aluno ou lista
        aluno_keywords = [
            "aluno", "estudante", "nota", "notas", "informações", "dados",
            "foto", "telefone", "endereço", "responsável", "responsavel",
            "data de nascimento", "série", "serie", "turma", "ano", "turno",
            "lista", "quais", "quantos", "todos", "sexto", "sétimo", "setimo",
            "oitavo", "nono", "manhã", "manha", "tarde",
        ]
        is_student_query = any(keyword in user_message.lower()
                               for keyword in aluno_keywords)

        # Chamada à API com function calling
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                functions=functions if is_student_query else None,
                function_call="auto" if is_student_query else None,
                temperature=0.7,
                max_tokens=500,
                top_p=0.9,
            )
        except Exception as api_error:
            print(f"Erro na chamada da API OpenAI, tentando alternativa: {api_error}")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                functions=functions if is_student_query else None,
                function_call="auto" if is_student_query else None,
                temperature=0.7,
                max_tokens=500,
                top_p=0.9,
            )

        # Processa a resposta
        message = response.choices[0].message

        # Verifica se o modelo chamou uma função
        if message.get("function_call"):
            function_name = message["function_call"]["name"]
            function_args = json.loads(message["function_call"]["arguments"])

            if function_name == "get_student_info":
                student_name = function_args.get("student_name", "")
                if not student_name:
                    return ("Olá! Forneça o nome do aluno para buscar. "
                            "Estou à disposição para mais perguntas!")

                student_name = student_name.strip().lower()
                student_info = get_student_info(student_name)

                if not student_info:
                    return (f"Olá! Não encontrei informações para '{student_name}'. "
                            "Verifique o nome ou tente outro. "
                            "Estou à disposição para mais perguntas!")

                # Segunda chamada à API com os dados do aluno
                try:
                    second_response = openai.ChatCompletion.create(
                        model="gpt-4o-mini-2024-07-18",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                            {"role": "function", "name": function_name,
                             "content": json.dumps(student_info)},
                        ],
                        temperature=0.7,
                        max_tokens=500,
                        top_p=0.9,
                    )
                except Exception as api_error:
                    print(f"Erro na segunda chamada, tentando alternativa: {api_error}")
                    second_response = openai.ChatCompletion.create(
                        model="gpt-4o-mini-2024-07-18",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                            {"role": "function", "name": function_name,
                             "content": json.dumps(student_info)},
                        ],
                        temperature=0.7,
                        max_tokens=500,
                        top_p=0.9,
                    )

                response_content = second_response.choices[0].message["content"]
                return remove_datetime_references(response_content)

            elif function_name == "get_student_photo":
                student_name = function_args.get("student_name", "")
                if not student_name:
                    return ("Olá! Forneça o nome do aluno para a foto. "
                            "Estou à disposição para mais perguntas!")

                student_name = student_name.strip().lower()
                student_info = get_student_info(student_name)

                if not student_info or not student_info.get("foto_url"):
                    return (f"Olá! Não encontrei a foto de '{student_name}'. "
                            "Verifique o nome ou a disponibilidade. "
                            "Estou à disposição para mais perguntas!")

                return [
                    f"Olá! Aqui está a foto de {student_info['nome']}. Estou à disposição para mais perguntas!",
                    {
                        "type": "image",
                        "url": student_info['foto_url']
                    }
]

            elif function_name == "get_students_by_filter":
                filter_type = function_args.get("filter_type", "")
                filter_value = function_args.get("filter_value", "")

                if not filter_type or not filter_value:
                    return ("Olá! Forneça o tipo de filtro e o valor. "
                            "Estou à disposição para mais perguntas!")

                print(f"Buscando alunos com filtro: {filter_type}={filter_value}")
                students_list = get_students_by_filter(filter_type, filter_value)

                if students_list:
                    print(f"Encontrados {len(students_list)} alunos")
                else:
                    print(f"Nenhum aluno encontrado com o filtro")

                if not students_list:
                    return (f"Olá! Não encontrei alunos para '{filter_type}={filter_value}'. "
                            "Verifique os critérios ou tente outros filtros. "
                            "Estou à disposição para mais perguntas!")

                # Segunda chamada à API com a lista de alunos
                try:
                    specific_instruction = """
                    IMPORTANTE:
                    1. Use formatação simples (ex: "Nome: valor"), sem asteriscos (**).
                    2. Não inclua data e hora atuais.
                    3. Apresente a lista numerada e organizada.
                    """
                    second_response = openai.ChatCompletion.create(
                        model="gpt-4o-mini-2024-07-18",
                        messages=[
                            {"role": "system",
                             "content": system_prompt + specific_instruction},
                            {"role": "user", "content": user_message},
                            {"role": "function", "name": function_name,
                             "content": json.dumps(students_list)},
                        ],
                        temperature=0.7,
                        max_tokens=500,
                        top_p=0.9,
                    )
                except Exception as api_error:
                    print(f"Erro na segunda chamada, tentando alternativa: {api_error}")
                    second_response = openai.ChatCompletion.create(
                        model="gpt-4o-mini-2024-07-18",
                        messages=[
                            {"role": "system",
                             "content": system_prompt + specific_instruction},
                            {"role": "user", "content": user_message},
                            {"role": "function", "name": function_name,
                             "content": json.dumps(students_list)},
                        ],
                        temperature=0.7,
                        max_tokens=500,
                        top_p=0.9,
                    )

                response_content = second_response.choices[0].message["content"]
                response_content = remove_datetime_references(response_content)
                response_content = response_content.replace("**", "")

                # Garante que a lista esteja presente na resposta
                if "1." not in response_content and "1:" not in response_content and students_list:
                    filter_display = {
                        "ano": "ano",
                        "serie": "série",
                        "turno": "turno",
                        "nivel": "nível",
                        "turma": "turma",
                    }.get(filter_type, filter_type)

                    filter_value_display = filter_value
                    if filter_type == "ano":
                        if filter_value in ["6", "sexto"]:
                            filter_value_display = "6º ano"
                        elif filter_value in ["7", "sétimo", "setimo"]:
                            filter_value_display = "7º ano"
                        elif filter_value in ["8", "oitavo"]:
                            filter_value_display = "8º ano"
                        elif filter_value in ["9", "nono"]:
                            filter_value_display = "9º ano"
                    elif filter_type == "turno":
                        if filter_value in ["m", "manhã", "manha"]:
                            filter_value_display = "manhã"
                        elif filter_value in ["t", "tarde"]:
                            filter_value_display = "tarde"

                    students_text = "\n".join(
                        f"{i+1}. {student['nome']} - {student['ano']} ({student['turno']})"
                        for i, student in enumerate(students_list)
                    )
                    response_content = (f"Olá! Encontrei {len(students_list)} alunos "
                                        f"no {filter_display} {filter_value_display}:\n\n"
                                        f"{students_text}\n\n"
                                        "Estou à disposição para mais perguntas!")

                return response_content

        # Resposta direta, sem chamada de função
        response_content = message["content"]
        return remove_datetime_references(response_content)

    except Exception as e:
        print(f"Erro na chamada da API OpenAI: {e}")
        return ("Desculpe, ocorreu um erro ao processar sua solicitação. "
                "Tente novamente. Estou à disposição para mais perguntas!")


def remove_datetime_references(text: str) -> str:
    """
    Remove referências a data e hora do texto.
    """
    patterns = [
        r"Data e hora atuais: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\.",
        r"Data e hora: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\.",
        r"A data e hora atuais são: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}.*",
        r"A data e hora atuais são: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",
        r"\(horário de Belém, Pará - GMT-3\)",
        r"Data e hora atuais: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",
        r"Data e hora: \d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",
    ]

    result = text
    for pattern in patterns:
        result = re.sub(pattern, "", result)

    # Remove linhas vazias extras
    result = re.sub(r"\n\s*\n", "\n\n", result)

    # Remove espaços em branco no final
    return result.strip()


def get_students_by_filter(filter_type: str, filter_value: str) -> List[Dict]:
    """
    Retorna uma lista de alunos com base em critérios de filtro.

    Args:
        filter_type: Tipo de filtro a aplicar (ano, serie, turno, nivel, turma)
        filter_value: Valor do filtro (ex: '6' para sexto ano, 'M' para manhã)

    Returns:
        Lista de dicionários com informações básicas dos alunos
    """
    try:
        students_queryset = Aluno.objects.all()

        # Normaliza os parâmetros
        filter_type = filter_type.lower().strip()
        filter_value = filter_value.lower().strip()

        # Aplica filtros com base no tipo
        if filter_type == "ano":
            if "6" in filter_value or "sexto" in filter_value:
                students_queryset = students_queryset.filter(ano="6")
            elif "7" in filter_value or "sétimo" in filter_value or "setimo" in filter_value:
                students_queryset = students_queryset.filter(ano="7")
            elif "8" in filter_value or "oitavo" in filter_value:
                students_queryset = students_queryset.filter(ano="8")
            elif "9" in filter_value or "nono" in filter_value:
                students_queryset = students_queryset.filter(Q(ano="901") | Q(ano="902"))
            elif "3" in filter_value or "terceiro" in filter_value:
                students_queryset = students_queryset.filter(ano="3")
            elif "4" in filter_value or "quarto" in filter_value:
                students_queryset = students_queryset.filter(ano="4")
            elif "5" in filter_value or "quinto" in filter_value:
                students_queryset = students_queryset.filter(ano="5")

        elif filter_type == "turno":
            if "manhã" in filter_value or "manha" in filter_value or "m" in filter_value:
                students_queryset = students_queryset.filter(turno="M")
            elif "tarde" in filter_value or "t" in filter_value:
                students_queryset = students_queryset.filter(turno="T")

        elif filter_type == "nivel":
            if "fundamental i" in filter_value or "iniciais" in filter_value or "efi" in filter_value:
                students_queryset = students_queryset.filter(nivel="EFI")
            elif "fundamental ii" in filter_value or "finais" in filter_value or "eff" in filter_value:
                students_queryset = students_queryset.filter(nivel="EFF")

        elif filter_type == "turma":
            if "901" in filter_value:
                students_queryset = students_queryset.filter(ano="901")
            elif "902" in filter_value:
                students_queryset = students_queryset.filter(ano="902")

        # Ordena os resultados
        students_queryset = students_queryset.order_by("nome")

        if not students_queryset.exists():
            return []

        # Converte para lista de dicionários
        students_list = []
        for student in students_queryset:
            students_list.append({
                "nome": student.nome,
                "matricula": student.matricula,
                "ano": student.get_ano_display(),
                "turno": student.get_turno_display(),
                "nivel": student.get_nivel_display(),
            })

        return students_list

    except Exception as e:
        print(f"Erro ao buscar lista de alunos por filtro: {e}")
        return []