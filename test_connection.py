# test_connection.py
from services.database import SupabaseService

def test_connection():
    service = SupabaseService()
    try:
        response = service.list_alunos()
        print("Connection successful!")
        print(f"Number of records: {len(response.data) if response and hasattr(response, 'data') else 0}")
        return response
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return None

if __name__ == "__main__":
    test_connection()