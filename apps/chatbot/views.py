from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.shortcuts import render
from apps.alunos.models import Aluno, Nota
from apps.chatbot.utils import get_openai_response, get_student_info, get_student_grades
import json

@login_required
def chatbot(request):
    return render(request, 'chatbot/chatbot.html')

@login_required
def chatbot_response(request):
    if request.method == 'POST':
        message = request.POST.get('message', '')
        
        # Definir as ferramentas (funções) que o modelo pode chamar
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
                        },
                        # Change this line - at least one parameter must be provided
                        "required": ["student_id", "name"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_student_grades",
                    "description": "Busca as notas de um aluno pelo nome ou ID",
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
                        },
                        # Change this line too for consistency
                        "required": ["student_id", "name"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        ]
        
        # Mensagens para o modelo
        messages = [
            {"role": "system", "content": "Você é um assistente virtual para uma escola. Você pode ajudar a buscar informações sobre alunos e suas notas."},
            {"role": "user", "content": message}
        ]
        
        # Obter resposta do modelo
        response = get_openai_response(messages, tools)
        
        # Verificar se o modelo decidiu chamar uma função
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Adicionar a mensagem do modelo à conversa
            messages.append({"role": "assistant", "content": response.content, "tool_calls": response.tool_calls})
            
            # Processar cada chamada de função
            for tool_call in response.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Executar a função apropriada
                if function_name == "get_student_info":
                    function_response = get_student_info(**function_args)
                elif function_name == "get_student_grades":
                    function_response = get_student_grades(**function_args)
                else:
                    function_response = "Função não implementada."
                
                # Adicionar o resultado da função à conversa
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(function_response)
                })
            
            # Obter resposta final do modelo com os resultados das funções
            final_response = get_openai_response(messages, tools)
            return JsonResponse({"response": final_response.content})
        else:
            # Se não houve chamada de função, retornar a resposta direta
            return JsonResponse({"response": response.content})
    
    return JsonResponse({"error": "Método não permitido"}, status=405)