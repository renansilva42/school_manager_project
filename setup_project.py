import os

def create_project_structure():
    directories = [
        'escola_manager',
        'escola_manager/escola_manager',
        'escola_manager/apps',
        'escola_manager/apps/alunos',
        'escola_manager/apps/usuarios',
        'escola_manager/apps/relatorios',
        'escola_manager/apps/chatbot',
        'escola_manager/templates',
        'escola_manager/templates/alunos',
        'escola_manager/templates/usuarios',
        'escola_manager/templates/relatorios',
        'escola_manager/templates/chatbot',
        'escola_manager/static',
        'escola_manager/static/css',
        'escola_manager/static/js',
        'escola_manager/media',
        'escola_manager/media/fotos_alunos',
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    files = [
        ('escola_manager/manage.py', ''),
        ('escola_manager/escola_manager/__init__.py', ''),
        ('escola_manager/escola_manager/settings.py', ''),
        ('escola_manager/escola_manager/urls.py', ''),
        ('escola_manager/escola_manager/wsgi.py', ''),
        ('escola_manager/apps/__init__.py', ''),
        ('escola_manager/apps/alunos/__init__.py', ''),
        ('escola_manager/apps/alunos/models.py', ''),
        ('escola_manager/apps/alunos/views.py', ''),
        ('escola_manager/apps/alunos/forms.py', ''),
        ('escola_manager/apps/alunos/urls.py', ''),
        ('escola_manager/apps/alunos/tests.py', ''),
        ('escola_manager/apps/usuarios/__init__.py', ''),
        ('escola_manager/apps/usuarios/models.py', ''),
        ('escola_manager/apps/usuarios/views.py', ''),
        ('escola_manager/apps/usuarios/urls.py', ''),
        ('escola_manager/apps/relatorios/__init__.py', ''),
        ('escola_manager/apps/relatorios/views.py', ''),
        ('escola_manager/apps/relatorios/urls.py', ''),
        ('escola_manager/apps/chatbot/__init__.py', ''),
        ('escola_manager/apps/chatbot/views.py', ''),
        ('escola_manager/apps/chatbot/urls.py', ''),
        ('escola_manager/apps/chatbot/utils.py', ''),
        ('escola_manager/templates/base.html', ''),
        ('escola_manager/templates/alunos/lista_alunos.html', ''),
        ('escola_manager/templates/alunos/detalhe_aluno.html', ''),
        ('escola_manager/templates/alunos/cadastrar_aluno.html', ''),
        ('escola_manager/templates/alunos/editar_aluno.html', ''),
        ('escola_manager/templates/alunos/adicionar_nota.html', ''),
        ('escola_manager/templates/usuarios/login.html', ''),
        ('escola_manager/templates/relatorios/relatorios.html', ''),
        ('escola_manager/templates/relatorios/media_por_serie.html', ''),
        ('escola_manager/templates/relatorios/alunos_por_serie.html', ''),
        ('escola_manager/templates/relatorios/notas_baixas.html', ''),
        ('escola_manager/templates/chatbot/chatbot.html', ''),
        ('escola_manager/requirements.txt', ''),
        ('escola_manager/setup_project.py', open(__file__, 'r').read()),
    ]
    for file_path, content in files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == '__main__':
    create_project_structure()
    print("Estrutura do projeto criada com sucesso! Execute os seguintes passos:")
    print("1. Crie e ative o ambiente virtual: `python -m venv venv` e `source venv/bin/activate` (Linux/Mac) ou `venv\\Scripts\\activate` (Windows)")
    print("2. Instale as dependências: `pip install -r requirements.txt`")
    print("3. Crie um arquivo .env com as variáveis de ambiente necessárias.")