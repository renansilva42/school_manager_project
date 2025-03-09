import os
import django
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.utils import OperationalError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

def executar_migracoes():
    """Executa as migrações do banco de dados"""
    print("Executando migrações...")
    os.system('python manage.py migrate')

def criar_superusuarios():
    """Cria três superusuários se não existirem"""
    User = get_user_model()
    
    # Lista de superusuários para criar
    superusers = [
        {
            'username': 'admin1',
            'email': 'admin1@exemplo.com',
            'password': 'senhapadrao1'
        },
        {
            'username': 'admin2',
            'email': 'admin2@exemplo.com',
            'password': 'senhapadrao2'
        },
        {
            'username': 'admin3',
            'email': 'admin3@exemplo.com',
            'password': 'senhapadrao3'
        }
    ]
    
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

def verificar_banco():
    """Verifica se o banco de dados está disponível"""
    conexao = connections['default']
    try:
        conexao.cursor()
        return True
    except OperationalError:
        return False

if __name__ == "__main__":
    if verificar_banco():
        executar_migracoes()
        criar_superusuarios()
    else:
        print("Falha na conexão com o banco de dados!")