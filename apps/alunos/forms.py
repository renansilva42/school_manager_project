from django import forms
from django.core.exceptions import ValidationError
import json
from .models import Aluno, Nota

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome', 'data_nascimento', 'foto', 'serie', 'matricula', 'email', 'telefone', 'endereco', 'dados_adicionais']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'dados_adicionais': forms.Textarea(attrs={'rows': 4}),
        }

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

    # def clean_dados_adicionais(self):
    #     dados_adicionais = self.cleaned_data.get('dados_adicionais')
    #     if dados_adicionais:
    #         try:
    #             return json.loads(dados_adicionais)
    #         except json.JSONDecodeError:
    #             raise ValidationError("Dados adicionais devem estar em formato JSON válido.")
    #     return dados_adicionais

class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['disciplina', 'valor']  # Remova 'data' daqui
        
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor < 0 or valor > 10:
            raise ValidationError("A nota deve estar entre 0 e 10.")
        return valor