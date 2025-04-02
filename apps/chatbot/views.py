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
            {"role": "system", "content": "Você é um assistente virtual do sistema School Manager, especializado em fornecer informações sobre alunos. Quando perguntarem sobre responsáveis de um aluno, você DEVE usar a função get_student_info para obter todas as informações do aluno, incluindo seus responsáveis cadastrados. Utilize o parâmetro name com o nome do aluno para fazer a consulta."},
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
                    aluno_name = aluno_match.group(1).strip().upper()
                    logger.info(f"Nome do aluno extraído da mensagem: {aluno_name}")
                    
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
            
            # Get response from OpenAI
            logger.info("Enviando requisição para OpenAI")
            response = get_openai_response(messages=messages, tools=tools)
            logger.info(f"Resposta recebida da OpenAI: {str(response)}")
            
            # Check if the response includes a function call
            if hasattr(response, 'function_call') and response.function_call:
                function_name = response.function_call.name
                logger.info(f"Função a ser chamada: {function_name}")
                
                # Parse function arguments safely
                try:
                    function_args = json.loads(response.function_call.arguments)
                    logger.info(f"Argumentos da função: {function_args}")
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao decodificar argumentos JSON: {str(e)}, argumentos: {response.function_call.arguments}")
                    return JsonResponse({"response": "Erro ao processar argumentos da função."})
                
                # Initialize database connector
                db_connector = ChatbotDatabaseConnector()
                
                # Execute the appropriate function based on the name
                if function_name == "get_student_info":
                    logger.info(f"Buscando informações do aluno com: {function_args}")
                    result = db_connector.get_student_info(**function_args)
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
                    # Format successful response
                    # Verificar se estamos buscando por responsáveis
                    if "responsável" in message.lower() or "responsavel" in message.lower():
                        # Formatação específica para perguntas sobre responsáveis
                        if "responsaveis" in result and result["responsaveis"]:
                            nome_aluno = result.get("dados_pessoais", {}).get("nome", "")
                            resp_text = f"Os responsáveis pelo aluno {nome_aluno} são:\n\n"
                            
                            for idx, resp in enumerate(result["responsaveis"], 1):
                                resp_text += f"**Responsável {idx}**\n"
                                for k, v in resp.items():
                                    if v:
                                        resp_text += f"- {k.replace('_', ' ').title()}: {v}\n"
                                resp_text += "\n"
                            
                            return JsonResponse({"response": resp_text})
                        else:
                            nome_aluno = result.get("dados_pessoais", {}).get("nome", "")
                            return JsonResponse({"response": f"O aluno {nome_aluno} está cadastrado no sistema, mas não possui responsáveis registrados."})
                    
                    # Processamento padrão para outros tipos de informações
                    if "foto_url" in result or (isinstance(result, dict) and "dados_pessoais" in result and "foto_url" in result["dados_pessoais"]):
                        # Se tiver uma foto, formatamos especificamente para usar o componente de imagem
                        foto_url = result.get("foto_url") or result.get("dados_pessoais", {}).get("foto_url")
                        nome = result.get("nome") or result.get("dados_pessoais", {}).get("nome")
                        
                        # Montar texto descritivo baseado nos dados
                        info_texto = f"Aqui estão as informações do aluno {nome}:\n\n"
                        
                        # Formatação em texto legível dos dados do aluno
                        if "dados_pessoais" in result:
                            # Formatação para o novo formato de resposta
                            info_texto += "**Dados Pessoais**\n"
                            for k, v in result["dados_pessoais"].items():
                                if k != "foto_url" and v:
                                    info_texto += f"- {k.replace('_', ' ').title()}: {v}\n"
                            
                            # Adicionar outras categorias
                            for categoria in ["contato", "endereco", "dados_academicos", "responsaveis"]:
                                if categoria in result and result[categoria]:
                                    info_texto += f"\n**{categoria.replace('_', ' ').title()}**\n"
                                    if categoria == "responsaveis" and isinstance(result[categoria], list):
                                        for idx, resp in enumerate(result[categoria], 1):
                                            info_texto += f"- Responsável {idx}: {resp.get('nome', 'N/A')}"
                                            if resp.get('telefone'):
                                                info_texto += f" (Tel: {resp.get('telefone')})"
                                            info_texto += "\n"
                                    else:
                                        for k, v in result[categoria].items():
                                            if v:
                                                info_texto += f"- {k.replace('_', ' ').title()}: {v}\n"
                        else:
                            # Formatação para o formato antigo de resposta
                            for k, v in result.items():
                                if k not in ["foto_url", "id"] and v:
                                    if k == "responsaveis" and isinstance(v, list):
                                        info_texto += f"- Responsáveis:\n"
                                        for resp in v:
                                            info_texto += f"  - {resp.get('nome', 'N/A')}"
                                            if resp.get('telefone'):
                                                info_texto += f" (Tel: {resp.get('telefone')})"
                                            info_texto += "\n"
                                    else:
                                        info_texto += f"- {k.replace('_', ' ').title()}: {v}\n"
                        
                        # Usar marcação markdown para a imagem
                        resposta_markdown = f"{info_texto}\n\n![Foto do aluno]({foto_url})"
                        return JsonResponse({"response": resposta_markdown})
                    else:
                        # Para outros tipos de respostas, formatar como texto legível
                        if isinstance(result, dict):
                            # Converter o resultado em texto formatado
                            resposta_formatada = format_dict_response(result)
                            return JsonResponse({"response": resposta_formatada})
                        else:
                            # Caso seja outro tipo de dados
                            return JsonResponse({"response": str(result)})
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