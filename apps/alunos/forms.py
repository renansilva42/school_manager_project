from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Aluno, Nota
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import logging
import base64
from io import BytesIO
import uuid
import os
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseForm(forms.ModelForm):
    """Classe base para formulários com funcionalidades comuns"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.setup_form_widgets()
        
    def setup_form_widgets(self):
        """Configura atributos comuns dos widgets"""
        for field_name, field in self.fields.items():
            css_classes = ['form-control']
            if isinstance(field, forms.DateField):
                field.widget.attrs.update({'type': 'date'})
                field.input_formats = ['%d/%m/%Y']  # Força o formato DD/MM/YYYY
            if isinstance(field, forms.FileField):
                css_classes.append('form-control-file')
            field.widget.attrs.update({
                'class': ' '.join(css_classes),
                'placeholder': field.label
            })

class AlunoForm(BaseForm):
    foto_base64 = forms.CharField(required=False, widget=forms.HiddenInput())
    
    # Campo CPF explicitamente definido como não obrigatório
    data_nascimento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    data_matricula = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    cpf = forms.CharField(
        max_length=14,
        required=False,
        help_text="CPF no formato: 999.999.999-99. Este campo é opcional e pode ser deixado em branco."
    )
    
    # Campos de telefone com help_text aprimorado
    telefone = forms.CharField(
        max_length=15, 
        required=False,
        help_text="Digite apenas os números. O formato será aplicado automaticamente: (XX) XXXXX-XXXX"
    )
    
    telefone_responsavel1 = forms.CharField(
        max_length=15,
        help_text="Digite apenas os números. O formato será aplicado automaticamente: (XX) XXXXX-XXXX"
    )
    
    telefone_responsavel2 = forms.CharField(
        max_length=15,
        required=False,
        help_text="Digite apenas os números. O formato será aplicado automaticamente: (XX) XXXXX-XXXX"
    )
    
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        return str(matricula)
    
    def clean(self):
        cleaned_data = super().clean()
        foto_base64 = cleaned_data.get('foto_base64')
        foto_file = cleaned_data.get('foto')
        
        # Garantir que o diretório de destino exista
        upload_path = os.path.join(settings.MEDIA_ROOT, 'alunos/fotos')
        os.makedirs(upload_path, exist_ok=True)
        
        # Processa foto base64 se existir
        if foto_base64 and foto_base64.startswith('data:image'):
            try:
                # Extrai os dados base64
                format, imgstr = foto_base64.split(';base64,')
                ext = format.split('/')[-1]
                
                # Converte base64 para bytes
                imgdata = base64.b64decode(imgstr)
                
                # Cria um arquivo em memória
                buffer = BytesIO(imgdata)
                
                # Processa a imagem
                img = Image.open(buffer)
                
                # Converte para RGB se necessário
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Redimensiona se necessário
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                
                # Salva a imagem processada
                output = BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                
                # Gera um nome único para o arquivo
                unique_filename = f'alunos/fotos/camera_photo_{uuid.uuid4().hex[:8]}.jpg'

                cleaned_data['foto'] = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    unique_filename,
                    'image/jpeg',
                    len(output.getvalue()),
                    None
                )
                
                logger.info(f"Foto da câmera processada com sucesso: {unique_filename}")
                
            except Exception as e:
                logger.error(f"Erro ao processar foto da câmera: {str(e)}")
                raise ValidationError("Erro ao processar a foto da câmera")
                
        # Processa arquivo de foto se existir
        elif foto_file:
            try:
                # Verificar se é um arquivo recém-enviado ou um arquivo existente
                if hasattr(foto_file, 'content_type'):
                    # É um arquivo recém-enviado (UploadedFile)
                    # Validar tipo do arquivo
                    if not foto_file.content_type.startswith('image/'):
                        raise ValidationError('O arquivo deve ser uma imagem')
                    
                    # Validar tamanho
                    if foto_file.size > 5 * 1024 * 1024:  # 5MB
                        raise ValidationError('A foto não pode ter mais que 5MB')
                else:
                    # É um arquivo existente (ImageFieldFile)
                    # Verificar se o arquivo existe
                    if not foto_file:
                        return cleaned_data
                
                # Processar imagem
                img = Image.open(foto_file)
                
                # Converter para RGB se necessário
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Redimensionar se necessário
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                
                # Salvar imagem otimizada
                output = BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                
                # Gera um nome único para o arquivo
                unique_filename = f"alunos/fotos/{uuid.uuid4().hex}.jpg"

                cleaned_data['foto'] = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    unique_filename,
                    'image/jpeg',
                    len(output.getvalue()),
                    None
                )
                
                logger.info(f"Foto do arquivo processada com sucesso: {unique_filename}")
                
            except Exception as e:
                logger.error(f"Erro ao processar arquivo de imagem: {str(e)}")
                raise ValidationError(f"Erro ao processar imagem: {str(e)}")
        
        # Validação adicional para campos obrigatórios
        self.validate_nivel_combinations(cleaned_data)
        self.validate_unique_fields(cleaned_data)
        
        return cleaned_data

    class Meta:
        model = Aluno
        fields = [
            'nome', 'data_nascimento', 'cpf', 'rg', 'foto', 'foto_base64',
            'nivel', 'turno', 'ano', 'turma', 'matricula',
            'email', 'telefone', 'endereco', 'cidade', 'uf',
            'nome_responsavel1', 'telefone_responsavel1',
            'nome_responsavel2', 'telefone_responsavel2',
            'data_matricula', 'observacoes'
        ]
        widgets = {
            'foto': forms.FileInput(attrs={
                'accept': 'image/*',
                'data-max-size': '5242880'  # 5MB em bytes
            }),
            'foto_base64': forms.HiddenInput(),
            'observacoes': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': 1000
            }),
            'matricula': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_nivel_dependent_fields()
        self.setup_field_dependencies()
        # Configuração adicional para campos numéricos grandes
        if 'matricula' in self.fields:
            self.fields['matricula'].widget.attrs['maxlength'] = 20

    def setup_nivel_dependent_fields(self):
        """Configura campos que dependem da seleção do nível"""
        instance = self.instance
        if instance and instance.pk:
            self.fields['ano'].choices = self.get_filtered_ano_choices(instance.nivel, instance.turno)
            
            # Se for EFI, configura o turno como Manhã
            if instance.nivel == 'EFI':
                self.fields['turno'].initial = 'M'
                self.fields['turno'].widget.attrs['readonly'] = True  # Usa readonly em vez de disabled
        else:
            self.fields['ano'].choices = self.get_filtered_ano_choices()

    def setup_field_dependencies(self):
        """Configura dependências e comportamento dinâmico dos campos"""
        self.fields['nivel'].widget.attrs.update({
            'data-depends': 'turno,ano',
            'onchange': 'handleNivelChange(this)'
        })
        self.fields['turno'].widget.attrs.update({
            'data-depends': 'ano',
            'onchange': 'handleTurnoChange(this)'
        })

    def get_filtered_ano_choices(self, nivel=None, turno=None):
        """Obtém escolhas de ano filtradas com base em nível e turno"""
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

    def validate_nivel_combinations(self, cleaned_data):
        """Valida combinações de nível, turno e ano"""
        nivel = cleaned_data.get('nivel')
        turno = cleaned_data.get('turno')
        ano = cleaned_data.get('ano')
        
        if not nivel:
            return
            
        errors = {}
        
        # Garantir que turno e ano estejam presentes
        if not turno:
            errors['turno'] = _("Este campo é obrigatório.")
        
        if not ano:
            errors['ano'] = _("Este campo é obrigatório.")
            
        if nivel == 'EFI':
            # Para EFI, força o turno como Manhã
            cleaned_data['turno'] = 'M'
            
            # Valida o ano para EFI
            if ano and ano not in ['3', '4', '5']:
                errors['ano'] = _("Este ano não está disponível para Ensino Fundamental Anos Iniciais.")
            
            # Garantir que o ano seja um dos valores válidos para EFI
            if not ano or ano not in ['3', '4', '5']:
                # Se o ano não for válido, definir um valor padrão
                if self.instance and hasattr(self.instance, 'ano') and self.instance.ano in ['3', '4', '5']:
                    # Se o aluno já tem um ano válido, manter
                    cleaned_data['ano'] = self.instance.ano
                else:
                    # Caso contrário, definir o primeiro ano válido
                    cleaned_data['ano'] = '3'
                
        elif nivel == 'EFF':
            # Para EFF, valida as combinações de turno e ano
            if turno == 'M' and ano and ano in ['901', '902']:
                errors['ano'] = _("As turmas do 9º ano só estão disponíveis no turno da tarde.")
            elif ano and ano in ['3', '4', '5']:
                errors['ano'] = _("Este ano não está disponível para Ensino Fundamental Anos Finais.")
                
        if errors:
            raise ValidationError(errors)

   
        def validate_unique_fields(self, cleaned_data):
            """Valida campos únicos considerando registros existentes"""
            for field in ['matricula', 'email', 'cpf']:
                value = cleaned_data.get(field)
                # Pula validação para valores vazios ou None
                if not value or value.strip() == '':
                    continue
                    
                query = {field: value}
                if self.instance.pk:
                    if Aluno.objects.filter(**query).exclude(pk=self.instance.pk).exists():
                        raise ValidationError({field: _(f"Este {field} já está em uso.")})
                else:
                    if Aluno.objects.filter(**query).exists():
                        raise ValidationError({field: _(f"Este {field} já está em uso.")})
    def save(self, commit=True):
        """Método de salvamento aprimorado com rastreamento de usuário"""
        instance = super().save(commit=False)
        
        if self.user:
            if not instance.pk:
                instance.created_by = self.user
            instance.updated_by = self.user
            
        if commit:
            instance.save()
            
        return instance

class NotaForm(BaseForm): 
    """Formulário aprimorado para registro de notas"""  
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
    """Formulário aprimorado para filtro de alunos"""
    
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
        """Configura widgets do formulário de filtro"""
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control form-control-sm',
                'data-filter': 'true'
            })