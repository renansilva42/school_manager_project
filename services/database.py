# services/database.py
from supabase_client import get_supabase_client
from datetime import datetime
from supabase import create_client
from django.conf import settings

class SupabaseService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.client = create_client(self.supabase_url, self.supabase_key)

    def create_aluno(self, aluno_data):
        try:
            response = self.client.table('alunos').insert(aluno_data).execute()
            print(f"Supabase response: {response}")
            return response.data if response else None
        except Exception as e:
            print(f"Supabase error: {str(e)}")
            return None

    def update_aluno(self, aluno_id, aluno_data):
        try:
            response = self.client.table('alunos').update(aluno_data).eq('id', aluno_id).execute()
            return response.data if response else None
        except Exception as e:
            print(f"Supabase error: {str(e)}")
            return None

    def delete_aluno(self, aluno_id):
        try:
            response = self.client.table('alunos').delete().eq('id', aluno_id).execute()
            return response.data if response else None
        except Exception as e:
            print(f"Supabase error: {str(e)}")
            return None

    def list_alunos(self, filters=None):
        query = self.supabase.table('alunos').select("*")
        
        if filters:
            if filters.get('nivel'):
                query = query.eq('nivel', filters['nivel'])
            if filters.get('turno'):
                query = query.eq('turno', filters['turno'])
            if filters.get('ano'):
                query = query.eq('ano', filters['ano'])
            if filters.get('search'):
                query = query.or_(f"nome.ilike.%{filters['search']}%,matricula.ilike.%{filters['search']}%")

        return query.execute()

    def create_nota(self, data):
        return self.supabase.table('notas').insert(data).execute()

    def get_notas_aluno(self, aluno_id):
        return self.supabase.table('notas').select("*").eq('aluno_id', aluno_id).execute()