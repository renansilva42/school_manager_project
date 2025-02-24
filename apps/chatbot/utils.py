# apps/chatbot/utils.py
import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

def get_openai_response(user_message, context):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente escolar com acesso aos dados dos alunos."},
                {"role": "user", "content": f"Context: {context}\n\nPergunta: {user_message}"}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Erro ao processar a mensagem: {str(e)}"