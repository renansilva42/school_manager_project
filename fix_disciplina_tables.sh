#!/bin/bash

# Define the project directory
PROJECT_DIR="/workspace/escola_manager"

# Navigate to the workspace directory
cd /workspace

# Fix the alunos migration conflict
echo "Fixing alunos migration conflict..."
python ${PROJECT_DIR}/fix_alunos_migration.py

# Create the tables in the database
echo "Creating tables in the database..."
python manage.py dbshell < ${PROJECT_DIR}/fix_tables.sql

# Fake the migration to tell Django the tables exist
echo "Faking migrations..."
python manage.py migrate professores --fake

# Check if the models are correctly defined
echo "Checking models..."
python ${PROJECT_DIR}/check_models.py

# Restart the server (if needed)
echo "Done! You may need to restart your server."
echo "Try accessing the admin page again: http://app.escolamanager.com/admin/professores/atribuicaodisciplina/"
