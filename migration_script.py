# migration_script.py

import os
import django
from services.database import SupabaseService
import uuid
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

def generate_safe_id():
    """Gera um ID seguro que não excederá o limite do SQLite"""
    return str(uuid.uuid4())

def migrate_data():
    # Create an instance of SupabaseService
    supabase_service = SupabaseService()
    print("Connecting to Supabase...")
    
    try:
        # Get all students using the service
        response = supabase_service.list_alunos()
        print(f"Response received: {response}")
        
        if not response or not hasattr(response, 'data'):
            print("No data returned from Supabase")
            return
            
        alunos_data = response.data
        
        count = 0
        for aluno_data in alunos_data:
            # Get the required fields
            ano = aluno_data.get('ano')
            nivel = aluno_data.get('nivel')
            turno = aluno_data.get('turno')
            
            # Gerar um novo ID seguro
            id = generate_safe_id()
            
            if not all([ano, nivel, turno]):
                continue
                
            # Prepare the update data
            update_data = {
                'id': id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'version': 1  # Começando com versão 1
            }
            
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
            
            # Adicionar outros campos do aluno ao update_data
            for key, value in aluno_data.items():
                if key not in update_data and value is not None:
                    update_data[key] = value
            
            try:
                # Use the service's update method
                response = supabase_service.update_aluno(id, update_data)
                if response and hasattr(response, 'data'):
                    count += 1
                    print(f"Updated aluno {id} with data: {update_data}")
            except Exception as e:
                print(f"Error updating aluno {id}: {str(e)}")
                continue
        
        print(f"Migração concluída para {count} alunos.")

    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise e

if __name__ == "__main__":
    migrate_data()