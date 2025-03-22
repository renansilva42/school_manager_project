from django.db import models

from django.db import models

class Professor(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    disciplina = models.CharField(max_length=50)

    def __str__(self):
        return self.nome

class SiteSettings(models.Model):
    school_name = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    smtp_server = models.CharField(max_length=100, blank=True, null=True)
    smtp_port = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Configurações do Site'
        verbose_name_plural = 'Configurações do Site'

    def __str__(self):
        return "Configurações do Site"

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class DisponibilidadeHorario(models.Model):
    DIAS_SEMANA = [
        ('SEG', 'Segunda-feira'),
        ('TER', 'Terça-feira'),
        ('QUA', 'Quarta-feira'),
        ('QUI', 'Quinta-feira'),
        ('SEX', 'Sexta-feira'),
    ]

    class Meta:
        verbose_name = 'Configurações do Site'
        verbose_name_plural = 'Configurações do Site'

    def __str__(self):
        return "Configurações do Site"

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

# Define the AtribuicaoDisciplina class
class AtribuicaoDisciplina(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    disciplina = models.CharField(max_length=50)
    turma = models.CharField(max_length=50)
    horario = models.DateTimeField()

    def __str__(self):
        return f"{self.professor.nome} - {self.disciplina} - {self.turma}"