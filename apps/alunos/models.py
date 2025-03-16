from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from io import BytesIO
import re
import os
import uuid
import logging

logger = logging.getLogger(__name__)

# Validators
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

class NivelChoices(models.TextChoices):
    EFI = 'EFI', 'Ensino Fundamental Anos Iniciais'
    EFF = 'EFF', 'Ensino Fundamental Anos Finais'
    
class TurnoChoices(models.TextChoices):
    MANHA = 'M', 'Manhã'
    TARDE = 'T', 'Tarde'

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
    """Validate image file format and size"""
    try:
        if not fieldfile_obj:
            return
            
        # Validate file size
        filesize = fieldfile_obj.size
        megabyte_limit = 5.0
        if filesize > megabyte_limit * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo do arquivo é {megabyte_limit}MB")

        # Validate image format
        valid_formats = ['image/jpeg', 'image/png', 'image/gif']
        
        if hasattr(fieldfile_obj, 'content_type'):
            file_type = fieldfile_obj.content_type
        else:
            import imghdr
            file_type = 'image/' + imghdr.what(None, fieldfile_obj.read(2048))
            fieldfile_obj.seek(0)

        if file_type not in valid_formats:
            raise ValidationError("Formato de imagem não suportado. Use JPEG, PNG ou GIF.")
            
        # Validate image dimensions
        img = Image.open(fieldfile_obj)
        if img.height > 2000 or img.width > 2000:
            raise ValidationError("Dimensões máximas permitidas: 2000x2000 pixels")
            
    except Exception as e:
        logger.error(f"Erro na validação da imagem: {str(e)}")
        raise ValidationError("Erro ao validar imagem. Verifique o formato e tamanho do arquivo.")

def aluno_foto_path(instance, filename):
    """Gera um caminho único para a foto do aluno"""
    ext = filename.split('.')[-1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"
    return f'alunos/fotos/{new_name}'  # Removido 'media/' do início 
class Aluno(models.Model):
    DEFAULT_PHOTO_URL = "https://ui-avatars.com/api/?name={}&background=random"
    id = models.CharField(
        primary_key=True,
        max_length=36,
        editable=False
    )
    
    foto = models.ImageField(
        upload_to=aluno_foto_path,
        null=True,
        blank=True,
        verbose_name='Foto do Aluno',
        validators=[validate_image],
        help_text='Tamanho máximo permitido: 5MB'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    dados_adicionais = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Dados Adicionais"
    )
    
    def get_foto_url(self):
        if self.foto:
            return self.foto.url
        # Retorna uma URL com as iniciais do nome do aluno
        return self.DEFAULT_PHOTO_URL.format(self.nome.replace(" ", "+"))

    def backup_image(self, image_path):
        """Cria um backup da imagem no S3"""
        try:
            if default_storage.exists(image_path):
                with default_storage.open(image_path, 'rb') as f:
                    backup_path = f"backup/alunos/fotos/{os.path.basename(image_path)}"
                    default_storage.save(backup_path, ContentFile(f.read()))
                    logger.info(f"Backup criado em: {backup_path}")
        except Exception as e:
            logger.error(f"Erro ao criar backup da imagem: {str(e)}")

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = str(uuid.uuid4())
            
        if self.foto and hasattr(self.foto, 'file'):
            try:
                # Processar imagem
                img = Image.open(self.foto)
                img = img.convert('RGB')
                
                # Redimensionar se necessário
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                
                # Salvar em buffer
                output = BytesIO()
                img.save(output, format='JPEG', quality=85)
                output.seek(0)
                
                # Gerar nome único
                filename = f"{uuid.uuid4().hex}.jpg"
                
                # Salvar no S3
                self.foto = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    filename,
                    'image/jpeg',
                    output.tell(),
                    None
                )
                
            except Exception as e:
                logger.error(f"Erro ao processar imagem para {self.nome}: {e}")
                raise ValidationError(f"Erro ao processar imagem: {str(e)}")

        super().save(*args, **kwargs)
        logger.info(f"Aluno {self.nome} salvo com sucesso")

    # Resto do código permanece igual...
    # (Mantenha todos os outros campos e métodos da classe Aluno exatamente como estão)

# Mantenha a classe Nota exatamente como está
    

    
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
    version = models.BigIntegerField(default=1, editable=False)
    
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
        help_text="Data de nascimento do aluno",
        null=True,
        blank=True
    )
    
    cpf = models.CharField(
        max_length=14,
        validators=[cpf_regex],
        verbose_name="CPF",
        help_text="CPF no formato: 999.999.999-99. Este campo é opcional.",
        null=True,  # Permite valores nulos no banco de dados
        blank=True  # Permite valores em branco no formulário
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
                condition=models.Q(ativo=True) & ~models.Q(cpf='') & ~models.Q(cpf__isnull=True),
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
        if not self.data_nascimento:
            return  # Retorna sem validar se não houver data de nascimento
            
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
            # Verificar CPF apenas se não estiver vazio
            if self.cpf and self.cpf.strip() and Aluno.objects.filter(cpf=self.cpf, ativo=True).exists():
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
        try:
            # Primeiro remove a foto se existir
            if self.foto:
                self.foto.delete(save=False)
            # Então executa a deleção normal
            super().delete(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro ao excluir aluno {self.nome}: {str(e)}")
            raise

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