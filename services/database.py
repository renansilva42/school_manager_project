from supabase import create_client
from django.conf import settings

class SupabaseService:
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        # Adicione os atributos de conexão
        self.db_name = settings.DATABASES['default']['NAME']
        self.db_user = settings.DATABASES['default']['USER']
        self.db_password = settings.DATABASES['default']['PASSWORD']
        self.db_host = settings.DATABASES['default']['HOST']
        self.db_port = settings.DATABASES['default']['PORT']

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
    
    def sincronizar_com_supabase(self):
        """
        Sincroniza dados entre Supabase e banco local
        """
        try:
            # Usa o método list_alunos já existente na classe
            response = self.list_alunos()
            
            if response and hasattr(response, 'data'):
                from apps.alunos.models import Aluno  # Importação local para evitar circular import
                
                for aluno_data in response.data:
                    # Remove os campos que não queremos sincronizar
                    aluno_data.pop('created_at', None)
                    aluno_data.pop('dados_adicionais', None)
                    
                    # Atualiza ou cria o aluno no banco local
                    Aluno.objects.update_or_create(
                        id=aluno_data['id'],
                        defaults=aluno_data
                    )
                return True
            return False
        except Exception as e:
            print(f"Erro na sincronização com Supabase: {str(e)}")
            return False

    def get_aluno(self, id):
        return self.client.table('alunos').select('*').eq('id', id).execute()

    def create_aluno(self, data):
        return self.client.table('alunos').insert(data).execute()

    def update_aluno(self, id, data):
        return self.client.table('alunos').update(data).eq('id', id).execute()

    def delete_aluno(self, id):
        return self.client.table('alunos').delete().eq('id', id).execute()

    def upload_photo(self, photo_file, aluno_id):
        """
        Upload a photo to Supabase storage and return the public URL
        """
        if not photo_file:
            return None
            
        file_path = f'alunos/{aluno_id}/{photo_file.name}'
        try:
            # Upload the photo to the fotos_alunos bucket
            self.client.storage.from_('fotos_alunos').upload(
                file_path,
                photo_file.read()
            )
            
            # Get the public URL of the uploaded photo
            photo_url = self.client.storage.from_('fotos_alunos').get_public_url(file_path)
            
            # Update the aluno record with the photo URL
            self.update_aluno(aluno_id, {'foto': photo_url})
            
            return photo_url
        except Exception as e:
            print(f"Erro ao fazer upload da foto: {str(e)}")
            return None