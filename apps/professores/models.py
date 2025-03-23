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


class SiteSettings(models.Model):
    # Add your site settings fields here
    
    @classmethod
    def get_settings(cls):
        # Implement your settings retrieval logic
        return cls.objects.first()  # or however you want to retrieve settings
