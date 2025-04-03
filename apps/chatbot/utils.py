# apps/chatbot/utils.py
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import openai
from django.conf import settings
from django.db.models import Avg, Max, Min
from apps.alunos.models import Aluno, Nota
from decimal import Decimal
from django.urls import reverse
import logging

# Configurar o logger
logger = logging.getLogger(__name__)

# Verifica a versão do openai para definir a forma correta de uso
try:
    openai_version = openai.__version__
    use_legacy_api = openai_version.startswith("0.")
except AttributeError:
    use_legacy_api = True

def get_openai_response(messages, tools=None, tool_choice="auto"):
    """
    Obtém resposta da API OpenAI com suporte a function calling e tool calling.
    """
    try:
        logger.info(f"Chamando OpenAI API com tool_choice: {tool_choice}")
        logger.info(f"Mensagens: {messages}")
        logger.info(f"Tools: {tools}")
        
        if use_legacy_api:
            openai.api_key = settings.OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini-2024-07-18",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice
            )
        else:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice
            )
        
        # Obtenha a primeira escolha da resposta
        choice = response.choices[0].message
        
        # Verifique e registre o tipo de resposta recebida
        if hasattr(choice, 'tool_calls') and choice.tool_calls:
            logger.info(f"Resposta contém tool_calls: {choice.tool_calls}")
        elif hasattr(choice, 'function_call') and choice.function_call:
            logger.info(f"Resposta contém function_call: {choice.function_call}")
        elif hasattr(choice, 'content') and choice.content:
            logger.info(f"Resposta contém content: {choice.content[:100]}...")
        else:
            logger.warning("Resposta não contém tool_calls, function_call nem content")
            
        return choice
    except Exception as e:
        logger.error(f"Erro ao chamar a API OpenAI: {str(e)}")
        raise

def format_dict_response(data, indent=0, fields=None):
    """
    Formata um dicionário para exibição como texto.
    
    Args:
        data: Dicionário com os dados a serem formatados
        indent: Nível de indentação para formatação hierárquica
        fields: Lista de campos específicos a serem incluídos na resposta
               (pode incluir seções como 'dados_pessoais', 'contato', etc. ou campos específicos)
    """
    if not data:
        return "Sem dados disponíveis."
    
    # Log para depuração
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"format_dict_response recebeu: {str(data)[:500]}...")
    logger.info(f"Campos solicitados: {fields}")
        
    result = ""
    prefix = "  " * indent
    
    # Para formatações específicas de dados
    if "notas" in data and isinstance(data["notas"], list):
        result += f"**Notas do Aluno {data.get('aluno', {}).get('nome', '')}**\n\n"
        result += "<table>\n<tr><th>Disciplina</th><th>Nota</th><th>Data</th></tr>\n"
        
        for nota in data["notas"]:
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
    
    # Formato específico para responsáveis quando é uma pergunta direta
    # Removido para evitar conflito com o formato específico para informações do aluno
    
    # Formato específico para informações do aluno (novo formato visualmente atraente)
    if "dados_pessoais" in data and isinstance(data["dados_pessoais"], dict):
        nome_aluno = data.get("dados_pessoais", {}).get("nome", "")
        
        # Verificar se foram solicitados campos específicos
        if fields:
            # Converter campos para minúsculas para comparação case-insensitive
            fields_lower = [f.lower() for f in fields]
            
            # Verificar se foi solicitado um campo específico dentro de dados_pessoais
            campos_especificos_dados_pessoais = [f for f in fields_lower if f in [k.lower() for k in data["dados_pessoais"].keys()]]
            
            # Se foram solicitados campos específicos dentro de dados_pessoais
            if campos_especificos_dados_pessoais:
                result += f"# 📚 Informações do Aluno: {nome_aluno} 📚\n\n"
                
                for campo in campos_especificos_dados_pessoais:
                    # Encontrar a chave original (preservando case)
                    for k in data["dados_pessoais"].keys():
                        if k.lower() == campo:
                            v = data["dados_pessoais"][k]
                            label = k.replace('_', ' ').title()
                            if v:
                                if k == "matricula":
                                    result += f"📝 **{label}:** {v}\n"
                                elif k == "data_nascimento":
                                    result += f"🎂 **{label}:** {v}\n"
                                elif k == "idade":
                                    result += f"🔢 **{label}:** {v} anos\n"
                                elif k == "cpf":
                                    result += f"📄 **{label}:** {v}\n"
                                elif k == "rg":
                                    result += f"📄 **{label}:** {v}\n"
                                else:
                                    result += f"ℹ️ **{label}:** {v}\n"
                            else:
                                result += f"ℹ️ **{label}:** Não Informado\n"
                
                return result
            
            # Verificar quais seções foram solicitadas
            mostrar_dados_pessoais = 'dados_pessoais' in fields_lower
            mostrar_contato = 'contato' in fields_lower
            mostrar_endereco = 'endereco' in fields_lower
            mostrar_dados_academicos = 'dados_academicos' in fields_lower
            mostrar_responsaveis = 'responsaveis' in fields_lower
            mostrar_informacoes_adicionais = 'informacoes_adicionais' in fields_lower
            
            # Se nenhuma seção específica foi solicitada, verificar se há campos específicos
            if not any([mostrar_dados_pessoais, mostrar_contato, mostrar_endereco, 
                       mostrar_dados_academicos, mostrar_responsaveis, mostrar_informacoes_adicionais]):
                # Retornar apenas os campos solicitados
                result += f"# 📚 Informações do Aluno: {nome_aluno} 📚\n\n"
                
                for field in fields_lower:
                    # Procurar o campo em todas as seções
                    for section in ["dados_pessoais", "contato", "endereco", "dados_academicos"]:
                        if section in data and isinstance(data[section], dict):
                            for k, v in data[section].items():
                                if k.lower() == field:
                                    label = k.replace('_', ' ').title()
                                    if v:
                                        result += f"ℹ️ **{label}:** {v}\n"
                                    else:
                                        result += f"ℹ️ **{label}:** Não Informado\n"
                
                # Verificar se algum campo solicitado está em responsáveis
                if "responsaveis" in data and isinstance(data["responsaveis"], list) and len(data["responsaveis"]) > 0:
                    for field in fields_lower:
                        if field in ["responsavel", "responsáveis", "responsaveis"]:
                            result += "\n## 👪 Responsáveis\n\n"
                            for idx, resp in enumerate(data["responsaveis"], 1):
                                result += f"### Responsável {idx}\n\n"
                                if resp.get("nome"):
                                    result += f"👤 **Nome:** {resp['nome']}\n"
                                else:
                                    result += f"👤 **Nome:** Não Informado\n"
                                    
                                if resp.get("telefone"):
                                    result += f"📱 **Telefone:** {resp['telefone']}\n"
                                else:
                                    result += f"📱 **Telefone:** Não Informado\n"
                                result += "\n"
                
                return result
        
        # Se não foram solicitados campos específicos, mostrar todas as informações
        # Cabeçalho com nome do aluno
        result += f"# 📚 Ficha do Aluno: {nome_aluno} 📚\n\n"
        
        # Status do aluno (ativo/inativo)
        status = data.get("status", "")
        if status:
            status_emoji = "✅" if status == "Ativo" else "❌"
            result += f"{status_emoji} **Status:** {status}\n\n"
        
        # Separador
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Dados Pessoais (mostrar apenas se não foram especificados campos ou se foi solicitado explicitamente)
        if not fields or mostrar_dados_pessoais:
            result += "## 👤 Dados Pessoais\n\n"
            for k, v in data["dados_pessoais"].items():
                if k != "nome" and k != "foto_url":  # Nome já está no cabeçalho, foto_url será tratada separadamente
                    label = k.replace('_', ' ').title()
                    if v:
                        if k == "matricula":
                            result += f"📝 **{label}:** {v}\n"
                        elif k == "data_nascimento":
                            result += f"🎂 **{label}:** {v}\n"
                        elif k == "idade":
                            result += f"🔢 **{label}:** {v} anos\n"
                        elif k == "cpf":
                            result += f"📄 **{label}:** {v}\n"
                        elif k == "rg":
                            result += f"📄 **{label}:** {v}\n"
                        else:
                            result += f"ℹ️ **{label}:** {v}\n"
                    else:
                        result += f"ℹ️ **{label}:** Não Informado\n"
            result += "\n"
        
        # Contato (mostrar apenas se não foram especificados campos ou se foi solicitado explicitamente)
        if (not fields or mostrar_contato) and "contato" in data:
            result += "## 📞 Contato\n\n"
            if isinstance(data["contato"], dict):
                for k, v in data["contato"].items():
                    label = k.replace('_', ' ').title()
                    if v:
                        if k == "email":
                            result += f"📧 **{label}:** {v}\n"
                        elif k == "telefone":
                            result += f"📱 **{label}:** {v}\n"
                        else:
                            result += f"ℹ️ **{label}:** {v}\n"
                    else:
                        result += f"ℹ️ **{label}:** Não Informado\n"
            else:
                result += "ℹ️ **Informações de Contato:** Não Informadas\n"
            result += "\n"
        
        # Endereço (mostrar apenas se não foram especificados campos ou se foi solicitado explicitamente)
        if (not fields or mostrar_endereco) and "endereco" in data:
            result += "## 🏠 Endereço\n\n"
            if isinstance(data["endereco"], dict):
                for k, v in data["endereco"].items():
                    label = k.replace('_', ' ').title()
                    if v:
                        result += f"📍 **{label}:** {v}\n"
                    else:
                        result += f"📍 **{label}:** Não Informado\n"
            else:
                result += "📍 **Endereço:** Não Informado\n"
            result += "\n"
        
        # Separador (apenas se houver mais seções a serem mostradas)
        if (not fields or any([mostrar_dados_academicos, mostrar_responsaveis, mostrar_informacoes_adicionais])):
            result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Dados Acadêmicos (mostrar apenas se não foram especificados campos ou se foi solicitado explicitamente)
        if (not fields or mostrar_dados_academicos) and "dados_academicos" in data:
            result += "## 🎓 Dados Acadêmicos\n\n"
            if isinstance(data["dados_academicos"], dict):
                for k, v in data["dados_academicos"].items():
                    label = k.replace('_', ' ').title()
                    if v:
                        if k == "nivel":
                            result += f"📚 **{label}:** {v}\n"
                        elif k == "turno":
                            emoji = "🌞" if v == "Manhã" else "🌙" if v == "Noite" else "🌆"
                            result += f"{emoji} **{label}:** {v}\n"
                        elif k == "ano":
                            result += f"📅 **{label}:** {v}\n"
                        elif k == "turma":
                            result += f"👨‍👩‍👧‍👦 **{label}:** {v}\n"
                        elif k == "data_matricula":
                            result += f"📆 **{label}:** {v}\n"
                        else:
                            result += f"ℹ️ **{label}:** {v}\n"
                    else:
                        result += f"ℹ️ **{label}:** Não Informado\n"
            else:
                result += "ℹ️ **Dados Acadêmicos:** Não Informados\n"
            result += "\n"
        
        # Separador (apenas se houver mais seções a serem mostradas)
        if (not fields or any([mostrar_responsaveis, mostrar_informacoes_adicionais])):
            result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Responsáveis (mostrar apenas se não foram especificados campos ou se foi solicitado explicitamente)
        if (not fields or mostrar_responsaveis) and "responsaveis" in data:
            result += "## 👪 Responsáveis\n\n"
            if isinstance(data["responsaveis"], list) and len(data["responsaveis"]) > 0:
                for idx, resp in enumerate(data["responsaveis"], 1):
                    result += f"### Responsável {idx}\n\n"
                    if resp.get("nome"):
                        result += f"👤 **Nome:** {resp['nome']}\n"
                    else:
                        result += f"👤 **Nome:** Não Informado\n"
                        
                    if resp.get("telefone"):
                        result += f"📱 **Telefone:** {resp['telefone']}\n"
                    else:
                        result += f"📱 **Telefone:** Não Informado\n"
                    result += "\n"
            else:
                result += "ℹ️ **Responsáveis:** Não Informados\n\n"
        
        # Informações Adicionais (mostrar apenas se não foram especificados campos ou se foi solicitado explicitamente)
        if (not fields or mostrar_informacoes_adicionais) and "informacoes_adicionais" in data:
            if isinstance(data["informacoes_adicionais"], dict) and any(data["informacoes_adicionais"].values()):
                result += "## ℹ️ Informações Adicionais\n\n"
                for k, v in data["informacoes_adicionais"].items():
                    label = k.replace('_', ' ').title()
                    if v:
                        result += f"📋 **{label}:** {v}\n"
                    else:
                        result += f"📋 **{label}:** Não Informado\n"
                result += "\n"
        
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
