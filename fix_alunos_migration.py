#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

from django.db import connections
from django.db.migrations.recorder import MigrationRecorder

def fix_migration_conflict():
    """Fix migration conflict by removing conflicting migrations from the database"""
    connection = connections['default']
    recorder = MigrationRecorder(connection)
    
    # Get all applied migrations
    applied_migrations = recorder.applied_migrations()
    
    # Find conflicting migrations
    conflicting_migrations = [
        ('alunos', '0002_alter_data_matricula_nullable'),
        ('alunos', '0003_alter_aluno_id'),
        ('alunos', 'make_data_nascimento_nullable')
    ]
    
    # Check which ones are applied
    applied_conflicting = []
    for app, name in conflicting_migrations:
        if (app, name) in applied_migrations:
            applied_conflicting.append((app, name))
    
    if not applied_conflicting:
        print("No conflicting migrations found in the database.")
        return
    
    print(f"Found {len(applied_conflicting)} conflicting migrations:")
    for app, name in applied_conflicting:
        print(f"  - {app}.{name}")
    
    # Keep only the latest migration
    latest_migration = applied_conflicting[-1]
    to_remove = applied_conflicting[:-1]
    
    print(f"\nKeeping latest migration: {latest_migration[0]}.{latest_migration[1]}")
    print(f"Removing {len(to_remove)} conflicting migrations:")
    
    # Remove conflicting migrations
    for app, name in to_remove:
        print(f"  - Removing {app}.{name}...")
        recorder.record_unapplied(app, name)
        print(f"  - {app}.{name} removed.")
    
    print("\nMigration conflict resolved.")

if __name__ == "__main__":
    fix_migration_conflict()