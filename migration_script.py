import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

from apps.alunos.models import Aluno

def migrate_data():
    alunos = Aluno.objects.all()
    
    for aluno in alunos:
        # Determinar o nível com base no ano
        if aluno.ano in ['3', '4', '5']:
            aluno.nivel = 'EFI'
        else:
            aluno.nivel = 'EFF'
        
        # Verificar se a combinação de turno, nível e ano é válida
        if aluno.nivel == 'EFI' and aluno.turno == 'T':
            # Corrigir: EFI só está disponível no turno da manhã
            aluno.turno = 'M'
        
        if aluno.nivel == 'EFF' and aluno.turno == 'M' and aluno.ano in ['901', '902']:
            # Corrigir: 9º ano só está disponível no turno da tarde
            aluno.turno = 'T'
        
        aluno.save()
    
    print(f"Migração concluída para {alunos.count()} alunos.")

if __name__ == "__main__":
    migrate_data()