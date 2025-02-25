# apps/alunos/models.py
from django.db import models

class Aluno(models.Model):
    TURNO_CHOICES = [
        ('M', 'Manhã'),
        ('T', 'Tarde'),
    ]
    
    ANO_CHOICES = [
        ('6', '6º Ano'),
        ('7', '7º Ano'),
        ('8', '8º Ano'),
        ('901', '9º Ano - Turma 901'),
        ('902', '9º Ano - Turma 902'),
    ]
    
    nome = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    data_nascimento = models.DateField()
    # Manteremos o campo série para compatibilidade com dados existentes
    serie = models.CharField(max_length=20)
    # Novos campos para organização
    turno = models.CharField(max_length=1, choices=TURNO_CHOICES, default='M')
    ano = models.CharField(max_length=4, choices=ANO_CHOICES, default='6')
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='fotos_alunos', blank=True, null=True)
    dados_adicionais = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.nome} - {self.get_ano_display()} ({self.get_turno_display()})"

class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='notas')
    disciplina = models.CharField(max_length=50)
    valor = models.DecimalField(max_digits=4, decimal_places=2)
    data = models.DateField(auto_now_add=True)