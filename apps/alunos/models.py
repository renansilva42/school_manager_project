# apps/alunos/models.py
from django.db import models

class Aluno(models.Model):
    TURNO_CHOICES = [
        ('M', 'Manhã'),
        ('T', 'Tarde'),
    ]
    
    NIVEL_CHOICES = [
        ('EFI', 'Ensino Fundamental Anos Iniciais'),
        ('EFF', 'Ensino Fundamental Anos Finais'),
    ]
    
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
    
    nome = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    data_nascimento = models.DateField()
    serie = models.CharField(max_length=20)
    nivel = models.CharField(max_length=3, choices=NIVEL_CHOICES, default='EFF')
    turno = models.CharField(max_length=1, choices=TURNO_CHOICES, default='M')
    ano = models.CharField(max_length=4, choices=ANO_CHOICES, default='6')
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='fotos_alunos', blank=True, null=True)
    dados_adicionais = models.TextField(blank=True, null=True)
    
    # Add the missing fields
    cpf = models.CharField(max_length=14, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    turma = models.CharField(max_length=10, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    nome_responsavel1 = models.CharField(max_length=100, blank=True, null=True)
    telefone_responsavel1 = models.CharField(max_length=20, blank=True, null=True)
    nome_responsavel2 = models.CharField(max_length=100, blank=True, null=True)
    telefone_responsavel2 = models.CharField(max_length=20, blank=True, null=True)
    data_matricula = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.nome} - {self.get_ano_display()} ({self.get_turno_display()})"

class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='notas')
    disciplina = models.CharField(max_length=50)
    valor = models.DecimalField(max_digits=4, decimal_places=2)
    data = models.DateField(auto_now_add=True)