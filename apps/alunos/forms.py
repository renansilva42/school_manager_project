from django import forms
from django.core.exceptions import ValidationError

class NotaForm(forms.Form):
    disciplina = forms.ChoiceField(choices=[
        ('PORTUGUES', 'Português'),
        ('MATEMATICA', 'Matemática'),
        ('CIENCIAS', 'Ciências'),
        ('HISTORIA', 'História'),
        ('GEOGRAFIA', 'Geografia'),
        ('INGLES', 'Inglês'),
        ('ARTES', 'Artes'),
        ('EDUCACAO_FISICA', 'Educação Física')
    ])
    nota = forms.DecimalField(max_digits=4, decimal_places=2)
    data = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    bimestre = forms.ChoiceField(choices=[
        ('1', '1º Bimestre'),
        ('2', '2º Bimestre'),
        ('3', '3º Bimestre'),
        ('4', '4º Bimestre')
    ])

class AlunoForm(forms.Form):
    nome = forms.CharField(max_length=255)
    data_nascimento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    cpf = forms.CharField(max_length=14)
    rg = forms.CharField(max_length=20)
    foto = forms.ImageField(required=False)
    nivel = forms.ChoiceField(choices=[
        ('EFI', 'Ensino Fundamental Anos Iniciais'),
        ('EFF', 'Ensino Fundamental Anos Finais'),
    ])
    turno = forms.ChoiceField(choices=[
        ('M', 'Manhã'),
        ('T', 'Tarde'),
    ])
    ano = forms.ChoiceField(choices=[
        ('3', '3º Ano'),
        ('4', '4º Ano'),
        ('5', '5º Ano'),
        ('6', '6º Ano'),
        ('7', '7º Ano'),
        ('8', '8º Ano'),
        ('901', '9º Ano - Turma 901'),
        ('902', '9º Ano - Turma 902'),
    ])
    turma = forms.CharField(max_length=10)
    matricula = forms.CharField(max_length=20)
    email = forms.EmailField(required=False)
    telefone = forms.CharField(max_length=15)
    endereco = forms.CharField(max_length=255)
    cidade = forms.CharField(max_length=100)
    uf = forms.CharField(max_length=2)
    nome_responsavel1 = forms.CharField(max_length=255)
    telefone_responsavel1 = forms.CharField(max_length=15)
    nome_responsavel2 = forms.CharField(max_length=255, required=False)
    telefone_responsavel2 = forms.CharField(max_length=15, required=False)
    data_matricula = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    observacoes = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        cleaned_data = super().clean()
        nivel = cleaned_data.get('nivel')
        turno = cleaned_data.get('turno')
        ano = cleaned_data.get('ano')
        
        if nivel == 'EFI' and turno != 'M':
            raise ValidationError('Para EFI, apenas o turno da manhã está disponível')
        
        # Add other validations as needed
        
        
        return cleaned_data
    
    