from django import forms
from .models import Professor, AtribuicaoDisciplina, DisponibilidadeHorario, Disciplina
from django.core.exceptions import ValidationError

class ProfessorForm(forms.ModelForm):
    class Meta:
        model = Professor
        fields = ['nome', 'email', 'telefone', 'formacao', 'especialidade', 'foto']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control phone-mask'}),
            'formacao': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidade': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})

class AtribuicaoDisciplinaForm(forms.ModelForm):
    class Meta:
        model = AtribuicaoDisciplina
        fields = ['professor', 'disciplina', 'turma', 'ano_letivo']
        widgets = {
            'professor': forms.Select(attrs={'class': 'form-control'}),
            'disciplina': forms.Select(attrs={'class': 'form-control'}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'ano_letivo': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class DisponibilidadeHorarioForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadeHorario
        fields = ['professor', 'dia_semana', 'hora_inicio', 'hora_fim']
        widgets = {
            'professor': forms.Select(attrs={'class': 'form-control'}),
            'dia_semana': forms.Select(attrs={'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }


class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'carga_horaria_iniciais', 'carga_horaria_finais', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'carga_horaria_iniciais': forms.NumberInput(attrs={'class': 'form-control'}),
            'carga_horaria_finais': forms.NumberInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Form para atribuição de disciplinas
class AtribuicaoDisciplinaFormUpdate(forms.ModelForm):
    class Meta:
        model = AtribuicaoDisciplina
        fields = ['professor', 'disciplina', 'turma', 'ano_letivo']
        widgets = {
            'professor': forms.Select(attrs={'class': 'form-control'}),
            'disciplina': forms.Select(attrs={'class': 'form-control'}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'ano_letivo': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professor'].queryset = Professor.objects.filter(ativo=True)
        self.fields['disciplina'].queryset = Disciplina.objects.filter(ativo=True)
