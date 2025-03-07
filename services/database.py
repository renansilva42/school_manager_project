from supabase import create_client
from django.conf import settings
import uuid
import base64
from PIL import Image
from io import BytesIO

class SupabaseService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.client = create_client(self.supabase_url, self.supabase_key)

    def upload_photo(self, photo_file, aluno_id):
        try:
            # Gerar nome único para o arquivo
            file_ext = photo_file.name.split('.')[-1]
            file_name = f"aluno_{aluno_id}.{file_ext}"
            
            # Otimizar a imagem
            img = Image.open(photo_file)
            img.thumbnail((800, 800))
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            photo_data = buffer.getvalue()
            
            # Upload para o Supabase Storage
            response = self.client.storage \
                .from_('alunos_fotos') \
                .upload(file_name, photo_data, {'content-type': 'image/jpeg'})
            
            if response.error:
                raise Exception(response.error.message)
            
            # Obter URL pública
            photo_url = self.client.storage \
                .from_('alunos_fotos') \
                .get_public_url(file_name)
            
            return photo_url
            
        except Exception as e:
            print(f"Erro ao fazer upload da foto: {str(e)}")
            return None

    def create_aluno(self, aluno_data):
        try:
            response = self.client.table('alunos').insert(aluno_data).execute()
            return response.data if response else None
        except Exception as e:
            print(f"Erro Supabase: {str(e)}")
            return None

    def update_aluno(self, aluno_id, aluno_data):
        try:
            # Handle photo upload if present
            if 'foto' in aluno_data and aluno_data['foto']:
                photo_url = self.upload_photo(aluno_data['foto'], aluno_id)
                aluno_data['foto_url'] = photo_url
            
            # Remove the actual photo file from data before sending to Supabase
            if 'foto' in aluno_data:
                del aluno_data['foto']
            
            response = self.client.table('alunos') \
                .update(aluno_data) \
                .eq('id', aluno_id) \
                .execute()
            return response.data if response else None
        except Exception as e:
            print(f"Supabase error: {str(e)}")
            return None