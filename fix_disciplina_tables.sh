#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Create the tables in the database
echo "Creating tables in the database..."
python manage.py dbshell < fix_tables.sql

# Fake the migration to tell Django the tables exist
echo "Faking migrations..."
python manage.py migrate professores --fake

# Check if the models are correctly defined
echo "Checking models..."
python check_models.py

# Restart the server (if needed)
echo "Done! You may need to restart your server."
echo "Try accessing the admin page again: http://app.escolamanager.com/admin/professores/atribuicaodisciplina/"