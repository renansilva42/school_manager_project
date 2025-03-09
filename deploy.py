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

def criar_superusuario():
    """Cria um superusuário se não existir"""
    User = get_user_model()
    
    # Pegar credenciais das variáveis de ambiente
    EMAIL = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@exemplo.com')
    USERNAME = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
    SENHA = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'senhapadrao')
    
    try:
        if not User.objects.filter(is_superuser=True).exists():
            print("Criando superusuário...")
            User.objects.create_superuser(
                username=USERNAME,
                email=EMAIL,
                password=SENHA
            )
            print("Superusuário criado com sucesso!")
        else:
            print("Superusuário já existe.")
    except Exception as e:
        print(f"Erro ao criar superusuário: {e}")

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
        criar_superusuario()
    else:
        print("Falha na conexão com o banco de dados!")