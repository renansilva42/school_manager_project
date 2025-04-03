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
            }
        ]

        # Prepare messages for the API
        messages = [
            {"role": "system", "content": "Você é um assistente virtual do sistema School Manager, especializado em fornecer informações sobre alunos. Quando perguntarem sobre informações de um aluno ou sobre responsáveis de um aluno, você DEVE usar a função get_student_info para obter todas as informações do aluno. Utilize o parâmetro name com o nome do aluno para fazer a consulta. Sempre que o usuário pedir informações sobre um aluno, mesmo que não mencione especificamente 'responsáveis', você deve usar get_student_info para mostrar TODAS as informações disponíveis do aluno."},
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
            
            # Extrair nome do aluno em caso de pergunta sobre responsável
            if "responsável" in message.lower() or "responsavel" in message.lower():
                import re
                aluno_match = re.search(r'aluno\s+([A-Za-zÀ-ÖØ-öø-ÿ\s]+)(\?|$|\.|,)', message, re.IGNORECASE)
                if aluno_match:
                    try:
                        aluno_name = aluno_match.group(1).strip().upper()
                        logger.info(f"Nome do aluno extraído da mensagem: {aluno_name}")
                        
                        # Verificar se o nome do aluno é válido
                        if not aluno_name or len(aluno_name) < 2:
                            logger.warning(f"Nome do aluno muito curto ou vazio: '{aluno_name}'")
                            return JsonResponse({"response": "Não consegui identificar o nome do aluno na sua pergunta. Por favor, especifique o nome completo do aluno."})
                        
                        # Verificar o aluno diretamente antes de chamar a API
                        db_connector = ChatbotDatabaseConnector()
                        result = db_connector.get_student_info(name=aluno_name)
                        
                        if "error" in result:
                            logger.warning(f"Aluno não encontrado na verificação prévia: {aluno_name}")
                            return JsonResponse({"response": f"Não encontrei um aluno com o nome {aluno_name} no sistema. Por favor, verifique se o nome está correto."})
                        
                        # Se encontramos múltiplos alunos, informar ao usuário
                        if "message" in result and "alunos" in result:
                            alunos_list = [f"{aluno['nome']} (ID: {aluno['id']})" for aluno in result['alunos']]
                            response_text = f"{result['message']}\nEncontrei os seguintes alunos:\n" + "\n".join(alunos_list) + "\n\nPor favor, especifique de qual aluno você precisa informações."
                            return JsonResponse({"response": response_text})
                        
                        # Se chegamos aqui, temos um único aluno - vamos formatar a resposta sobre os responsáveis
                        if "responsaveis" in result and result["responsaveis"]:
                            nome_aluno = result.get("dados_pessoais", {}).get("nome", result.get("nome", aluno_name))
                            resp_text = f"Os responsáveis pelo aluno {nome_aluno} são:\n\n"
                            
                            for idx, resp in enumerate(result["responsaveis"], 1):
                                resp_text += f"**Responsável {idx}**\n"
                                for k, v in resp.items():
                                    if v:
                                        resp_text += f"- {k.replace('_', ' ').title()}: {v}\n"
                                resp_text += "\n"
                            
                            return JsonResponse({"response": resp_text})
                        else:
                            return JsonResponse({"response": f"O aluno {aluno_name} está cadastrado no sistema, mas não possui responsáveis registrados."})
                    except Exception as e:
                        logger.error(f"Erro ao extrair ou processar nome do aluno: {str(e)}")
                        return JsonResponse({"response": "Ocorreu um erro ao processar o nome do aluno. Por favor, tente novamente com o nome completo."})
                else:
                    logger.warning("Não foi possível extrair o nome do aluno da mensagem")
                    return JsonResponse({"response": "Não consegui identificar o nome do aluno na sua pergunta. Por favor, especifique o nome completo do aluno."})
            
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
                else:
                    logger.error(f"Função desconhecida solicitada via function_call: {function_name}")
                    return JsonResponse({"response": f"Não sei como executar a função {function_name}."})
                
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
                    resposta_formatada = format_dict_response(result)
                    logger.info(f"Resposta formatada: {resposta_formatada[:200]}...")
                    
                    # Se tiver uma foto, adicionar ao final da resposta formatada
                    if "foto_url" in result or (isinstance(result, dict) and "dados_pessoais" in result and "foto_url" in result["dados_pessoais"]):
                        foto_url = result.get("foto_url") or result.get("dados_pessoais", {}).get("foto_url")
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