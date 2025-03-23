#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escola_manager.settings')
django.setup()

from django.apps import apps

# Check if the models are registered
try:
    disciplina_model = apps.get_model('professores', 'Disciplina')
    print(f"Disciplina model found: {disciplina_model}")
    print(f"Table name: {disciplina_model._meta.db_table}")
    print("Fields:")
    for field in disciplina_model._meta.fields:
        print(f"  - {field.name}: {field.__class__.__name__}")
except LookupError:
    print("Disciplina model not found in the professores app")

try:
    atribuicao_model = apps.get_model('professores', 'AtribuicaoDisciplina')
    print(f"\nAtribuicaoDisciplina model found: {atribuicao_model}")
    print(f"Table name: {atribuicao_model._meta.db_table}")
    print("Fields:")
    for field in atribuicao_model._meta.fields:
        print(f"  - {field.name}: {field.__class__.__name__}")
except LookupError:
    print("\nAtribuicaoDisciplina model not found in the professores app")

# Check if the models are registered in admin
from django.contrib.admin.sites import site
print("\nModels registered in admin:")
for model, admin_obj in site._registry.items():
    print(f"  - {model._meta.app_label}.{model.__name__}")