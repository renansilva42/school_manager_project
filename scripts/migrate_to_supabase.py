# scripts/migrate_to_supabase.py
from django.core.management.base import BaseCommand
from apps.alunos.models import Aluno, Nota
from services.database import SupabaseService

class Command(BaseCommand):
    help = 'Migra dados do SQLite para o Supabase'

    def handle(self, *args, **kwargs):
        db = SupabaseService()
        
        # Migrar alunos
        alunos = Aluno.objects.all()
        for aluno in alunos:
            db.create_aluno(aluno.__dict__)
            
        # Migrar notas
        notas = Nota.objects.all()
        for nota in notas:
            db.create_nota(nota.__dict__)

        self.stdout.write(self.style.SUCCESS('Migração concluída com sucesso!'))