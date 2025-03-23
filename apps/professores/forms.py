from django import forms
from .models import Professor, AtribuicaoDisciplina, DisponibilidadeHorario, Disciplina
from django.core.exceptions import ValidationError

class ProfessorForm(forms.ModelForm):
    class Meta:
        model = Professor
        fields = ['nome', 'email', 'telefone', 'formacao', 'especialidade', 'foto']
        widgets = {
            'telefone': forms.TextInput(attrs={'class': 'phone-mask'}),
        }

class AtribuicaoDisciplinaForm(forms.ModelForm):
    class Meta:
        model = AtribuicaoDisciplina
        fields = ['professor', 'disciplina', 'turma', 'ano_letivo']

class DisponibilidadeHorarioForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadeHorario
        fields = '__all__'
        # If you want to exclude certain fields, you can use:
        # exclude = ['field_to_exclude']


class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'carga_horaria', 'descricao']

# Atualizar AtribuicaoDisciplinaForm
class AtribuicaoDisciplinaForm(forms.ModelForm):
    class Meta:
        model = AtribuicaoDisciplina
        fields = ['professor', 'disciplina', 'turma', 'ano_letivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professor'].queryset = Professor.objects.filter(ativo=True)
        self.fields['disciplina'].queryset = Disciplina.objects.filter(ativo=True)
