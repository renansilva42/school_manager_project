from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

def validate_image(fieldfile_obj):
    filesize = fieldfile_obj.size
    megabyte_limit = 5.0
    if filesize > megabyte_limit * 1024 * 1024:
        raise ValidationError(f"Tamanho máximo da imagem é {megabyte_limit}MB")

class Aluno(models.Model):
    """
    Model representing a student in the school management system.
    Includes personal information, academic details, and contact information.
    """
    
    # Choice Constants
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
    
    NIVEL_CHOICES = [
        ('EFI', 'Ensino Fundamental Anos Iniciais'),
        ('EFF', 'Ensino Fundamental Anos Finais'),
    ]
    
    TURNO_CHOICES = [
        ('M', 'Manhã'),
        ('T', 'Tarde'),
    ]


    phone_regex = RegexValidator(
        regex=r'^\(\d{2}\) \d{4,5}-\d{4}$',
        message="Formato do telefone deve ser: (99) 99999-9999"
    )
    
    cpf_regex = RegexValidator(
        regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
        message="Formato do CPF deve ser: 999.999.999-99"
    )

   # Fields
    foto = models.ImageField(
    upload_to='alunos/fotos/',
    null=True,
    blank=True,
    verbose_name='Foto do Aluno',
    validators=[validate_image],
    help_text='Tamanho máximo permitido: 5MB'
    )
    # Personal Information
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome Completo",
        help_text="Digite o nome completo do aluno"
    )
    data_nascimento = models.DateField(
        verbose_name="Data de Nascimento",
        help_text="Data de nascimento do aluno"
    )
    cpf = models.CharField(
    max_length=14,
    validators=[cpf_regex],
    unique=True,
    verbose_name="CPF",
    help_text="CPF no formato: 999.999.999-99",
    null=True,  # Adicione esta linha
    blank=True  # Adicione esta linha
)
    
    rg = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="RG",
        help_text="Número do RG"
    )
    foto_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Foto",
        help_text="URL da foto do aluno"
    )

    # Academic Information
    nivel = models.CharField(
        max_length=3,
        choices=NIVEL_CHOICES,
        default='EFI',
        verbose_name="Nível de Ensino"
    )
    turno = models.CharField(
        max_length=1,
        choices=TURNO_CHOICES,
        default='M',
        verbose_name="Turno"
    )
    ano = models.CharField(
        max_length=3,
        choices=ANO_CHOICES,
        default='3',
        verbose_name="Ano/Série"
    )
    turma = models.CharField(
        max_length=10,
        default="Não informada",
        verbose_name="Turma"
    )
    matricula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Matrícula"
    )

    # Contact Information
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="E-mail"
    )
    telefone = models.CharField(
        max_length=15,
        validators=[phone_regex],
        default="(00) 00000-0000",
        verbose_name="Telefone"
    )
    endereco = models.CharField(
        max_length=255,
        default="Não informado",
        verbose_name="Endereço"
    )
    cidade = models.CharField(
        max_length=100,
        default="Não informada",
        verbose_name="Cidade"
    )
    uf = models.CharField(
        max_length=2,
        default="NA",
        verbose_name="UF"
    )

    # Guardian Information
    nome_responsavel1 = models.CharField(
        max_length=255,
        default="Não informado",
        verbose_name="Nome do Responsável 1"
    )
    telefone_responsavel1 = models.CharField(
        max_length=15,
        validators=[phone_regex],
        default="(00) 00000-0000",
        verbose_name="Telefone do Responsável 1"
    )
    nome_responsavel2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nome do Responsável 2"
    )
    telefone_responsavel2 = models.CharField(
        max_length=15,
        validators=[phone_regex],
        blank=True,
        null=True,
        verbose_name="Telefone do Responsável 2"
    )

    # Additional Information
    data_matricula = models.DateField(
        default=timezone.now,
        verbose_name="Data da Matrícula"
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Criado em")
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['matricula']),
            models.Index(fields=['cpf']),
        ]

    def __str__(self):
        return f"{self.nome} - Matrícula: {self.matricula}"

    def clean(self):
        super().clean()
        errors = {}
        
        # Validação de idade
        if self.data_nascimento:
            idade = (timezone.now().date() - self.data_nascimento).days / 365
            if idade < 5 or idade > 18:
                errors['data_nascimento'] = _('Idade deve estar entre 5 e 18 anos')
        
        # Validação de nível e turno
        if self.nivel == 'EFI' and self.turno != 'M':
            errors['turno'] = _('Ensino Fundamental Anos Iniciais só está disponível no turno da manhã')
        
        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        """Get the absolute URL for the student detail page."""
        from django.urls import reverse
        return reverse('detalhe_aluno', args=[str(self.id)])

    def get_idade(self):
        """Calculate and return the student's age."""
        today = timezone.now().date()
        return (today - self.data_nascimento).days // 365

    def get_media_geral(self):
        """Calculate and return the student's overall grade average."""
        notas = self.nota_set.all()
        if not notas:
            return 0
        return sum(nota.valor for nota in notas) / len(notas)

class Nota(models.Model):
    """
    Model representing a grade/score for a student in a specific subject.
    """
    
    DISCIPLINA_CHOICES = [
        ('PORT', 'Português'),
        ('MAT', 'Matemática'),
        ('CIEN', 'Ciências'),
        ('HIST', 'História'),
        ('GEO', 'Geografia'),
        ('ING', 'Inglês'),
        ('ART', 'Artes'),
        ('EDF', 'Educação Física'),
    ]

    BIMESTRE_CHOICES = [
        (1, '1º Bimestre'),
        (2, '2º Bimestre'),
        (3, '3º Bimestre'),
        (4, '4º Bimestre'),
    ]

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        verbose_name="Aluno"
    )
    disciplina = models.CharField(
        max_length=4,
        choices=DISCIPLINA_CHOICES,
        verbose_name="Disciplina"
    )
    valor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ],
        verbose_name="Nota"
    )
    bimestre = models.IntegerField(
        choices=BIMESTRE_CHOICES,
        default=1,
        verbose_name="Bimestre"
    )
    data = models.DateField(
        default=timezone.now,
        verbose_name="Data de Lançamento"
    )
    observacao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observação"
    )

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        ordering = ['aluno', 'disciplina', 'bimestre']
        unique_together = ['aluno', 'disciplina', 'bimestre']
        indexes = [
            models.Index(fields=['aluno', 'disciplina']),
        ]

    def __str__(self):
        return f"{self.aluno.nome} - {self.get_disciplina_display()}: {self.valor} ({self.get_bimestre_display()})"

    def clean(self):
        """Validate the model data."""
        if self.valor < 0 or self.valor > 10:
            raise ValidationError('A nota deve estar entre 0 e 10')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)