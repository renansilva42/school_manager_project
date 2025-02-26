# apps/chatbot/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.shortcuts import render
from apps.alunos.models import Aluno, Nota
from apps.chatbot.utils import get_openai_response, get_student_info, get_student_grades, analyze_student_performance, compare_students
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
                        # Corrigido: ambos os parâmetros são obrigatórios para strict mode
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
                        # Corrigido para consistência
                        "required": ["student_id", "name"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_student_performance",
                    "description": "Analisa o desempenho de um aluno com base em suas notas",
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
                        "required": ["student_id", "name"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_students",
                    "description": "Compara o desempenho de dois ou mais alunos",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_names": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Lista de nomes de alunos para comparação"
                            },
                            "student_ids": {
                                "type": "array",
                                "items": {
                                    "type": "integer"
                                },
                                "description": "Lista de IDs de alunos para comparação"
                            }
                        },
                        "required": ["student_names", "student_ids"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        ]
        
        # Mensagens para o modelo
        messages = [
            {"role": "system", "content": "Você é um assistente virtual para uma escola. Você pode ajudar a buscar todas as informações de qualquer aluno cadastrado, incluindo dados pessoais, notas, fotos e análises de desempenho. Você também pode comparar alunos quando solicitado. Quando o usuário perguntar sobre um aluno, use a função get_student_info para buscar informações. Se o usuário não fornecer um ID, passe null para student_id. Se o usuário não fornecer um nome, passe null para name. Pelo menos um dos dois deve ser fornecido."},
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
                    # Garantir que os argumentos sejam tratados corretamente
                    student_id = function_args.get("student_id")
                    name = function_args.get("name")
                    # Se ambos forem None, definir um valor padrão para evitar erros
                    if student_id is None and (name is None or name == ""):
                        function_response = {"error": "É necessário fornecer o ID ou o nome do aluno"}
                    else:
                        function_response = get_student_info(student_id=student_id, name=name)
                elif function_name == "get_student_grades":
                    student_id = function_args.get("student_id")
                    name = function_args.get("name")
                    if student_id is None and (name is None or name == ""):
                        function_response = {"error": "É necessário fornecer o ID ou o nome do aluno"}
                    else:
                        function_response = get_student_grades(student_id=student_id, name=name)
                elif function_name == "analyze_student_performance":
                    student_id = function_args.get("student_id")
                    name = function_args.get("name")
                    if student_id is None and (name is None or name == ""):
                        function_response = {"error": "É necessário fornecer o ID ou o nome do aluno"}
                    else:
                        function_response = analyze_student_performance(student_id=student_id, name=name)
                elif function_name == "compare_students":
                    student_names = function_args.get("student_names", [])
                    student_ids = function_args.get("student_ids", [])
                    if not student_names and not student_ids:
                        function_response = {"error": "É necessário fornecer pelo menos um nome ou ID de aluno"}
                    else:
                        function_response = compare_students(student_names=student_names, student_ids=student_ids)
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