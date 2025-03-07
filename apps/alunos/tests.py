from django.test import TestCase
from .forms import AlunoForm, NotaForm, AlunoFilterForm
from .models import Aluno
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date

class FormsTestCase(TestCase):
    def test_aluno_form_valid(self):
        """Testa se o formulário de aluno é válido com dados corretos"""
        form_data = {
            'nome': 'João Silva',
            'nivel': 'EFI',
            'turno': 'M',
            'ano': '3',
            # adicione outros campos obrigatórios
        }
        form = AlunoForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_nota_form_valid(self):
        """Testa se o formulário de nota é válido com dados corretos"""
        form_data = {
            'disciplina': 'Matemática',
            'valor': 8.5
        }
        form = NotaForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_aluno_filter_form_valid(self):
        """Testa se o formulário de filtro é válido com dados corretos"""
        form_data = {
            'nivel': 'EFI',
            'turno': 'M',
            'ano': '3',
            'search': 'João'
        }
        form = AlunoFilterForm(data=form_data)
        self.assertTrue(form.is_valid())
        
def test_aluno_foto_upload(self):
    """Testa o upload de foto do aluno"""
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    # Crie um arquivo de imagem de teste
    image = SimpleUploadedFile(
        name='test_image.jpg',
        content=b'',  # conteúdo vazio para teste
        content_type='image/jpeg'
    )
    
    form_data = {
        'nome': 'João Silva',
        'foto': image,
        # outros campos necessários
    }
    
    form = AlunoForm(data=form_data, files={'foto': image})
    self.assertTrue(form.is_valid())
    
    
class AlunoViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.aluno = Aluno.objects.create(
            nome='Aluno Teste',
            data_nascimento=date(2010, 1, 1),
            # ... outros campos obrigatórios ...
        )
        
    def test_lista_alunos_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('lista_alunos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'alunos/lista_alunos.html')