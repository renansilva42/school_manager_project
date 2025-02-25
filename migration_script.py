import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

from apps.alunos.models import Aluno

def migrate_data():
    alunos = Aluno.objects.all()
    
    for aluno in alunos:
        # Lógica para determinar o turno e o ano com base na série existente
        # Exemplo simples:
        if '6' in aluno.serie:
            aluno.ano = '6'
        elif '7' in aluno.serie:
            aluno.ano = '7'
        elif '8' in aluno.serie:
            aluno.ano = '8'
        elif '901' in aluno.serie:
            aluno.ano = '901'
        elif '9' in aluno.serie:
            aluno.ano = '902'
        
        # Determinar o turno (exemplo simples)
        if 'manhã' in aluno.serie.lower():
            aluno.turno = 'M'
        else:
            aluno.turno = 'T'
        
        aluno.save()
    
    print(f"Migração concluída para {alunos.count()} alunos.")

if __name__ == "__main__":
    migrate_data()