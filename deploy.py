import os
import django

# Primeiro, configure o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

# Somente após o django.setup() importamos os modelos
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import connections
from django.db.utils import OperationalError
from services.database import SupabaseService
from apps.alunos.models import Aluno

def verificar_banco():
    """Verifica se o banco de dados está disponível"""
    try:
        from services.database import SupabaseService
        service = SupabaseService()
        
        # Set the database environment variables from the working Supabase connection
        os.environ['SUPABASE_DB_NAME'] = service.db_name
        os.environ['SUPABASE_DB_USER'] = service.db_user
        os.environ['SUPABASE_DB_PASSWORD'] = service.db_password
        os.environ['SUPABASE_DB_HOST'] = service.db_host
        os.environ['SUPABASE_DB_PORT'] = service.db_port
        
        response = service.list_alunos()
        return True if response else False
    except Exception as e:
        print(f"Erro na verificação do banco: {e}")
        return False

def criar_grupo_administradores():
    """Cria o grupo Administradores com todas as permissões"""
    try:
        # Obtém ou cria o grupo Administradores
        grupo_admin, created = Group.objects.get_or_create(name='Administradores')
        
        # Obtém todas as permissões disponíveis
        todas_permissoes = Permission.objects.all()
        
        # Adiciona todas as permissões ao grupo
        grupo_admin.permissions.set(todas_permissoes)
        
        print("Grupo Administradores configurado com todas as permissões!")
        return grupo_admin
    except Exception as e:
        print(f"Erro ao configurar grupo Administradores: {e}")
        return None

def criar_superusuarios():
    """Cria superusuários com todas as permissões e os adiciona ao grupo Administradores"""
    User = get_user_model()
    
    # Cria/obtém o grupo Administradores
    grupo_admin = criar_grupo_administradores()
    if not grupo_admin:
        return
    
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
            # Cria ou obtém o superusuário
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                email=user_data['email']
            )
            
            if created:
                user.set_password(user_data['password'])
                print(f"Criando superusuário {user_data['username']}...")
            else:
                print(f"Superusuário {user_data['username']} já existe.")
            
            # Configura como superusuário
            user.is_superuser = True
            user.is_staff = True
            
            # Adiciona todas as permissões individuais
            todas_permissoes = Permission.objects.all()
            user.user_permissions.set(todas_permissoes)
            
            # Adiciona ao grupo Administradores
            user.groups.add(grupo_admin)
            
            user.save()
            
            print(f"Superusuário {user_data['username']} configurado com todas as permissões!")
            
        except Exception as e:
            print(f"Erro ao configurar superusuário {user_data['username']}: {e}")

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

def sincronizar_com_supabase():
    """Sincroniza os dados dos alunos com o Supabase"""
    print("Iniciando sincronização com Supabase...")
    try:
        supabase = SupabaseService()
        # Busca todos os alunos do Supabase
        response = supabase.list_alunos()
        
        if response and hasattr(response, 'data'):
            for aluno_data in response.data:
                # Atualiza ou cria o aluno no banco local
                Aluno.objects.update_or_create(
                    id=aluno_data['id'],
                    defaults=aluno_data
                )
            print("Sincronização com Supabase concluída com sucesso!")
        return True
    except Exception as e:
        print(f"Erro na sincronização com Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    if verificar_banco():
        if executar_migracoes():
            print("Iniciando sincronização com Supabase...")
            if sincronizar_com_supabase():
                print("Sincronização concluída. Configurando superusuários...")
                criar_superusuarios()
            else:
                print("Falha na sincronização com Supabase!")
        else:
            print("Falha ao executar migrações!")
    else:
        print("Falha na conexão com o banco de dados!")