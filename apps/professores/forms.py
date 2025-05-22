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

from django import forms
from .models import Professor, AtribuicaoDisciplina, DisponibilidadeHorario, Disciplina
from django.core.exceptions import ValidationError

class AtribuicaoDisciplinaForm(forms.Form):
    professor = forms.ModelChoiceField(
        queryset=Professor.objects.filter(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    disciplinas = forms.ModelMultipleChoiceField(
        queryset=Disciplina.objects.filter(ativo=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=True
    )
    turmas = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite as turmas separadas por vírgula'}),
        required=True,
        help_text='Digite as turmas separadas por vírgula, ex: 1A, 2B'
    )
    ano_letivo = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=True
    )

    def clean_turmas(self):
        turmas_str = self.cleaned_data['turmas']
        turmas_list = [t.strip() for t in turmas_str.split(',') if t.strip()]
        if not turmas_list:
            raise ValidationError('Informe pelo menos uma turma válida.')
        return turmas_list

    def save(self):
        professor = self.cleaned_data['professor']
        disciplinas = self.cleaned_data['disciplinas']
        turmas = self.cleaned_data['turmas']
        ano_letivo = self.cleaned_data['ano_letivo']

        created_assignments = []
        errors = []
        for turma in turmas:
            for disciplina in disciplinas:
                atrib, created = AtribuicaoDisciplina.objects.get_or_create(
                    professor=professor,
                    disciplina=disciplina,
                    turma=turma,
                    ano_letivo=ano_letivo
                )
                if created:
                    created_assignments.append(atrib)
                else:
                    errors.append(f'Atribuição já existe: {professor.nome} - {disciplina.nome} - {turma}')
        if errors:
            raise ValidationError(errors)
        return created_assignments

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
