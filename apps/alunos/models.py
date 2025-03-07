from django.db import models
from django.utils import timezone

class Aluno(models.Model):
    
    ANO_CHOICES = [
        ('3', '3º Ano'),
        ('4', '4º Ano'),
        ('5', '5º Ano'),
        ('6', '6º Ano'),
        ('7', '7º Ano'),
        ('8', '8º Ano'),
        ('901', '9º Ano - Turma 901'),
        ('902', '9º Ano - Turma 902'),
    ]
    
    nome = models.CharField(max_length=255, default='Não informado')
    data_nascimento = models.DateField(default=timezone.now)
    cpf = models.CharField(max_length=14, default='Não informado')
    rg = models.CharField(max_length=20, default='Não informado')
    foto_url = models.URLField(max_length=500, null=True, blank=True)
    nivel = models.CharField(max_length=3, choices=[
        ('EFI', 'Ensino Fundamental Anos Iniciais'),
        ('EFF', 'Ensino Fundamental Anos Finais'),
    ], default='EFI')
    turno = models.CharField(max_length=1, choices=[
        ('M', 'Manhã'),
        ('T', 'Tarde'),
    ], default='M')
    ano = models.CharField(
        max_length=3,
        choices=ANO_CHOICES,
        default='3'
    )
    
    turma = models.CharField(max_length=10, default='A')
    matricula = models.CharField(max_length=20, unique=True, default='0000')
    email = models.EmailField(unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=15, default='Não informado')
    endereco = models.CharField(max_length=255, default='Não informado')
    cidade = models.CharField(max_length=100, default='Não informado')
    uf = models.CharField(max_length=2, default='SP')
    nome_responsavel1 = models.CharField(max_length=255, default='Não informado')
    telefone_responsavel1 = models.CharField(max_length=15, default='Não informado')
    nome_responsavel2 = models.CharField(max_length=255, blank=True, null=True)
    telefone_responsavel2 = models.CharField(max_length=15, blank=True, null=True)
    data_matricula = models.DateField(default=timezone.now)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    disciplina = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=4, decimal_places=2)
    data = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.aluno.nome} - {self.disciplina}: {self.valor}"