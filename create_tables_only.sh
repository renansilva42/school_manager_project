#!/bin/bash

# Define the project directory
PROJECT_DIR="/workspace/escola_manager"

# Navigate to the workspace directory
cd /workspace

# Create the tables in the database
echo "Creating tables in the database..."
cat > create_tables.sql << 'EOF'
-- Drop the existing tables if they're problematic
DROP TABLE IF EXISTS professores_atribuicaodisciplina;
DROP TABLE IF EXISTS professores_disciplina;

-- Create the Disciplina table
CREATE TABLE professores_disciplina (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    carga_horaria INTEGER NOT NULL,
    descricao TEXT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

-- Create the AtribuicaoDisciplina table
CREATE TABLE professores_atribuicaodisciplina (
    id SERIAL PRIMARY KEY,
    turma VARCHAR(50) NOT NULL,
    ano_letivo INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    professor_id INTEGER NOT NULL REFERENCES professores_professor(id) ON DELETE CASCADE,
    disciplina_id INTEGER NOT NULL REFERENCES professores_disciplina(id) ON DELETE CASCADE,
    UNIQUE(professor_id, disciplina_id, turma, ano_letivo)
);

-- Create index for AtribuicaoDisciplina
CREATE INDEX professor_disciplina_idx 
ON professores_atribuicaodisciplina(professor_id, disciplina_id, turma, ano_letivo);
EOF

python manage.py dbshell < create_tables.sql

echo "Tables created. Try accessing the admin page again: http://app.escolamanager.com/admin/professores/atribuicaodisciplina/"