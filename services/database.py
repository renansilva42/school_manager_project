from supabase import create_client
from django.conf import settings

class SupabaseService:
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def list_alunos(self, filters=None):
        query = self.client.table('alunos').select('*')
        
        if filters:
            if filters.get('nivel'):
                query = query.eq('nivel', filters['nivel'])
            if filters.get('turno'):
                query = query.eq('turno', filters['turno'])
            if filters.get('ano'):
                query = query.eq('ano', filters['ano'])
            if filters.get('search'):
                query = query.or_(
                    f"nome.ilike.%{filters['search']}%,"
                    f"matricula.ilike.%{filters['search']}%"
                )
        
        # Corrigindo a chamada do método order
        query = query.order('nivel')
        query = query.order('turno')
        query = query.order('ano')
        query = query.order('nome')
        
        return query.execute()

    def get_aluno(self, id):
        return self.client.table('alunos').select('*').eq('id', id).execute()

    def create_aluno(self, data):
        return self.client.table('alunos').insert(data).execute()

    def update_aluno(self, id, data):
        return self.client.table('alunos').update(data).eq('id', id).execute()

    def delete_aluno(self, id):
        return self.client.table('alunos').delete().eq('id', id).execute()

    def upload_photo(self, photo_file, aluno_id):
        file_path = f'alunos/{aluno_id}/{photo_file.name}'
        try:
            self.client.storage.from_('photos').upload(
                file_path,
                photo_file.read()
            )
            return self.client.storage.from_('photos').get_public_url(file_path)
        except Exception as e:
            print(f"Erro ao fazer upload da foto: {str(e)}")
            return None