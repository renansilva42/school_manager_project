from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Aluno, Nota
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile

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
    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if foto:
            if foto.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError('A foto não pode ter mais que 5MB')
            return foto
        return None
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_nivel_dependent_fields()
        self.setup_field_dependencies()

    def setup_nivel_dependent_fields(self):
        """Setup fields that depend on nivel selection"""
        instance = self.instance
        if instance and instance.pk:
            self.set_ano_choices(instance.nivel, instance.turno)
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

# As classes NotaForm e AlunoFilterForm permanecem inalteradas
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