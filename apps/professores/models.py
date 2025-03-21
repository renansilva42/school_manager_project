from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

phone_regex = RegexValidator(
    regex=r'^\(\d{2}\) \d{5}-\d{4}$',
    message="O número deve estar no formato: '(99) 99999-9999'"
)

class Professor(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(validators=[phone_regex], max_length=15, blank=True)
    formacao = models.CharField(max_length=100)
    especialidade = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='professores/', blank=True, null=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'
        ordering = ['nome']

    def __str__(self):
        return self.nome

class AtribuicaoDisciplina(models.Model):
    professor = models.ForeignKey('Professor', on_delete=models.CASCADE)
    disciplina = models.CharField(max_length=50)
    turma = models.CharField(max_length=50)
    ano_letivo = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Atribuição de Disciplina'
        verbose_name_plural = 'Atribuições de Disciplinas'
        unique_together = ['professor', 'disciplina', 'turma', 'ano_letivo']

    def __str__(self):
        return f"{self.professor.nome} - {self.disciplina} - {self.turma}"

class DisponibilidadeHorario(models.Model):
    DIAS_SEMANA = [
        ('SEG', 'Segunda-feira'),
        ('TER', 'Terça-feira'),
        ('QUA', 'Quarta-feira'),
        ('QUI', 'Quinta-feira'),
        ('SEX', 'Sexta-feira'),
    ]

    professor = models.ForeignKey('Professor', on_delete=models.CASCADE)
    dia_semana = models.CharField(max_length=3, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    class Meta:
        verbose_name = 'Disponibilidade de Horário'
        verbose_name_plural = 'Disponibilidades de Horários'
        unique_together = ['professor', 'dia_semana', 'hora_inicio']

    def __str__(self):
        return f"{self.professor.nome} - {self.get_dia_semana_display()} ({self.hora_inicio} - {self.hora_fim})"