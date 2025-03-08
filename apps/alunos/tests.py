from django.test import TestCase, Client
from django.urls import reverse
from apps.alunos.models import Aluno
from django.contrib.auth.models import User

class URLTests(TestCase):
    def setUp(self):
        # Criar usuário para testes
        self.user = User.objects.create_user(
            username='testuser',
            password='12345'
        )
        self.client = Client()
        self.client.login(username='testuser', password='12345')
        
        # Criar aluno para testes
        self.aluno = Aluno.objects.create(
            nome="Aluno Teste",
            matricula="12345",
            nivel="EFF"
        )

    def test_lista_alunos_url(self):
        url = reverse('alunos:lista')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detalhe_aluno_url(self):
        url = reverse('alunos:detalhe', kwargs={'pk': self.aluno.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cadastrar_aluno_url(self):
        url = reverse('alunos:cadastrar')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)