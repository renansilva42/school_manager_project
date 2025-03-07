# apps/alunos/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Aluno, Nota
# apps/alunos/forms.py
class AlunoForm(forms.ModelForm):
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
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'data_matricula': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        instance = kwargs.get('instance')
        
        if instance:
            nivel = instance.nivel
            turno = instance.turno
            self.set_ano_choices(nivel, turno)
            
            if nivel == 'EFI':
                self.fields['turno'].widget.attrs['disabled'] = 'disabled'
        else:
            # Agora vai funcionar porque ANO_CHOICES existe na classe Aluno
            self.fields['ano'].choices = Aluno.ANO_CHOICES
    
    def set_ano_choices(self, nivel, turno):
        """Define as opções de ano com base no nível e turno"""
        choices = []
        
        if nivel == 'EFI':
            # Ensino Fundamental Anos Iniciais - apenas turno da manhã
            choices = [
                ('3', '3º Ano'),
                ('4', '4º Ano'),
                ('5', '5º Ano'),
            ]
        elif nivel == 'EFF':
            # Ensino Fundamental Anos Finais
            if turno == 'M':
                choices = [
                    ('6', '6º Ano'),
                    ('7', '7º Ano'),
                    ('8', '8º Ano'),
                ]
            elif turno == 'T':
                choices = [
                    ('6', '6º Ano'),
                    ('7', '7º Ano'),
                    ('8', '8º Ano'),
                    ('901', '9º Ano - Turma 901'),
                    ('902', '9º Ano - Turma 902'),
                ]
        
        self.fields['ano'].choices = choices
    
    def clean(self):
        cleaned_data = super().clean()
        nivel = cleaned_data.get('nivel')
        turno = cleaned_data.get('turno')
        ano = cleaned_data.get('ano')
        
        # Validar combinações de turno, nível e ano
        if nivel == 'EFI' and turno != 'M':
            # Forçar o turno para manhã para EFI
            cleaned_data['turno'] = 'M'
        
        if nivel == 'EFI' and ano not in ['3', '4', '5']:
            raise ValidationError("Este ano não está disponível para Ensino Fundamental Anos Iniciais.")
        
        if nivel == 'EFF' and turno == 'M' and ano in ['901', '902']:
            raise ValidationError("As turmas do 9º ano só estão disponíveis no turno da tarde.")
        
        if nivel == 'EFF' and ano in ['3', '4', '5']:
            raise ValidationError("Este ano não está disponível para Ensino Fundamental Anos Finais.")
        
        return cleaned_data

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if Aluno.objects.exclude(pk=self.instance.pk if self.instance else None).filter(matricula=matricula).exists():
            raise ValidationError("Esta matrícula já está em uso.")
        return matricula

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Aluno.objects.exclude(pk=self.instance.pk if self.instance else None).filter(email=email).exists():
            raise ValidationError("Este e-mail já está em uso.")
        return email
class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['disciplina', 'valor']  # Remova 'data' daqui
        
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor < 0 or valor > 10:
            raise ValidationError("A nota deve estar entre 0 e 10.")
        return valor