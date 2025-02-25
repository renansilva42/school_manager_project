# apps/alunos/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Aluno, Nota

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome', 'data_nascimento', 'foto', 'nivel', 'turno', 'ano', 'matricula', 'email', 'telefone', 'endereco', 'dados_adicionais']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'dados_adicionais': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar os campos inicialmente
        self.fields['ano'].widget = forms.Select(choices=[])
        self.update_ano_choices()
        
        # Adicionar JavaScript para atualizar dinamicamente as opções de ano
        self.fields['turno'].widget.attrs.update({
            'onchange': 'updateAnoChoices(this.value, document.getElementById("id_nivel").value)'
        })
        self.fields['nivel'].widget.attrs.update({
            'onchange': 'updateAnoChoices(document.getElementById("id_turno").value, this.value)'
        })

    def update_ano_choices(self):
        """Atualiza as opções de ano com base no turno e nível selecionados"""
        turno = self.data.get('turno') if self.data else self.initial.get('turno', 'M')
        nivel = self.data.get('nivel') if self.data else self.initial.get('nivel', 'EFF')
        
        choices = []
        
        if nivel == 'EFI':
            # Ensino Fundamental Anos Iniciais - apenas turno da manhã
            if turno == 'M':
                choices = [
                    ('3', '3º Ano'),
                    ('4', '4º Ano'),
                    ('5', '5º Ano'),
                ]
        else:  # EFF - Ensino Fundamental Anos Finais
            if turno == 'M':
                choices = [
                    ('6', '6º Ano'),
                    ('7', '7º Ano'),
                    ('8', '8º Ano'),
                ]
            else:  # Turno da tarde
                choices = [
                    ('6', '6º Ano'),
                    ('7', '7º Ano'),
                    ('8', '8º Ano'),
                    ('901', '9º Ano - Turma 901'),
                    ('902', '9º Ano - Turma 902'),
                ]
        
        self.fields['ano'].widget.choices = choices
        
    def clean(self):
        cleaned_data = super().clean()
        turno = cleaned_data.get('turno')
        nivel = cleaned_data.get('nivel')
        ano = cleaned_data.get('ano')
        
        # Validar combinações de turno, nível e ano
        if nivel == 'EFI' and turno == 'T':
            raise ValidationError("Ensino Fundamental Anos Iniciais só está disponível no turno da manhã.")
        
        if nivel == 'EFI' and ano in ['6', '7', '8', '901', '902']:
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