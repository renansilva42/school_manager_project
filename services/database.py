from django.db.models import Q
from apps.alunos.models import Aluno
import logging

# Configurar o logger
logger = logging.getLogger(__name__)

class DatabaseService:
    def upload_photo(self, photo_file, aluno_id):
        """
        Upload a photo file to local storage and return the URL
        
        Args:
            photo_file: InMemoryUploadedFile object containing the photo
            aluno_id: UUID of the student
            
        Returns:
            str: URL of the uploaded photo or None if upload fails
        """
        try:
            # Obtém o aluno
            aluno = self.get_aluno(aluno_id)
            
            # Salva a foto no campo foto do modelo Aluno
            aluno.foto = photo_file
            aluno.save()
            
            # Retorna a URL da foto
            return aluno.foto.url if aluno.foto else None
            
        except Exception as e:
            logger.error(f"Error uploading photo: {str(e)}")
            return None

    def delete_photo(self, aluno_id):
        """
        Delete a student's photo
        
        Args:
            aluno_id: UUID of the student
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            aluno = self.get_aluno(aluno_id)
            if aluno.foto:
                aluno.foto.delete()  # Deleta o arquivo físico
                aluno.foto = None    # Remove a referência no banco de dados
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
        return Aluno.objects.create(**data)

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