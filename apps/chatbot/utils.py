import openai
from django.conf import settings
from apps.alunos.models import Aluno, Nota
from django.db.models import Q

def get_student_info(nome_ou_serie):
    try:
        aluno = Aluno.objects.filter(
            Q(nome__icontains=nome_ou_serie) | 
            Q(serie__icontains=nome_ou_serie)
        ).first()
        
        if aluno:
            notas = Nota.objects.filter(aluno=aluno)
            notas_info = [f"{nota.disciplina}: {nota.valor}" for nota in notas]
            
            aluno_info = {
                "nome": aluno.nome,
                "matricula": aluno.matricula,
                "data_nascimento": aluno.data_nascimento,
                "serie": aluno.serie,
                "email": aluno.email,
                "telefone": aluno.telefone,  # Adicionado telefone
                "endereco": aluno.endereco,  # Adicionado endereço
                "notas": notas_info,
                "responsavel": aluno.dados_adicionais
            }
            return aluno_info
        return None
    except Exception as e:
        print(f"Erro ao buscar informações do aluno: {e}")
        return None

def get_openai_response(user_message, context=""):
    try:
        # Verifica se é uma saudação
        saudacoes = ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hi", "hello"]
        mensagem_lower = user_message.lower()
        
        # Se for apenas uma saudação, retorna uma resposta amigável
        if any(saudacao in mensagem_lower for saudacao in saudacoes) and len(mensagem_lower.split()) <= 3:
            return "Olá! Que bom ter você por aqui! Como posso ajudar hoje? Posso fornecer informações sobre qualquer aluno da escola."

        # Processamento normal para outras mensagens
        palavras_chave = mensagem_lower.split()
        info_aluno = None
        
        for palavra in palavras_chave:
            info_aluno = get_student_info(palavra)
            if info_aluno:
                break

        system_prompt = """
        Você é um assistente escolar amigável e prestativo que tem acesso aos dados dos alunos.
        Regras importantes:
        1. Sempre mantenha um tom amigável e acolhedor
        2. Comece suas respostas com uma saudação apropriada
        3. Forneça todas as informações disponíveis sobre os alunos de forma clara
        4. Se não tiver certeza sobre alguma informação, seja honesto e diga que não tem acesso
        5. Termine suas respostas se colocando à disposição para mais perguntas
        6. Se o usuário pedir informações específicas (como telefone ou endereço), forneça exatamente o que foi pedido
        """

        context_with_data = {
            "user_message": user_message,
            "aluno_info": info_aluno if info_aluno else "Aluno não encontrado"
        }

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Contexto: {context_with_data}\n\nPergunta: {user_message}"}
            ],
            temperature=0.7,
            max_tokens=500
        )

        if not info_aluno:
            return "Olá! Por favor, especifique o nome do aluno ou faça uma pergunta mais específica sobre qual aluno você gostaria de saber informações. Estou aqui para ajudar!"

        return response.choices[0].message['content']

    except Exception as e:
        print(f"Erro na chamada da API: {e}")
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."