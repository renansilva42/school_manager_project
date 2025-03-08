from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image
import re
import os

phone_regex = RegexValidator(
        regex=r'^\(\d{2}\) \d{4,5}-\d{4}$',
        message="Formato do telefone deve ser: (99) 99999-9999"
    )
    
class AnoChoices(models.TextChoices):
        ANO_3 = '3', '3º Ano'
        ANO_4 = '4', '4º Ano'
        ANO_5 = '5', '5º Ano'
        ANO_6 = '6', '6º Ano'
        ANO_7 = '7', '7º Ano'
        ANO_8 = '8', '8º Ano'
        ANO_901 = '901', '9º Ano - Turma 901'
        ANO_902 = '902', '9º Ano - Turma 902'   

class AlunoManager(models.Manager):
    """Custom manager for Aluno model with additional query methods"""
    
    def ativos(self):
        return self.filter(ativo=True)
    
    def por_nivel(self, nivel):
        return self.filter(nivel=nivel)
    
    def por_turno(self, turno):
        return self.filter(turno=turno)
        
    def busca_avancada(self, **kwargs):
        queryset = self.all()
        if kwargs.get('nome'):
            queryset = queryset.filter(nome__icontains=kwargs['nome'])
        if kwargs.get('nivel'):
            queryset = queryset.filter(nivel=kwargs['nivel'])
        if kwargs.get('turno'):
            queryset = queryset.filter(turno=kwargs['turno'])
        return queryset

def validate_image(fieldfile_obj):
    megabyte_limit = 5.0
    if hasattr(fieldfile_obj, 'size'):
        if fieldfile_obj.size > megabyte_limit * 1024 * 1024:
            raise ValidationError(f"Imagem muito grande. O tamanho máximo permitido é {megabyte_limit}MB")
    elif hasattr(fieldfile_obj, 'getbuffer'):
        if fieldfile_obj.getbuffer().nbytes > megabyte_limit * 1024 * 1024:
            raise ValidationError(f"Imagem muito grande. O tamanho máximo permitido é {megabyte_limit}MB")
        
    # Validate file size
    megabyte_limit = 5.0
    if fieldfile_obj.size > megabyte_limit * 1024 * 1024:
        raise ValidationError(f"Tamanho máximo da imagem é {megabyte_limit}MB")
        
    # Validate image format
    valid_formats = ['image/jpeg', 'image/png', 'image/gif']
    file_type = fieldfile_obj.content_type
    if file_type not in valid_formats:
        raise ValidationError("Formato de imagem não suportado. Use JPEG, PNG ou GIF.")

def aluno_foto_path(instance, filename):
    """Generate path for student photos"""
    ext = filename.split('.')[-1]
    return f'alunos/fotos/{instance.matricula}.{ext}'

class Aluno(models.Model):
    """
    Model representing a student in the school management system.
    Includes personal information, academic details, and contact information.
    """
    

    
    class NivelChoices(models.TextChoices):
        EFI = 'EFI', 'Ensino Fundamental Anos Iniciais'
        EFF = 'EFF', 'Ensino Fundamental Anos Finais'
    
    class TurnoChoices(models.TextChoices):
        MANHA = 'M', 'Manhã'
        TARDE = 'T', 'Tarde'


    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    # Validators
    nivel = models.CharField(
        max_length=3,
        choices=NivelChoices.choices,
        verbose_name="Nível",
        help_text="Nível de ensino do aluno"
    )
    
    matricula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Matrícula",
        help_text="Número de matrícula do aluno"
    )
    
    turno = models.CharField(
        max_length=1,
        choices=TurnoChoices.choices,
        verbose_name="Turno",
        help_text="Turno de estudo do aluno"
    )
    
    
    cpf_regex = RegexValidator(
        regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
        message="Formato do CPF deve ser: 999.999.999-99"
    )
    
    nome_regex = RegexValidator(
        regex=r'^[A-Za-zÀ-ÿ\s]*$',
        message="Nome deve conter apenas letras"
    )

    # Version control
    version = models.IntegerField(default=1, editable=False)
    
    # Audit fields
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='alunos_created',
        editable=False
    )
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='alunos_updated',
        editable=False
    )

    # Fields with improved validation and organization
    foto = models.ImageField(
        upload_to=aluno_foto_path,
        null=True,
        blank=True,
        verbose_name='Foto do Aluno',
        validators=[validate_image],
        help_text='Tamanho máximo permitido: 5MB'
    )
    
    # Personal Information with improved validation
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome Completo",
        help_text="Digite o nome completo do aluno",
        validators=[nome_regex]
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
        null=True,
        blank=True
    )
    
    # Informações de Contato
    email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="E-mail"
    )
    telefone = models.CharField(
        max_length=15,
        validators=[phone_regex],
        blank=True,
        verbose_name="Telefone"
    )
    
    # Informações de Endereço
    endereco = models.CharField(
        max_length=255,
        verbose_name="Endereço"
    )
    cidade = models.CharField(
        max_length=100,
        verbose_name="Cidade"
    )
    uf = models.CharField(
        max_length=2,
        verbose_name="UF"
    )
    
    # Informações Acadêmicas
    ano = models.CharField(
        max_length=3,
        choices=AnoChoices.choices,
        verbose_name="Ano"
    )
    
    turma = models.CharField(
        max_length=50,
        verbose_name="Turma"
    )
    data_matricula = models.DateField(
        verbose_name="Data de Matrícula"
    )
    
    # Informações dos Responsáveis
    nome_responsavel1 = models.CharField(
        max_length=255,
        verbose_name="Nome do Responsável 1"
    )
    telefone_responsavel1 = models.CharField(
        max_length=15,
        validators=[phone_regex],
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
    
    # Informações Adicionais
    rg = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="RG"
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    # ... [rest of the fields remain the same but with improved organization]

    # Custom manager
    objects = AlunoManager()

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['matricula']),
            models.Index(fields=['cpf']),
            models.Index(fields=['nivel', 'turno']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['cpf'],
                condition=models.Q(ativo=True),
                name='unique_active_cpf'
            ),
            models.UniqueConstraint(
                fields=['matricula'],
                condition=models.Q(ativo=True),
                name='unique_active_matricula'
            ),
        ]

    def __str__(self):
        return f"{self.nome} - Matrícula: {self.matricula}"

    def clean(self):
        """Enhanced validation logic"""
        super().clean()
        errors = {}
        
        self.validate_idade(errors)
        self.validate_nivel_turno(errors)
        self.validate_unique_fields(errors)
        
        if errors:
            raise ValidationError(errors)

    def validate_idade(self, errors):
        """Validate student age"""
        if self.data_nascimento:
            idade = self.get_idade()
            if idade < 5 or idade > 18:
                errors['data_nascimento'] = _('Idade deve estar entre 5 e 18 anos')

    def validate_nivel_turno(self, errors):
        """Validate level and shift combinations"""
        if self.nivel == self.NivelChoices.EFI and self.turno != self.TurnoChoices.MANHA:
            errors['turno'] = _('Ensino Fundamental Anos Iniciais só está disponível no turno da manhã')

    def validate_unique_fields(self, errors):
        """Validate unique fields"""
        if not self.pk:
            if Aluno.objects.filter(cpf=self.cpf, ativo=True).exists():
                errors['cpf'] = _('CPF já cadastrado')
            if Aluno.objects.filter(matricula=self.matricula, ativo=True).exists():
                errors['matricula'] = _('Matrícula já cadastrada')

    def save(self, *args, **kwargs):
        """Enhanced save method with image processing"""
        if self.pk:
            self.version += 1
            
        # Process photo if present
        if self.foto:
            try:
                img = Image.open(self.foto)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    img.save(self.foto.path)
            except Exception as e:
                raise ValidationError(f"Erro ao processar imagem: {str(e)}")
                
        super().save(*args, **kwargs)

    def get_idade(self):
        """Calculate student's age"""
        if self.data_nascimento:
            today = timezone.now().date()
            return (today - self.data_nascimento).days // 365
        return 0

    def get_media_geral(self):
        """Calculate overall grade average with caching"""
        from django.core.cache import cache
        
        cache_key = f'aluno_media_{self.pk}'
        media = cache.get(cache_key)
        
        if media is None:
            notas = self.nota_set.all()
            if not notas:
                media = 0
            else:
                media = sum(nota.valor for nota in notas) / len(notas)
            cache.set(cache_key, media, timeout=3600)  # Cache for 1 hour
            
        return media

    def delete(self, *args, **kwargs):
        """Soft delete implementation"""
        self.ativo = False
        self.save()

# ... [Nota model remains largely the same with similar improvements]

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
    
    # Contact Information
    email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="E-mail"
    )
    telefone = models.CharField(
        max_length=15,
        validators=[phone_regex],
        blank=True,
        verbose_name="Telefone"
    )
    
    # Address Information
    endereco = models.CharField(
    max_length=255,
    verbose_name="Endereço",
    null=True,
    blank=True
    )
    cidade = models.CharField(
    max_length=100,
    verbose_name="Cidade",
    null=True,
    blank=True
    )
    uf = models.CharField(
    max_length=2,
    verbose_name="UF",
    null=True,
    blank=True
    )
    
    # Academic Information
    
    turma = models.CharField(
    max_length=255,
    verbose_name="Turma",
    null=True,
    blank=True
    )
    data_matricula = models.DateField(
    verbose_name="Data de Matrícula",
    null=True,
    blank=True
    )
    
    # Guardian Information
    nome_responsavel1 = models.CharField(
        max_length=255,
        verbose_name="Nome do Responsável 1"
    )
    nome_responsavel1 = models.CharField(
    max_length=255,
    verbose_name="Nome do Responsável 1",
    null=True,
    blank=True
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
    rg = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="RG"
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        ordering = ['aluno', 'disciplina', 'bimestre']
        unique_together = ['aluno', 'disciplina', 'bimestre']
        indexes = [
            models.Index(fields=['aluno', 'disciplina'])
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
        
class NivelChoices(models.TextChoices):
    EFI = 'EFI', 'Ensino Fundamental Anos Iniciais'
    EFF = 'EFF', 'Ensino Fundamental Anos Finais'
    
class TurnoChoices(models.TextChoices):
    MANHA = 'M', 'Manhã'
    TARDE = 'T', 'Tarde'