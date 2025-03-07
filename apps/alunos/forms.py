from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Aluno, Nota
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import logging


logger = logging.getLogger(__name__)


class BaseForm(forms.ModelForm):
    """Base form class with common functionality"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.setup_form_widgets()
        
    def setup_form_widgets(self):
        """Setup common widget attributes"""
        for field_name, field in self.fields.items():
            css_classes = ['form-control']
            if isinstance(field, forms.DateField):
                field.widget.attrs.update({'type': 'date'})
            if isinstance(field, forms.FileField):
                css_classes.append('form-control-file')
            field.widget.attrs.update({
                'class': ' '.join(css_classes),
                'placeholder': field.label
            })

class AlunoForm(BaseForm):
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        return str(matricula)  # Força a conversão para string
    
    def clean_foto(self):
        """Validação e processamento melhorado da foto"""
        foto = self.cleaned_data.get('foto')
        if foto:
            logger.debug(f"Iniciando validação da foto: {foto.name}")
            
            # Validar tipo do arquivo
            if not foto.content_type.startswith('image/'):
                logger.error(f"Tipo de arquivo inválido: {foto.content_type}")
                raise ValidationError('O arquivo deve ser uma imagem')
            
            # Validar tamanho
            if foto.size > 5 * 1024 * 1024:  # 5MB
                logger.error(f"Arquivo muito grande: {foto.size} bytes")
                raise ValidationError('A foto não pode ter mais que 5MB')
            
            try:
                # Processar imagem
                img = Image.open(foto)
                
                # Converter para RGB se necessário
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                    logger.debug("Imagem convertida para RGB")
                
                # Redimensionar se necessário
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    logger.debug(f"Imagem redimensionada para {output_size}")
                
                # Salvar imagem otimizada
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                
                # Criar novo arquivo
                new_foto = InMemoryUploadedFile(
                    output,
                    'foto',
                    f"{foto.name.split('.')[0]}.jpg",
                    'image/jpeg',
                    output.getbuffer().nbytes,
                    None
                )
                
                logger.info("Foto processada com sucesso")
                return new_foto
                
            except Exception as e:
                logger.error(f"Erro ao processar imagem: {str(e)}")
                raise ValidationError(f"Erro ao processar imagem: {str(e)}")
                
        return foto
    
    class Meta:
        model = Aluno
        fields = [
            'nome', 'data_nascimento', 'cpf', 'rg', 'foto',
            'nivel', 'turno', 'ano', 'turma', 'matricula',
            'email', 'telefone', 'endereco', 'cidade', 'uf',
            'nome_responsavel1', 'telefone_responsavel1',
            'nome_responsavel2', 'telefone_responsavel2',
            'data_matricula', 'observacoes'
        ]
        widgets = {
            'foto': forms.FileInput(attrs={
                'accept': 'image/*',
                'data-max-size': '5242880'  # 5MB in bytes
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': 1000
            }),
            'matricula': forms.TextInput(),  # Alterado para TextInput para evitar problemas com números grandes
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_nivel_dependent_fields()
        self.setup_field_dependencies()
        # Configuração adicional para campos numéricos grandes
        if 'matricula' in self.fields:
            self.fields['matricula'].widget.attrs['maxlength'] = 20

    def setup_nivel_dependent_fields(self):
        """Setup fields that depend on nivel selection"""
        instance = self.instance
        if instance and instance.pk:
            # Instead of calling non-existent set_ano_choices, use get_filtered_ano_choices directly
            self.fields['ano'].choices = self.get_filtered_ano_choices(instance.nivel, instance.turno)
            if instance.nivel == 'EFI':
                self.fields['turno'].widget.attrs['disabled'] = True
                self.fields['turno'].initial = 'M'
        else:
            self.fields['ano'].choices = self.get_filtered_ano_choices()

    def setup_field_dependencies(self):
        """Setup field dependencies and dynamic behavior"""
        self.fields['nivel'].widget.attrs.update({
            'data-depends': 'turno,ano',
            'onchange': 'handleNivelChange(this)'
        })
        self.fields['turno'].widget.attrs.update({
            'data-depends': 'ano',
            'onchange': 'handleTurnoChange(this)'
        })

    def get_filtered_ano_choices(self, nivel=None, turno=None):
        """Get filtered year choices based on nivel and turno"""
        choices = []
        
        if nivel == 'EFI' or not nivel:
            choices.extend([
                ('3', '3º Ano'),
                ('4', '4º Ano'),
                ('5', '5º Ano'),
            ])
            
        if nivel == 'EFF' or not nivel:
            basic_choices = [
                ('6', '6º Ano'),
                ('7', '7º Ano'),
                ('8', '8º Ano'),
            ]
            choices.extend(basic_choices)
            
            if turno == 'T' or not turno:
                choices.extend([
                    ('901', '9º Ano - Turma 901'),
                    ('902', '9º Ano - Turma 902'),
                ])
                
        return choices

    def clean_foto(self):
        """Valida e processa o upload da foto"""
        foto = self.cleaned_data.get('foto')
        if foto:
            # Verifica o tipo de conteúdo
            if not foto.content_type.startswith('image/'):
                raise ValidationError(_("O arquivo enviado não é uma imagem."))
            
            # Verifica o tamanho do arquivo (máximo de 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if foto.size > max_size:
                raise ValidationError(_("A imagem excede o tamanho máximo de 5MB."))
            
            try:
                # Processa a imagem
                img = Image.open(foto)
                # Converte para RGB se necessário
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                # Redimensiona se for muito grande
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                # Salva a imagem otimizada
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                
                # Cria um objeto InMemoryUploadedFile para compatibilidade com Django
                new_foto = InMemoryUploadedFile(
                    output,
                    None,
                    foto.name,
                    'image/jpeg',
                    output.getbuffer().nbytes,
                    None
                )
                
                return new_foto
            except Exception as e:
                raise ValidationError(f"Erro ao processar imagem: {str(e)}")
        return foto

    def clean(self):
        """Enhanced validation logic"""
        cleaned_data = super().clean()
        self.validate_nivel_combinations(cleaned_data)
        self.validate_unique_fields(cleaned_data)
        
        # Validação adicional para campos numéricos
        matricula = cleaned_data.get('matricula')
        if matricula and len(str(matricula)) > 20:
            raise ValidationError({'matricula': _("Número de matrícula muito grande")})
            
        return cleaned_data

    def validate_nivel_combinations(self, cleaned_data):
        """Validate nivel, turno and ano combinations"""
        nivel = cleaned_data.get('nivel')
        turno = cleaned_data.get('turno')
        ano = cleaned_data.get('ano')
        
        if not all([nivel, turno, ano]):
            return
            
        errors = {}
        
        if nivel == 'EFI':
            if turno != 'M':
                cleaned_data['turno'] = 'M'
            if ano not in ['3', '4', '5']:
                errors['ano'] = _("Este ano não está disponível para Ensino Fundamental Anos Iniciais.")
                
        if nivel == 'EFF':
            if turno == 'M' and ano in ['901', '902']:
                errors['ano'] = _("As turmas do 9º ano só estão disponíveis no turno da tarde.")
            if ano in ['3', '4', '5']:
                errors['ano'] = _("Este ano não está disponível para Ensino Fundamental Anos Finais.")
                
        if errors:
            raise ValidationError(errors)

    def validate_unique_fields(self, cleaned_data):
        """Validate unique fields considering existing records"""
        for field in ['matricula', 'email', 'cpf']:
            value = cleaned_data.get(field)
            if value:
                query = {field: value}
                if self.instance.pk:
                    if Aluno.objects.filter(**query).exclude(pk=self.instance.pk).exists():
                        raise ValidationError({field: _(f"Este {field} já está em uso.")})
                else:
                    if Aluno.objects.filter(**query).exists():
                        raise ValidationError({field: _(f"Este {field} já está em uso.")})

    def save(self, commit=True):
        """Enhanced save method with user tracking"""
        instance = super().save(commit=False)
        
        if self.user:
            if not instance.pk:
                instance.created_by = self.user
            instance.updated_by = self.user
            
        if commit:
            instance.save()
            
        return instance

class NotaForm(BaseForm): 
    """Enhanced form for grade registration"""  
    class Meta:
        model = Nota
        fields = ['disciplina', 'valor', 'bimestre', 'observacao']
        
    valor = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0, message=_("A nota não pode ser menor que 0")),
            MaxValueValidator(10, message=_("A nota não pode ser maior que 10"))
        ]
    )

class AlunoFilterForm(forms.Form):
    """Enhanced filter form for student listing"""
    
    NIVEL_CHOICES = [('', _('Todos'))] + list(Aluno.NivelChoices.choices)
    TURNO_CHOICES = [('', _('Todos'))] + list(Aluno.TurnoChoices.choices)
    ANO_CHOICES = [('', _('Todos'))] + [
        ('3', '3º Ano'),
        ('4', '4º Ano'),
        ('5', '5º Ano'),
        ('6', '6º Ano'),
        ('7', '7º Ano'),
        ('8', '8º Ano'),
        ('901', '9º Ano - Turma 901'),
        ('902', '9º Ano - Turma 902')
    ]
    
    nivel = forms.ChoiceField(choices=NIVEL_CHOICES, required=False)
    turno = forms.ChoiceField(choices=TURNO_CHOICES, required=False)
    ano = forms.ChoiceField(choices=ANO_CHOICES, required=False)
    search = forms.CharField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_filter_widgets()
        
    def setup_filter_widgets(self):
        """Setup filter form widgets"""
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control form-control-sm',
                'data-filter': 'true'
            })