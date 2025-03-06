import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

from apps.alunos.models import Aluno

def migrate_data():
    alunos = Aluno.objects.filter()  # Use filter() instead of all()
    
    for aluno in alunos:
        # Rest of your migration logic
        if aluno.ano in ['3', '4', '5']:
            aluno.nivel = 'EFI'
        else:
            aluno.nivel = 'EFF'
        
        if aluno.nivel == 'EFI' and aluno.turno == 'T':
            aluno.turno = 'M'
        
        if aluno.nivel == 'EFF' and aluno.turno == 'M' and aluno.ano in ['901', '902']:
            aluno.turno = 'T'
        
        aluno.save()
    
    print(f"Migração concluída para {len(alunos)} alunos.")

if __name__ == "__main__":
    migrate_data()