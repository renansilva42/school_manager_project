import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

from apps.alunos.models import Aluno

def migrate_data():
    alunos_data = Aluno.objects.filter()  # Isso retorna os dados do Supabase
    
    for aluno_data in alunos_data.data:  # Acesse .data para obter a lista de registros
        # Acesse os campos como um dicionário
        ano = aluno_data.get('ano')
        nivel = aluno_data.get('nivel')
        turno = aluno_data.get('turno')
        id = aluno_data.get('id')
        
        # Prepare os dados para atualização
        update_data = {}
        
        if ano in ['3', '4', '5']:
            update_data['nivel'] = 'EFI'
        else:
            update_data['nivel'] = 'EFF'
        
        if nivel == 'EFI' and turno == 'T':
            update_data['turno'] = 'M'
        
        if nivel == 'EFF' and turno == 'M' and ano in ['901', '902']:
            update_data['turno'] = 'T'
        
        # Se houver alterações, atualize o registro
        if update_data:
            Aluno.objects.update(id, update_data)
    
    print(f"Migração concluída para {len(alunos_data.data)} alunos.")

if __name__ == "__main__":
    migrate_data()