import os
import django
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.utils import OperationalError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

def verificar_banco():
    """Verifica se o banco de dados está disponível"""
    conexao = connections['default']
    try:
        conexao.cursor()
        return True
    except OperationalError:
        return False

def criar_superusuarios():
    """Cria três superusuários usando variáveis de ambiente"""
    User = get_user_model()
    
    # Lista de superusuários para criar usando variáveis de ambiente
    superusers = []
    for i in range(1, 4):  # Para os 3 superusuários
        username = os.getenv(f'DJANGO_SUPERUSER_USERNAME{i}')
        email = os.getenv(f'DJANGO_SUPERUSER_EMAIL{i}')
        password = os.getenv(f'DJANGO_SUPERUSER_PASSWORD{i}')
        
        if username and email and password:
            superusers.append({
                'username': username,
                'email': email,
                'password': password
            })
    
    for user_data in superusers:
        try:
            if not User.objects.filter(username=user_data['username']).exists():
                print(f"Criando superusuário {user_data['username']}...")
                User.objects.create_superuser(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                print(f"Superusuário {user_data['username']} criado com sucesso!")
            else:
                print(f"Superusuário {user_data['username']} já existe.")
        except Exception as e:
            print(f"Erro ao criar superusuário {user_data['username']}: {e}")

def executar_migracoes():
    """Executa as migrações do banco de dados"""
    print("Verificando conexão com o banco de dados...")
    if not verificar_banco():
        print("Erro: Não foi possível conectar ao banco de dados!")
        return False
        
    print("Executando migrações...")
    try:
        os.system('python manage.py migrate')
        return True
    except Exception as e:
        print(f"Erro durante as migrações: {e}")
        return False

if __name__ == "__main__":
    if verificar_banco():
        if executar_migracoes():
            criar_superusuarios()
        else:
            print("Falha ao executar migrações!")
    else:
        print("Falha na conexão com o banco de dados!")