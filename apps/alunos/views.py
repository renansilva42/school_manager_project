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

@login_required
def lista_alunos(request):
    alunos = Aluno.objects.all()
    return render(request, 'alunos/lista_alunos.html', {'alunos': alunos})

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

@login_required
def exportar_detalhes_aluno_pdf(request, aluno_pk):
    aluno = get_object_or_404(Aluno, pk=aluno_pk)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Adicionar título
    p.drawString(100, 750, f"Detalhes do Aluno: {aluno.nome}")

    # Adicionar foto
    if aluno.foto:
        foto = ImageReader(aluno.foto)
        p.drawImage(foto, 100, 600, width=100, height=100)

    # Adicionar informações do aluno
    p.drawString(100, 580, f"Matrícula: {aluno.matricula}")
    p.drawString(100, 560, f"Data de Nascimento: {aluno.data_nascimento.strftime('%d/%m/%Y')}")
    p.drawString(100, 540, f"Série: {aluno.serie}")
    p.drawString(100, 520, f"E-mail: {aluno.email}")
    p.drawString(100, 500, f"Telefone: {aluno.telefone}")
    p.drawString(100, 480, f"Endereço: {aluno.endereco}")

    # Adicionar notas
    p.drawString(100, 460, "Notas:")
    y = 440
    for nota in aluno.notas.all():
        p.drawString(100, y, f"{nota.disciplina}: {nota.valor} - {nota.data.strftime('%d/%m/%Y')}")
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='detalhes_aluno.pdf')