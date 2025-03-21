from django import forms
from .models import Professor, AtribuicaoDisciplina, DisponibilidadeHorario

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
        fields = ['professor', 'dia_semana', 'hora_inicio', 'hora_fim']