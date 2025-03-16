#!/usr/bin/env python
import os
import sys
import shutil
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

def apply_changes():
    """
    Apply the changes to make the birth date field nullable
    """
    print("Applying changes to make the birth date field nullable...")
    
    # 1. Replace the original files with the updated ones
    try:
        # Replace database.py
        if os.path.exists('services/database_updated.py'):
            shutil.copy('services/database_updated.py', 'services/database.py')
            print("✅ Updated database.py")
        else:
            print("❌ services/database_updated.py not found")
        
        # Replace views.py
        if os.path.exists('apps/alunos/views_updated.py'):
            shutil.copy('apps/alunos/views_updated.py', 'apps/alunos/views.py')
            print("✅ Updated views.py")
        else:
            print("❌ apps/alunos/views_updated.py not found")
    except Exception as e:
        print(f"❌ Error replacing files: {str(e)}")
    
    # 2. Apply the migration
    try:
        from django.core.management import call_command
        
        # Make sure the migration file is properly named
        migration_dir = 'apps/alunos/migrations'
        migration_file = 'make_data_nascimento_nullable.py'
        migration_path = os.path.join(migration_dir, migration_file)
        
        if os.path.exists(migration_path):
            # Rename the migration file to follow Django's naming convention
            # Find the latest migration number
            migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.py') and f.startswith('0')]
            if migration_files:
                latest_num = max([int(f.split('_')[0]) for f in migration_files if f.split('_')[0].isdigit()])
                new_num = latest_num + 1
                new_name = f"{new_num:04d}_make_data_nascimento_nullable.py"
                new_path = os.path.join(migration_dir, new_name)
                shutil.copy(migration_path, new_path)
                print(f"✅ Renamed migration file to {new_name}")
            else:
                print("❌ No existing migrations found to determine numbering")
        else:
            print(f"❌ Migration file {migration_path} not found")
        
        # Apply migrations
        call_command('migrate')
        print("✅ Applied migrations")
        
    except Exception as e:
        print(f"❌ Error applying migration: {str(e)}")
    
    print("\nChanges applied successfully. The birth date field is now optional.")
    print("You may need to restart your application for the changes to take effect.")

if __name__ == "__main__":
    apply_changes()
