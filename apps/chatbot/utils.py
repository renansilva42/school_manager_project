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

def format_dict_response(data, indent=0):
    """
    Formata um dicionário para exibição como texto.
    """
    if not data:
        return "Sem dados disponíveis."
        
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
    if "responsaveis" in data and isinstance(data["responsaveis"], list) and len(data["responsaveis"]) > 0:
        nome_aluno = data.get("dados_pessoais", {}).get("nome", data.get("nome", ""))
        if nome_aluno:
            result += f"**Responsáveis do Aluno {nome_aluno}**\n\n"
            
            for idx, resp in enumerate(data["responsaveis"], 1):
                result += f"**Responsável {idx}**\n"
                for k, v in resp.items():
                    if v:
                        result += f"- {k.replace('_', ' ').title()}: {v}\n"
                result += "\n"
            
            return result
    
    # Formato específico para informações do aluno (novo formato visualmente atraente)
    if "dados_pessoais" in data and isinstance(data["dados_pessoais"], dict):
        nome_aluno = data.get("dados_pessoais", {}).get("nome", "")
        
        # Cabeçalho com nome do aluno
        result += f"# 📚 Ficha do Aluno: {nome_aluno} 📚\n\n"
        
        # Status do aluno (ativo/inativo)
        status = data.get("status", "")
        if status:
            status_emoji = "✅" if status == "Ativo" else "❌"
            result += f"{status_emoji} **Status:** {status}\n\n"
        
        # Separador
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Dados Pessoais
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
        
        # Contato
        result += "## 📞 Contato\n\n"
        if "contato" in data and isinstance(data["contato"], dict):
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
        
        # Endereço
        result += "## 🏠 Endereço\n\n"
        if "endereco" in data and isinstance(data["endereco"], dict):
            for k, v in data["endereco"].items():
                label = k.replace('_', ' ').title()
                if v:
                    result += f"📍 **{label}:** {v}\n"
                else:
                    result += f"📍 **{label}:** Não Informado\n"
        else:
            result += "📍 **Endereço:** Não Informado\n"
        result += "\n"
        
        # Separador
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Dados Acadêmicos
        result += "## 🎓 Dados Acadêmicos\n\n"
        if "dados_academicos" in data and isinstance(data["dados_academicos"], dict):
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
        
        # Separador
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Responsáveis
        result += "## 👪 Responsáveis\n\n"
        if "responsaveis" in data and isinstance(data["responsaveis"], list) and len(data["responsaveis"]) > 0:
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
        
        # Informações Adicionais (se existirem)
        if "informacoes_adicionais" in data and isinstance(data["informacoes_adicionais"], dict) and any(data["informacoes_adicionais"].values()):
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
