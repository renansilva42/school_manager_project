# migration_script.py

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

from apps.alunos.models import Aluno

def migrate_data():
    # Get all students using the custom manager
    response = Aluno.objects.all()  # This returns the Supabase response
    
    if not hasattr(response, 'data'):
        print("No data returned from Supabase")
        return
        
    alunos_data = response.data
    
    count = 0
    for aluno_data in alunos_data:
        # Get the required fields
        ano = aluno_data.get('ano')
        nivel = aluno_data.get('nivel')
        turno = aluno_data.get('turno')
        id = aluno_data.get('id')
        
        if not all([ano, nivel, turno, id]):
            continue
            
        # Prepare the update data
        update_data = {}
        
        # Rule 1: Update nivel based on ano
        if ano in ['3', '4', '5']:
            update_data['nivel'] = 'EFI'
        else:
            update_data['nivel'] = 'EFF'
        
        # Rule 2: Update turno for EFI students
        if nivel == 'EFI' and turno == 'T':
            update_data['turno'] = 'M'
        
        # Rule 3: Update turno for specific EFF classes
        if nivel == 'EFF' and turno == 'M' and ano in ['901', '902']:
            update_data['turno'] = 'T'
        
        # Only update if there are changes
        if update_data:
            try:
                # Use the custom manager's update method
                response = Aluno.objects.update(id, update_data)
                if response and hasattr(response, 'data'):
                    count += 1
            except Exception as e:
                print(f"Error updating aluno {id}: {str(e)}")
    
    print(f"Migração concluída para {count} alunos.")

if __name__ == "__main__":
    migrate_data()