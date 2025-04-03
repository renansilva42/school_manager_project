import logging
import json
import traceback
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .utils import get_openai_response, format_dict_response
from .database_connector import ChatbotDatabaseConnector

# Configurar o logger
logger = logging.getLogger(__name__)

@login_required
def chatbot(request):
    return render(request, 'chatbot/chatbot.html')

@login_required
def chatbot_response(request):
    if request.method == 'POST':
        message = request.POST.get('message', '')
        
        # Adicionar registro de log para a mensagem recebida
        logger.info(f"Mensagem recebida: '{message}'")
        
        # Define all available tools/functions
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_student_info",
                    "description": "Busca informações detalhadas sobre um aluno pelo ID, nome ou matrícula",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {
                                "type": ["integer", "null"],
                                "description": "ID do aluno no sistema"
                            },
                            "name": {
                                "type": ["string", "null"],
                                "description": "Nome do aluno para busca"
                            },
                            "matricula": {
                                "type": ["integer", "null"],
                                "description": "Número de matrícula do aluno"
                            },
                            "fields": {
                                "type": ["array", "null"],
                                "description": "Lista de campos específicos a serem retornados. Se não for fornecido, retorna todos os campos. Pode incluir: 'dados_pessoais', 'contato', 'endereco', 'dados_academicos', 'responsaveis', ou campos específicos como 'nome', 'email', 'telefone', etc.",
                                "items": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_student_grades",
                    "description": "Busca as notas de um aluno",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {
                                "type": ["integer", "null"],
                                "description": "ID do aluno no sistema"
                            },
                            "name": {
                                "type": ["string", "null"],
                                "description": "Nome do aluno para busca"
                            },
                            "matricula": {
                                "type": ["integer", "null"],
                                "description": "Número de matrícula do aluno"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_student_performance",
                    "description": "Analisa o desempenho acadêmico de um aluno",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {
                                "type": ["integer", "null"],
                                "description": "ID do aluno no sistema"
                            },
                            "name": {
                                "type": ["string", "null"],
                                "description": "Nome do aluno para busca"
                            },
                            "matricula": {
                                "type": ["integer", "null"],
                                "description": "Número de matrícula do aluno"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cross_reference_data",
                    "description": "Realiza consultas complexas que exigem cruzamento de dados de alunos",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "description": "Tipo de consulta a ser realizada",
                                "enum": ["alunos_por_turma", "comparacao_desempenho", "ranking_alunos", "estatisticas_turma"]
                            },
                            "params": {
                                "type": "object",
                                "description": "Parâmetros adicionais para a consulta",
                                "properties": {
                                    "turma": {
                                        "type": ["string", "null"],
                                        "description": "Turma para filtrar os resultados"
                                    },
                                    "aluno1_id": {
                                        "type": ["integer", "null"],
                                        "description": "ID do primeiro aluno para comparação"
                                    },
                                    "aluno2_id": {
                                        "type": ["integer", "null"],
                                        "description": "ID do segundo aluno para comparação"
                                    },
                                    "limite": {
                                        "type": ["integer", "null"],
                                        "description": "Limite de resultados a serem retornados"
                                    }
                                }
                            }
                        },
                        "required": ["query_type"]
                    }
                }
            }
        ]

        # Prepare messages for the API
        messages = [
            {"role": "system", "content": "Você é um assistente virtual do sistema School Manager, especializado em fornecer informações sobre alunos. Quando perguntarem sobre informações de um aluno, você deve usar a função get_student_info para obter as informações solicitadas. Utilize o parâmetro name com o nome do aluno para fazer a consulta. IMPORTANTE: Quando o usuário pedir informações específicas sobre um aluno (como apenas o telefone, endereço, ou responsáveis), você DEVE usar o parâmetro fields para especificar exatamente quais campos deseja obter, evitando retornar informações desnecessárias. Por exemplo, se o usuário perguntar apenas pelo telefone de um aluno, use fields=['telefone'] ou fields=['contato']. Se perguntar apenas pelo endereço, use fields=['endereco']. Quando o usuário fizer perguntas complexas que exigem cruzamento de dados entre alunos ou turmas, use a função cross_reference_data com o query_type apropriado."},
            {"role": "user", "content": message}
        ]

        try:
            # Verificar conexão com o banco de dados
            from django.db import connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    # Conexão OK
            except Exception as db_error:
                logger.error(f"Erro de conexão com o banco de dados: {str(db_error)}")
                return JsonResponse({"response": f"Não foi possível conectar ao banco de dados: {str(db_error)}"})
            
            # Não vamos mais tratar perguntas sobre responsáveis de forma especial
            # Todas as perguntas sobre alunos serão tratadas da mesma forma,
            # usando a API OpenAI para determinar a intenção e chamar a função apropriada
            
            # Determine if the message is asking about student information
            is_student_info_request = any(keyword in message.lower() for keyword in [
                "informações", "informacoes", "dados", "aluno", "estudante", 
                "matricula", "matrícula", "cadastro", "ficha", "registro"
            ])
            
            # Set tool_choice based on the message content
            tool_choice = {
                "type": "function",
                "function": {"name": "get_student_info"}
            } if is_student_info_request else "auto"
            
            # Get response from OpenAI
            logger.info("Enviando requisição para OpenAI")
            logger.info(f"Usando tool_choice: {tool_choice}")
            response = get_openai_response(messages=messages, tools=tools, tool_choice=tool_choice)
            logger.info(f"Resposta recebida da OpenAI: {str(response)}")
            
            # Check if the response includes a function call
            if hasattr(response, 'function_call') and response.function_call:
                function_name = response.function_call.name
                logger.info(f"Função a ser chamada via function_call: {function_name}")
                
                # Parse function arguments safely
                try:
                    function_args = json.loads(response.function_call.arguments)
                    logger.info(f"Argumentos da função via function_call: {function_args}")
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao decodificar argumentos JSON via function_call: {str(e)}, argumentos: {response.function_call.arguments}")
                    return JsonResponse({"response": "Erro ao processar argumentos da função."})
                
                # Initialize database connector
                db_connector = ChatbotDatabaseConnector()
                result = None
                
                try:
                    # Execute the appropriate function based on the name
                    if function_name == "get_student_info":
                        logger.info(f"Buscando informações do aluno via function_call com: {function_args}")
                        
                        # Validar os argumentos antes de chamar a função
                        if 'name' in function_args and isinstance(function_args['name'], str):
                            # Garantir que o nome não seja vazio
                            function_args['name'] = function_args['name'].strip()
                            if not function_args['name']:
                                return JsonResponse({"response": "O nome do aluno não pode estar vazio. Por favor, forneça um nome válido."})
                        
                        # Chamar a função e registrar o resultado completo
                        result = db_connector.get_student_info(**function_args)
                        logger.info(f"Resultado completo da função get_student_info via function_call: {result}")
                    elif function_name == "get_student_grades":
                        result = db_connector.get_student_grades(**function_args)
                        logger.info(f"Resultado da função get_student_grades via function_call: {result}")
                    elif function_name == "analyze_student_performance":
                        result = db_connector.analyze_student_performance(**function_args)
                        logger.info(f"Resultado da função analyze_student_performance via function_call: {result}")
                    elif function_name == "cross_reference_data":
                        logger.info(f"Realizando consulta complexa via function_call com: {function_args}")
                        result = db_connector.cross_reference_data(
                            query_type=function_args.get('query_type'),
                            params=function_args.get('params', {})
                        )
                        logger.info(f"Resultado da consulta complexa via function_call: {result}")
                    else:
                        logger.error(f"Função desconhecida solicitada via function_call: {function_name}")
                        return JsonResponse({"response": f"Não sei como executar a função {function_name}."})
                    
                    # Verificar se há erro no resultado
                    if "error" in result:
                        logger.error(f"Erro ao executar função via function_call: {result['error']}")
                        return JsonResponse({"response": f"Desculpe, encontrei um problema: {result['error']}"})
                    elif "message" in result and "alunos" in result:
                        # Handle multiple students found
                        alunos_list = [f"{aluno['nome']} (ID: {aluno['id']})" for aluno in result['alunos']]
                        return JsonResponse({
                            "response": f"{result['message']}\nAlunos encontrados:\n" + "\n".join(alunos_list)
                        })
                    
                    # Formatar a resposta usando a função format_dict_response
                    # Passar os campos solicitados, se houver
                    resposta_formatada = format_dict_response(result, fields=function_args.get('fields'))
                    logger.info(f"Resposta formatada completa via function_call: {resposta_formatada}")
                    
                    # Se for get_student_info e tiver uma foto, tratar a exibição da foto
                    if function_name == "get_student_info":
                        # Se tiver uma foto e não foi solicitado um campo específico que não inclui a foto,
                        # ou se a foto foi especificamente solicitada, adicionar ao final da resposta formatada
                        foto_solicitada = False
                        campos_especificos_solicitados = False
                        
                        # Verificar se foram solicitados campos específicos
                        if function_args.get('fields'):
                            campos_especificos_solicitados = True
                            # Verificar se a foto foi solicitada
                            foto_solicitada = 'foto_url' in function_args.get('fields') or 'dados_pessoais' in function_args.get('fields')
                        
                        # Adicionar a foto apenas se foi solicitada ou se não foram solicitados campos específicos
                        if (not campos_especificos_solicitados or foto_solicitada) and \
                           ("foto_url" in result or (isinstance(result, dict) and "dados_pessoais" in result and "foto_url" in result["dados_pessoais"])):
                            foto_url = result.get("foto_url") or result.get("dados_pessoais", {}).get("foto_url")
                            if foto_url:
                                resposta_formatada += f"\n\n![Foto do aluno]({foto_url})"
                    
                    # Verificar se a resposta formatada não está vazia
                    if not resposta_formatada.strip():
                        logger.error("Resposta formatada está vazia via function_call")
                        return JsonResponse({"response": "Erro interno: a resposta formatada está vazia."})
                    
                    # Enviar a resposta formatada para o cliente
                    logger.info(f"Enviando resposta formatada para o cliente via function_call: {resposta_formatada[:200]}...")
                    return JsonResponse({"response": resposta_formatada})
                except Exception as e:
                    logger.error(f"Erro ao processar function_call: {str(e)}")
                    return JsonResponse({"response": f"Erro ao processar sua solicitação: {str(e)}"})
                
            elif hasattr(response, 'tool_calls') and response.tool_calls:
                tool_call = response.tool_calls[0]
                function_name = tool_call.function.name
                logger.info(f"Função a ser chamada via tool_call: {function_name}")
                
                # Parse function arguments safely
                try:
                    function_args = json.loads(tool_call.function.arguments)
                    logger.info(f"Argumentos da função: {function_args}")
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao decodificar argumentos JSON: {str(e)}, argumentos: {tool_call.function.arguments}")
                    return JsonResponse({"response": "Erro ao processar argumentos da função."})
                
                # Initialize database connector
                db_connector = ChatbotDatabaseConnector()
                
                # Execute the appropriate function based on the name
                if function_name == "get_student_info":
                    logger.info(f"Buscando informações do aluno com: {function_args}")
                    
                    # Validar os argumentos antes de chamar a função
                    if 'name' in function_args and isinstance(function_args['name'], str):
                        # Garantir que o nome não seja vazio
                        function_args['name'] = function_args['name'].strip()
                        if not function_args['name']:
                            return JsonResponse({"response": "O nome do aluno não pode estar vazio. Por favor, forneça um nome válido."})
                    
                    # Chamar a função e registrar o resultado completo
                    result = db_connector.get_student_info(**function_args)
                    logger.info(f"Resultado completo da função get_student_info: {result}")
                    
                    # Verificar se o resultado é um dicionário válido com as informações do aluno
                    if isinstance(result, dict) and "dados_pessoais" in result:
                        logger.info("Resultado contém dados_pessoais, formatando resposta...")
                    else:
                        logger.warning(f"Resultado não contém dados_pessoais: {result}")
                elif function_name == "get_student_grades":
                    result = db_connector.get_student_grades(**function_args)
                elif function_name == "analyze_student_performance":
                    result = db_connector.analyze_student_performance(**function_args)
                elif function_name == "cross_reference_data":
                    logger.info(f"Realizando consulta complexa com: {function_args}")
                    result = db_connector.cross_reference_data(
                        query_type=function_args.get('query_type'),
                        params=function_args.get('params', {})
                    )
                else:
                    logger.error(f"Função desconhecida solicitada: {function_name}")
                    return JsonResponse({"response": f"Não sei como executar a função {function_name}."})
                
                logger.info(f"Resultado da função: {str(result)[:500]}...") # Limitar o tamanho do log
                
                # Format the response based on the result
                if "error" in result:
                    # Registrar o erro e retornar uma mensagem mais amigável
                    logger.error(f"Erro ao buscar dados: {result['error']}")
                    return JsonResponse({"response": f"Desculpe, encontrei um problema: {result['error']}"})
                elif "message" in result and "alunos" in result:
                    # Handle multiple students found
                    alunos_list = [f"{aluno['nome']} (ID: {aluno['id']})" for aluno in result['alunos']]
                    return JsonResponse({
                        "response": f"{result['message']}\nAlunos encontrados:\n" + "\n".join(alunos_list)
                    })
                else:
                    # Sempre usar a função format_dict_response para formatar os dados do aluno
                    # independentemente do tipo de pergunta
                    logger.info(f"Formatando dados do aluno com format_dict_response. Dados: {str(result)[:200]}...")
                    
                    # Garantir que estamos trabalhando com um dicionário válido
                    if not isinstance(result, dict):
                        logger.error(f"Resultado não é um dicionário: {type(result)}")
                        return JsonResponse({"response": "Erro interno: o resultado não é um dicionário válido."})
                    
                    # Verificar se o resultado contém as informações esperadas
                    if "dados_pessoais" not in result:
                        logger.warning(f"Resultado não contém dados_pessoais: {result}")
                        # Se não tiver dados_pessoais, mas tiver error, retornar a mensagem de erro
                        if "error" in result:
                            return JsonResponse({"response": f"Erro ao buscar informações: {result['error']}"})
                    
                    # Formatar a resposta usando a função format_dict_response
                    # Passar os campos solicitados, se houver
                    resposta_formatada = format_dict_response(result, fields=function_args.get('fields'))
                    logger.info(f"Resposta formatada completa: {resposta_formatada}")
                    
                    # Se tiver uma foto e não foi solicitado um campo específico que não inclui a foto,
                    # ou se a foto foi especificamente solicitada, adicionar ao final da resposta formatada
                    foto_solicitada = False
                    campos_especificos_solicitados = False
                    
                    # Verificar se foram solicitados campos específicos
                    if function_args.get('fields'):
                        campos_especificos_solicitados = True
                        # Verificar se a foto foi solicitada
                        foto_solicitada = 'foto_url' in function_args.get('fields') or 'dados_pessoais' in function_args.get('fields')
                    
                    # Adicionar a foto apenas se foi solicitada ou se não foram solicitados campos específicos
                    if (not campos_especificos_solicitados or foto_solicitada) and \
                       ("foto_url" in result or (isinstance(result, dict) and "dados_pessoais" in result and "foto_url" in result["dados_pessoais"])):
                        foto_url = result.get("foto_url") or result.get("dados_pessoais", {}).get("foto_url")
                        if foto_url:
                            resposta_formatada += f"\n\n![Foto do aluno]({foto_url})"
                    
                    # Verificar se a resposta formatada não está vazia
                    if not resposta_formatada.strip():
                        logger.error("Resposta formatada está vazia")
                        return JsonResponse({"response": "Erro interno: a resposta formatada está vazia."})
                    
                    # Enviar a resposta formatada para o cliente
                    logger.info(f"Enviando resposta formatada para o cliente: {resposta_formatada[:200]}...")
                    return JsonResponse({"response": resposta_formatada})
            elif hasattr(response, 'content') and response.content:
                # If no function call, return the direct response
                logger.info(f"Retornando resposta direta da OpenAI: {response.content}")
                return JsonResponse({"response": response.content})
            else:
                # Se não houve function call e não há conteúdo, responder com mensagem explicativa
                logger.warning("A resposta da OpenAI não contém content nem function_call")
                return JsonResponse({
                    "response": "Não consegui processar sua pergunta sobre o aluno. Por favor, tente reformular ou fornecer mais detalhes."
                })

        except Exception as e:
            # Registrar detalhes da exceção para depuração
            logger.error(f"Erro no chatbot_response: {str(e)}\n{traceback.format_exc()}")
            return JsonResponse({
                "response": f"Ocorreu um erro ao processar sua solicitação: {str(e)}\nPor favor, contate o administrador do sistema."
            })

    return JsonResponse({"response": "Método não permitido"}, status=405)

@login_required
def chatbot_diagnostics(request):
    """
    Página de diagnóstico para verificar a conexão com o banco de dados e configurações do chatbot
    """
    results = {
        "status": "OK",
        "database": "Não verificado",
        "openai": "Não verificado",
        "errors": []
    }
    
    # Verificar conexão com o banco de dados
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM alunos_aluno")
            count = cursor.fetchone()[0]
        results["database"] = f"Conectado. {count} alunos encontrados."
    except Exception as e:
        results["status"] = "ERROR"
        results["database"] = f"Erro: {str(e)}"
        results["errors"].append(f"Banco de dados: {str(e)}")

    # Verificar configurações do OpenAI
    try:
        openai_key = settings.OPENAI_API_KEY
        if openai_key:
            if len(openai_key) > 5:
                masked_key = openai_key[:5] + "*" * (len(openai_key) - 9) + openai_key[-4:]
                results["openai"] = f"Chave configurada: {masked_key}"
            else:
                results["status"] = "ERROR"
                results["openai"] = "Chave da API muito curta"
                results["errors"].append("Chave da OpenAI inválida")
        else:
            results["status"] = "ERROR"
            results["openai"] = "Chave da API não configurada"
            results["errors"].append("Chave da OpenAI não configurada")
    except Exception as e:
        results["status"] = "ERROR"
        results["openai"] = f"Erro: {str(e)}"
        results["errors"].append(f"OpenAI: {str(e)}")
    
    return render(request, 'chatbot/diagnostics.html', {'results': results})