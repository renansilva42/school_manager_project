import openai
from django.conf import settings
from apps.alunos.models import Aluno, Nota
from django.db.models import Q

def get_student_info(nome_ou_serie):
    """Função para buscar informações detalhadas do aluno"""
    try:
        # Busca por nome ou série
        aluno = Aluno.objects.filter(
            Q(nome__icontains=nome_ou_serie) | 
            Q(serie__icontains=nome_ou_serie)
        ).first()
        
        if aluno:
            # Busca as notas do aluno
            notas = Nota.objects.filter(aluno=aluno)
            notas_info = [f"{nota.disciplina}: {nota.valor}" for nota in notas]
            
            # Formata os dados do aluno
            aluno_info = {
                "nome": aluno.nome,
                "matricula": aluno.matricula,
                "data_nascimento": aluno.data_nascimento,
                "serie": aluno.serie,
                "email": aluno.email,
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
        # Extrai informações relevantes da mensagem do usuário
        palavras_chave = user_message.lower().split()
        info_aluno = None
        
        # Busca por aluno mencionado na mensagem
        for palavra in palavras_chave:
            info_aluno = get_student_info(palavra)
            if info_aluno:
                break

        # Define o prompt do sistema
        system_prompt = """
        Você é um assistente escolar que tem acesso aos dados dos alunos.
        Regras importantes:
        1. Você pode fornecer informações sobre nome, matrícula, série e notas dos alunos e quaisquer outras sobre os alunos ou seus responsáveis
        2. Responda de forma natural e amigável
        3. Se não tiver certeza sobre alguma informação, diga que não tem acesso a essa informação
        4. Mantenha um tom profissional e educado
        """

        # Prepara o contexto com as informações do aluno
        context_with_data = {
            "user_message": user_message,
            "aluno_info": info_aluno if info_aluno else "Aluno não encontrado"
        }

        # Faz a chamada para a API da OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",  # Modelo atualizado conforme solicitado
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Contexto: {context_with_data}\n\nPergunta: {user_message}"}
            ],
            temperature=0.7,
            max_tokens=500
        )

        # Se não encontrou informações do aluno
        if not info_aluno:
            return "Por favor, especifique o nome do aluno ou faça uma pergunta mais específica sobre qual aluno você gostaria de saber informações."

        return response.choices[0].message['content']

    except Exception as e:
        print(f"Erro na chamada da API: {e}")
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."