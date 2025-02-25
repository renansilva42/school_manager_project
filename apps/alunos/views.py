import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Aluno
from .forms import AlunoForm, NotaForm

def is_admin(user):
    return user.groups.filter(name='Administradores').exists()

# apps/alunos/views.py
@login_required
def lista_alunos(request):
    # Parâmetros de filtro da URL
    turno_filter = request.GET.get('turno')
    ano_filter = request.GET.get('ano')
    
    # Iniciar com todos os alunos
    alunos = Aluno.objects.all()
    
    # Aplicar filtros se fornecidos
    if turno_filter:
        alunos = alunos.filter(turno=turno_filter)
    if ano_filter:
        alunos = alunos.filter(ano=ano_filter)
    
    # Organizar por turno, ano e nome
    alunos = alunos.order_by('turno', 'ano', 'nome')
    
    # Contexto para o template
    context = {
        'alunos': alunos,
        'turno_choices': Aluno.TURNO_CHOICES,
        'ano_choices': Aluno.ANO_CHOICES,
        'turno_filter': turno_filter,
        'ano_filter': ano_filter,
    }
    
    return render(request, 'alunos/lista_alunos.html', context)

@login_required
def detalhe_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    return render(request, 'alunos/detalhe_aluno.html', {'aluno': aluno})

@login_required
@user_passes_test(is_admin)
def cadastrar_aluno(request):
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_alunos')
    else:
        form = AlunoForm()
    return render(request, 'alunos/cadastrar_aluno.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def editar_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES, instance=aluno)
        if form.is_valid():
            form.save()
            return redirect('detalhe_aluno', pk=pk)
    else:
        form = AlunoForm(instance=aluno)
    
    return render(request, 'alunos/editar_aluno.html', {'form': form, 'aluno': aluno})

@login_required
def adicionar_nota(request, aluno_pk):
    aluno = get_object_or_404(Aluno, pk=aluno_pk)
    if request.method == 'POST':
        form = NotaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.aluno = aluno
            nota.save()
            return redirect('detalhe_aluno', pk=aluno.pk)
    else:
        form = NotaForm()
    return render(request, 'alunos/adicionar_nota.html', {'form': form, 'aluno': aluno})

# apps/alunos/views.py
def exportar_detalhes_aluno_pdf(request, aluno_pk):
    aluno = get_object_or_404(Aluno, pk=aluno_pk)
    
    # Criar um buffer para o PDF
    buffer = io.BytesIO()
    
    # Criar o PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Adicionar título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Detalhes do Aluno: {aluno.nome}")
    
    # Adicionar foto se disponível
    if aluno.foto:
        try:
            img = ImageReader(aluno.foto.path)
            p.drawImage(img, 450, 650, width=100, height=100)
        except:
            pass
    
    # Adicionar informações do aluno
    p.setFont("Helvetica", 12)
    y = 700
    p.drawString(100, y, f"Matrícula: {aluno.matricula}")
    y -= 20
    p.drawString(100, y, f"Data de Nascimento: {aluno.data_nascimento.strftime('%d/%m/%Y')}")
    y -= 20
    p.drawString(100, y, f"Série: {aluno.serie}")
    y -= 20
    p.drawString(100, y, f"Turno: {aluno.get_turno_display()}")
    y -= 20
    p.drawString(100, y, f"Ano: {aluno.get_ano_display()}")
    
    # Continuar com o resto das informações...
    
    p.save()
    buffer.seek(0)
    
    # Retornar o PDF como resposta
    return FileResponse(buffer, as_attachment=True, filename=f"aluno_{aluno.pk}.pdf")