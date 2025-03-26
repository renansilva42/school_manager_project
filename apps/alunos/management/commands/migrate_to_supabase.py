from django.core.management.base import BaseCommand
from apps.alunos.models import Aluno, Nota
from services.database import DatabaseService
from django.forms.models import model_to_dict
import uuid
from decimal import Decimal
import json

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        db = DatabaseService()
        
        # Migrar alunos
        alunos = Aluno.objects.all()
        for aluno in alunos:
            # Converter o objeto aluno em um dicionário serializável
            aluno_dict = model_to_dict(aluno)
            
            # Gerar um novo UUID para cada aluno
            aluno_dict['id'] = str(uuid.uuid4())
            
            # Converter campos de data para string
            if aluno_dict.get('data_nascimento'):
                aluno_dict['data_nascimento'] = aluno_dict['data_nascimento'].strftime('%Y-%m-%d')
            if aluno_dict.get('data_matricula'):
                aluno_dict['data_matricula'] = aluno_dict['data_matricula'].strftime('%Y-%m-%d')
            
            # Remover campos não serializáveis
            if 'foto' in aluno_dict:
                del aluno_dict['foto']
                
            try:
                db.create_aluno(aluno_dict)
                self.stdout.write(self.style.SUCCESS(f'Aluno {aluno.nome} migrado com sucesso!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao migrar aluno {aluno.nome}: {str(e)}'))
            
        # Migrar notas
        notas = Nota.objects.all()
        for nota in notas:
            nota_dict = model_to_dict(nota)
            
            # Converter Decimal para float
            if isinstance(nota_dict['valor'], Decimal):
                nota_dict['valor'] = float(nota_dict['valor'])
            
            # Converter campos de data para string
            if nota_dict.get('data'):
                nota_dict['data'] = nota_dict['data'].strftime('%Y-%m-%d')
                
            try:
                db.create_nota(nota_dict)
                self.stdout.write(self.style.SUCCESS(f'Nota do aluno {nota.aluno.nome} migrada com sucesso!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao migrar nota: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Migração concluída com sucesso!'))