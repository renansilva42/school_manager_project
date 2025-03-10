import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

from django.db import connection

def test_connection():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("Conexão com o banco de dados estabelecida com sucesso!")
        return True
    except Exception as e:
        print(f"Erro na conexão: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()