from django.db.models import Q
from apps.alunos.models import Aluno
import logging
import base64
from django.core.files.base import ContentFile

# Configurar o logger
logger = logging.getLogger(__name__)

class DatabaseService:
    def upload_photo(self, photo_file, aluno_id):
        """
        Upload a photo file to local storage and return the URL
        """
        try:
            aluno = self.get_aluno(aluno_id)
            aluno.foto = photo_file
            aluno.save()
            return aluno.foto.url if aluno.foto else None
        except Exception as e:
            logger.error(f"Error uploading photo: {str(e)}")
            return None

    def delete_photo(self, aluno_id):
        """
        Delete a student's photo
        """
        try:
            aluno = self.get_aluno(aluno_id)
            if aluno.foto:
                aluno.foto.delete()
                aluno.foto = None
                aluno.save()
            return True
        except Exception as e:
            logger.error(f"Error deleting photo: {str(e)}")
            return False
        
    def list_alunos(self, filters=None):
        queryset = Aluno.objects.all()
        if filters:
            if filters.get('nivel'):
                queryset = queryset.filter(nivel=filters['nivel'])
            if filters.get('turno'):
                queryset = queryset.filter(turno=filters['turno'])
            if filters.get('ano'):
                queryset = queryset.filter(ano=filters['ano'])
            if filters.get('search'):
                queryset = queryset.filter(
                    Q(nome__icontains=filters['search']) |
                    Q(matricula__icontains=filters['search'])
                )
        return queryset.order_by('nivel', 'turno', 'ano', 'nome')

    def get_aluno(self, id):
        return Aluno.objects.get(id=id)

    def create_aluno(self, data):
        """
        Create a new student with optional photo processing
        """
        try:
            # Extrair foto_base64 dos dados se existir
            foto_base64 = data.pop('foto_base64', None)
            
            
            # Criar o aluno primeiro sem a foto
            aluno = Aluno.objects.create(**data)
            
            # Se tiver foto em base64, converter e salvar
            if foto_base64:
                try:
                    # Remover cabeçalho do base64 se existir
                    if 'data:image' in foto_base64:
                        format, imgstr = foto_base64.split(';base64,')
                    else:
                        imgstr = foto_base64
                        
                    # Converter base64 para arquivo
                    decoded_file = base64.b64decode(imgstr)
                    
                    # Criar nome do arquivo
                    filename = f'foto_aluno_{aluno.id}.png'
                    
                    # Criar arquivo e associar ao aluno
                    aluno.foto.save(filename, ContentFile(decoded_file), save=True)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar foto: {str(e)}")
                    # Mesmo se der erro na foto, o aluno já foi criado
                    
            return aluno
            
        except Exception as e:
            logger.error(f"Erro ao criar aluno: {str(e)}")
            raise

    def update_aluno(self, id, data):
        aluno = Aluno.objects.get(id=id)
        for key, value in data.items():
            setattr(aluno, key, value)
        aluno.save()
        return aluno

    def delete_aluno(self, id):
        aluno = Aluno.objects.get(id=id)
        aluno.delete()
        return True