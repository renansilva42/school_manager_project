# apps/chatbot/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from apps.chatbot.utils import get_openai_response, compare_students
from apps.chatbot.database_connector import ChatbotDatabaseConnector
import json
import logging

def format_dict_response(data, indent=0):
    """Formata um dicionário de forma recursiva para exibição amigável"""
    
    if not isinstance(data, dict):
        return str(data)
    
    result = ""
    prefix = "  " * indent
    
    # Tratamento especial para tipos específicos de resposta
    if "aluno" in data and "notas" in data:
        # Formatação para notas de alunos
        result += f"**Informações do Aluno {data['aluno'].get('nome', '')}**\n\n"
        
        if "message" in data:
            result += f"{data['message']}\n\n"
            return result
            
        result += "<table>\n<tr><th>Disciplina</th><th>Valor</th><th>Data</th></tr>\n"
        
        for nota in data["notas"]:
            if isinstance(nota, dict):
                disciplina = nota.get("disciplina", "N/A")
                valor = nota.get("valor", "N/A")
                data_nota = nota.get("data", "N/A")
                result += f"<tr><td>{disciplina}</td><td>{valor}</td><td>{data_nota}</td></tr>\n"
            
        result += "</table>\n\n"
        
        if "media_geral" in data:
            result += f"**Média Geral:** {data['media_geral']}"
            
        return result
    
    # Para análise de desempenho
    if "media_geral" in data and "situacao_geral" in data and "disciplinas" in data:
        result += f"**Análise de Desempenho de {data.get('aluno', {}).get('nome', '')}**\n\n"
        result += f"Média Geral: {data['media_geral']}\n"
        result += f"Situação: {data['situacao_geral']}\n\n"
        
        result += "<table>\n<tr><th>Disciplina</th><th>Média</th><th>Situação</th></tr>\n"
        
        for disc in data["disciplinas"]:
            result += f"<tr><td>{disc['disciplina']}</td><td>{disc['media']}</td><td>{disc['situacao']}</td></tr>\n"
            
        result += "</table>\n"
        return result
    
    # Formato geral para outros tipos de dicionários
    for key, value in data.items():
        if key in ["error", "message"]:
            result += f"{value}\n"
        elif isinstance(value, dict):
            result += f"{prefix}**{key.replace('_', ' ').title()}**:\n"
            result += format_dict_response(value, indent + 1)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            result += f"{prefix}**{key.replace('_', ' ').title()}**:\n"
            for item in value:
                result += f"{prefix}  - "
                if "nome" in item:
                    result += f"{item['nome']}"
                    if "id" in item:
                        result += f" (ID: {item['id']})"
                    result += "\n"
                else:
                    result += format_dict_response(item, indent + 2)
        else:
            result += f"{prefix}**{key.replace('_', ' ').title()}**: {value}\n"
    
    return result

# Configurar o logger
logger = logging.getLogger(__name__)

@login_required
def chatbot(request):
    return render(request, 'chatbot/chatbot.html')

@login_required
def chatbot_response(request):
    if request.method == 'POST':
        message = request.POST.get('message', '')
        
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
                            }
                        }
                    }
                }
            }
        ]

        # Prepare messages for the API
        messages = [
            {"role": "system", "content": "Você é um assistente virtual do sistema School Manager, especializado em fornecer informações sobre alunos."},
            {"role": "user", "content": message}
        ]

        try:
            # Get response from OpenAI
            response = get_openai_response(messages=messages, tools=tools)
            
            # Check if the response includes a function call
            if hasattr(response, 'function_call'):
                function_name = response.function_call.name
                function_args = json.loads(response.function_call.arguments)
                
                # Initialize database connector
                db_connector = ChatbotDatabaseConnector()
                
                # Execute the appropriate function based on the name
                if function_name == "get_student_info":
                    result = db_connector.get_student_info(**function_args)
                elif function_name == "get_student_grades":
                    result = db_connector.get_student_grades(**function_args)
                elif function_name == "analyze_student_performance":
                    result = db_connector.analyze_student_performance(**function_args)
                
                # Format the response based on the result
                if "error" in result:
                    return JsonResponse({"response": f"Erro: {result['error']}"})
                elif "message" in result and "alunos" in result:
                    # Handle multiple students found
                    alunos_list = [f"{aluno['nome']} (ID: {aluno['id']})" for aluno in result['alunos']]
                    return JsonResponse({
                        "response": f"{result['message']}\nAlunos encontrados:\n" + "\n".join(alunos_list)
                    })
                else:
                    # Format successful response
                    # Formatar a resposta de uma maneira amigável para o usuário
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
                            for categoria in ["contato", "endereco", "dados_academicos"]:
                                if categoria in result:
                                    info_texto += f"\n**{categoria.replace('_', ' ').title()}**\n"
                                    for k, v in result[categoria].items():
                                        if v:
                                            info_texto += f"- {k.replace('_', ' ').title()}: {v}\n"
                        else:
                            # Formatação para o formato antigo de resposta
                            for k, v in result.items():
                                if k not in ["foto_url", "id"] and v:
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
            
            # If no function call, return the direct response
            return JsonResponse({"response": response.content})

        except Exception as e:
            return JsonResponse({"response": f"Ocorreu um erro: {str(e)}"})

    return JsonResponse({"response": "Método não permitido"}, status=405)
