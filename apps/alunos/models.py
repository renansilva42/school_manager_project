from django.db import models

class Aluno(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    data_nascimento = models.DateField()
    serie = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='fotos_alunos', blank=True, null=True)
    dados_adicionais = models.TextField(blank=True, null=True)

class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='notas')
    disciplina = models.CharField(max_length=50)
    valor = models.DecimalField(max_digits=4, decimal_places=2)
    data = models.DateField(auto_now_add=True)