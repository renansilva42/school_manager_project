# /apps/professores/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class Professor(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=15)
    formacao = models.CharField(max_length=100)
    especialidade = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='professores/fotos/', null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class DisponibilidadeHorario(models.Model):
    DIAS_SEMANA = [
        ('SEG', 'Segunda-feira'),
        ('TER', 'Terça-feira'),
        ('QUA', 'Quarta-feira'),
        ('QUI', 'Quinta-feira'),
        ('SEX', 'Sexta-feira'),
        ('SAB', 'Sábado'),
        ('DOM', 'Domingo'),
    ]
    
    professor = models.ForeignKey('Professor', on_delete=models.CASCADE, related_name='disponibilidades')
    dia_semana = models.CharField(max_length=3, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    
    class Meta:
        verbose_name = 'Disponibilidade de Horário'
        verbose_name_plural = 'Disponibilidades de Horário'
        
    def __str__(self):
        return f"{self.professor} - {self.get_dia_semana_display()} {self.hora_inicio} - {self.hora_fim}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        sobreposicao = DisponibilidadeHorario.objects.filter(
            professor=self.professor,
            dia_semana=self.dia_semana,
        ).exclude(id=self.id)

        for horario in sobreposicao:
            if (self.hora_inicio <= horario.hora_fim and 
                self.hora_fim >= horario.hora_inicio):
                raise ValidationError(
                    'Existe sobreposição de horário com outro registro.'
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
class SiteSettings(models.Model):
    # Add your site settings fields here
    
    @classmethod
    def get_settings(cls):
        # Implement your settings retrieval logic
        return cls.objects.first()  # or however you want to retrieve settings
    

class Disciplina(models.Model):
    nome = models.CharField(max_length=100)
    carga_horaria = models.IntegerField()
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class AtribuicaoDisciplina(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    turma = models.CharField(max_length=50)
    ano_letivo = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['professor', 'disciplina', 'turma', 'ano_letivo'], name='professor_disciplina_idx'),
        ]
        unique_together = ['professor', 'disciplina', 'turma', 'ano_letivo']

    def clean(self):
        from django.core.exceptions import ValidationError
        if AtribuicaoDisciplina.objects.filter(
            professor=self.professor,
            disciplina=self.disciplina,
            turma=self.turma,
            ano_letivo=self.ano_letivo
        ).exclude(id=self.id).exists():
            raise ValidationError('Já existe uma atribuição similar para este professor.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.professor} - {self.disciplina} - {self.turma} ({self.ano_letivo})"
