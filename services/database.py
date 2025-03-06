# services/database.py
from supabase_client import get_supabase_client
from datetime import datetime

class SupabaseService:
    def __init__(self):
        self.supabase = get_supabase_client()

    def create_aluno(self, data):
        return self.supabase.table('alunos').insert(data).execute()

    def get_aluno(self, id):
        return self.supabase.table('alunos').select("*").eq('id', id).execute()

    def update_aluno(self, id, data):
        return self.supabase.table('alunos').update(data).eq('id', id).execute()

    def delete_aluno(self, id):
        return self.supabase.table('alunos').delete().eq('id', id).execute()

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