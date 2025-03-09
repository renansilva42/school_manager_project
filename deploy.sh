#!/bin/bash

# Executar migrações e criar superusuário
python deploy.py

# Iniciar a aplicação
gunicorn escola_manager.wsgi:application