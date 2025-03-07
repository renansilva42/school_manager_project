from django.test import TestCase
from .forms import AlunoForm, NotaForm, AlunoFilterForm
from .models import Aluno

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