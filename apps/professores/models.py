# /apps/professores/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class Disciplina(models.Model):
    nome = models.CharField(max_length=100)
    carga_horaria = models.IntegerField()
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name_plural = 'Disciplinas'
        verbose_name = 'Disciplina'


class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    data_nascimento = models.DateField(null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name_plural = 'Professores'
        verbose_name = 'Professor'


class AtribuicaoDisciplina(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    turma = models.CharField(max_length=50)
    ano_letivo = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Atribuições de Disciplinas'
        verbose_name = 'Atribuição de Disciplina'
        indexes = [
            models.Index(fields=['professor', 'disciplina', 'turma', 'ano_letivo'], name='professor_disciplina_idx'),
        ]
        unique_together = ['professor', 'disciplina', 'turma', 'ano_letivo']

    def clean(self):
        # Verificar se já existe uma atribuição similar
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


class DisponibilidadeHorario(models.Model):
    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='disponibilidades')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    
    class Meta:
        verbose_name = 'Disponibilidade de Horário'
        verbose_name_plural = 'Disponibilidades de Horário'
        ordering = ['dia_semana', 'hora_inicio']
    
    def __str__(self):
        return f"{self.professor.nome} - {self.get_dia_semana_display()} ({self.hora_inicio} - {self.hora_fim})"
    
    def clean(self):
        # Verificar se hora_inicio é anterior a hora_fim
        if self.hora_inicio and self.hora_fim and self.hora_inicio >= self.hora_fim:
            raise ValidationError('A hora de início deve ser anterior à hora de fim.')
        
        # Verificar sobreposição de horários
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
