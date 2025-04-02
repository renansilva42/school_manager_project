# apps/chatbot/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from apps.chatbot.utils import get_openai_response, compare_students
from apps.chatbot.database_connector import ChatbotDatabaseConnector
import json
import logging

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
                    "description": "Busca informações detalhadas sobre um aluno pelo nome ou ID",
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
                    return JsonResponse({"response": json.dumps(result, ensure_ascii=False)})
            
            # If no function call, return the direct response
            return JsonResponse({"response": response.content})

        except Exception as e:
            return JsonResponse({"response": f"Ocorreu um erro: {str(e)}"})

    return JsonResponse({"response": "Método não permitido"}, status=405)
