import openai
from django.conf import settings
from apps.alunos.models import Aluno, Nota
from django.db.models import Q
from datetime import datetime
import pytz
from typing import Optional, Dict

def get_current_datetime() -> str:
    """
    Retorna a data e hora atuais no fuso horário de Belém, Pará (GMT-3).
    Formato: DD/MM/YYYY HH:MM:SS
    """
    fuso_belem = pytz.timezone("America/Belem")
    agora = datetime.now(fuso_belem)
    return agora.strftime("%d/%m/%Y %H:%M:%S")

def get_student_info(query: str) -> Optional[Dict]:
    """
    Busca informações de um aluno com base no nome ou série fornecido na query.
    Retorna um dicionário com os dados do aluno, incluindo notas e URL da foto, ou None se não encontrado.
    """
    try:
        # Normaliza a query removendo prefixos comuns e ajustando para minúsculas
        query = query.lower().replace("notas do", "").replace("telefone do", "").replace("foto do", "").replace("endereço do", "").strip()
        
        # Busca por correspondência exata no nome
        aluno = Aluno.objects.filter(nome__iexact=query).first()
        
        # Se não encontrado, busca por correspondências parciais
        if not aluno:
            search_terms = query.split()
            alunos = Aluno.objects.filter(
                Q(nome__icontains=search_terms[0]) if search_terms else Q()
            )
            for term in search_terms[1:]:
                alunos = alunos.filter(nome__icontains=term)
            aluno = alunos.first()
        
        if aluno:
            # Coleta notas do aluno
            notas = Nota.objects.filter(aluno=aluno)
            notas_info = [f"{nota.disciplina}: {nota.valor}" for nota in notas]
            
            # Estrutura os dados do aluno
            aluno_info = {
                "nome": aluno.nome,
                "matricula": aluno.matricula,
                "data_nascimento": aluno.data_nascimento.strftime("%d/%m/%Y") if aluno.data_nascimento else "Não informado",
                "serie": aluno.serie,
                "email": aluno.email if aluno.email else "Não informado",
                "telefone": aluno.telefone if aluno.telefone else "Não informado",
                "endereco": aluno.endereco if aluno.endereco else "Não informado",
                "notas": notas_info if notas_info else ["Nenhuma nota registrada"],
                "responsavel": aluno.dados_adicionais if aluno.dados_adicionais else "Não informado",
                "foto_url": aluno.foto.url if aluno.foto else None
            }
            return aluno_info
        return None
    except Exception as e:
        print(f"Erro ao buscar informações do aluno: {e}")
        return None

def get_openai_response(user_message: str, context: str = "") -> str:
    """
    Gera uma resposta usando a API de Chat Completion da OpenAI, integrando dados de alunos quando aplicável.
    Mantém um tom amigável e profissional, fornecendo informações específicas conforme solicitado.
    """
    try:
        # Verifica se a chave da API está configurada
        if not settings.OPENAI_API_KEY:
            return "Erro: Chave da API OpenAI não configurada. Por favor, contate o administrador."
        
        openai.api_key = settings.OPENAI_API_KEY

        # Lista de saudações simples
        saudacoes = ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hi", "hello"]
        mensagem_lower = user_message.lower().strip()

        # Responde a saudações simples
        if any(saudacao in mensagem_lower for saudacao in saudacoes) and len(mensagem_lower.split()) <= 3:
            return f"Olá! Sou o assistente virtual da Escola Manager. Como posso ajudar você hoje? A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3)."

        # Extrai o nome do aluno potencial da mensagem
        query = mensagem_lower
        for keyword in ["notas do", "telefone do", "endereço do", "foto do"]:
            if keyword in query:
                query = query.replace(keyword, "").strip()
                break

        # Busca informações do aluno
        info_aluno = get_student_info(query)

        # Prompt do sistema para a OpenAI
        system_prompt = f"""
        Você é um assistente escolar amigável e prestativo da Escola Manager, com acesso aos dados dos alunos.
        Regras importantes:
        1. Sempre mantenha um tom amigável, acolhedor e profissional.
        2. Comece suas respostas com uma saudação apropriada, como "Olá!" ou "Oi!".
        3. Forneça todas as informações disponíveis sobre os alunos de forma clara e organizada.
        4. Se o usuário pedir informações específicas (como notas, telefone, endereço ou foto), forneça exatamente o que foi solicitado, formatando adequadamente (ex.: notas em lista, URL da foto se disponível).
        5. Se não encontrar informações sobre um aluno, diga: "Desculpe, não consegui encontrar informações sobre esse aluno. Por favor, verifique o nome ou forneça mais detalhes."
        6. Se não tiver certeza sobre alguma informação, seja honesto e diga que não tem acesso ou que a informação não está disponível.
        7. Termine suas respostas com: "Estou à disposição para mais perguntas!"
        8. Inclua a data e hora atuais (horário de Belém, Pará - GMT-3) em todas as respostas.

        A data e hora atuais são: {get_current_datetime()}.
        
        Exemplos de resposta:
        - Para "notas do João Pedro": "Olá! Aqui estão as notas de João Pedro: Matemática: 8.5, Português: 9.0. Estou à disposição para mais perguntas!"
        - Para "foto do João Pedro": "Oi! Aqui está a foto de João Pedro: [URL da foto]. Estou à disposição para mais perguntas!"
        """

        # Prepara o contexto para a OpenAI
        context_with_data = {
            "user_message": user_message,
            "aluno_info": info_aluno if info_aluno else None
        }

        # Constrói as mensagens para a API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Contexto: {context_with_data}\n\nPergunta: {user_message}"}
        ]

        # Chama a API de Chat Completion
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=messages,
            temperature=0.7,  # Equilíbrio entre criatividade e precisão
            max_tokens=500,   # Limite suficiente para respostas detalhadas
            top_p=0.9         # Melhora a qualidade das respostas
        )

        return response.choices[0].message['content'].strip()

    except openai.OpenAIError as e:
        print(f"Erro na chamada da API OpenAI: {e}")
        return f"Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3)."
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return f"Desculpe, ocorreu um erro inesperado. Por favor, tente novamente. A data e hora atuais são: {get_current_datetime()} (horário de Belém, Pará - GMT-3)."

# Exemplo de uso para teste
if __name__ == "__main__":
    queries = [
        "oi",
        "oi, preciso saber as notas do João Pedro",
        "qual é o telefone do João Pedro?",
        "mostre a foto do João Pedro"
    ]
    for q in queries:
        print(f"Usuário: {q}")
        print(f"Assistente: {get_openai_response(q)}\n")