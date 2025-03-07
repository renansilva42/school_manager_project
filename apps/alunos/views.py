import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from django.contrib import messages
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Aluno
from .forms import AlunoForm, NotaForm
from django.core.paginator import Paginator
from django.db import models
from django.template.loader import render_to_string
from django.http import JsonResponse
from services.database import SupabaseService

def is_admin(user):
    return user.groups.filter(name='Administradores').exists()

def lista_alunos(request):
    nivel = request.GET.get('nivel', '')
    turno = request.GET.get('turno', '')
    ano = request.GET.get('ano', '')
    search = request.GET.get('search', '')
    
    queryset = Aluno.objects.all()
    
    if nivel:
        queryset = queryset.filter(nivel=nivel)
    if turno:
        queryset = queryset.filter(turno=turno)
    if ano:
        queryset = queryset.filter(ano=ano)
    if search:
        queryset = queryset.filter(
            models.Q(nome__icontains=search) |
            models.Q(matricula__icontains=search)
        )
    
    queryset = queryset.order_by('nivel', 'turno', 'ano', 'nome')
    
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    alunos = paginator.get_page(page_number)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string(
            'alunos/partials/lista_alunos_partial.html',
            {'alunos': alunos}
        )
        return JsonResponse({'html': html})
    
    return render(request, 'alunos/lista_alunos.html', {
        'alunos': alunos
    })

@login_required
def detalhe_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    return render(request, 'alunos/detalhe_aluno.html', {'aluno': aluno})

@login_required
@user_passes_test(is_admin)
def excluir_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    nome_aluno = aluno.nome
    
    try:
        # Exclui o aluno do Django
        aluno.delete()
        
        # Exclui o aluno do Supabase
        supabase_service = SupabaseService()
        supabase_service.delete_aluno(pk)
        
        messages.success(request, f'Aluno "{nome_aluno}" excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir aluno: {str(e)}')
    
    return redirect('lista_alunos')

@login_required
@user_passes_test(is_admin)
def cadastrar_aluno(request):
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Não salve o aluno ainda
                aluno = form.save(commit=False)
                
                # Prepare os dados para o Supabase
                aluno_data = {
                    'id': str(uuid.uuid4()),
                    'nome': form.cleaned_data['nome'],
                    'matricula': form.cleaned_data['matricula'],
                    'data_nascimento': form.cleaned_data['data_nascimento'].strftime('%Y-%m-%d'),
                    'nivel': form.cleaned_data['nivel'],
                    'turno': form.cleaned_data['turno'],
                    'ano': form.cleaned_data['ano'],
                }

                # Se houver foto, faça o upload
                if 'foto' in request.FILES:
                    supabase_service = SupabaseService()
                    photo_url = supabase_service.upload_photo(
                        request.FILES['foto'], 
                        aluno_data['id']
                    )
                    if photo_url:
                        aluno.foto_url = photo_url
                
                # Salve o aluno no Django
                aluno.save()
                
                # Crie o registro no Supabase
                supabase_service = SupabaseService()
                response = supabase_service.create_aluno(aluno_data)
                
                if response:
                    messages.success(request, 'Aluno cadastrado com sucesso!')
                    return redirect('lista_alunos')
                else:
                    messages.error(request, 'Erro ao cadastrar aluno no Supabase')
                    
            except Exception as e:
                messages.error(request, f'Erro ao cadastrar aluno: {str(e)}')
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
            try:
                # Salva no Django
                aluno = form.save()
                
                # Prepara dados para o Supabase
                aluno_data = {
                    'id': aluno.pk,
                    'nome': aluno.nome,
                    'matricula': aluno.matricula,
                    'data_nascimento': aluno.data_nascimento.strftime('%Y-%m-%d'),
                    'nivel': aluno.nivel,
                    'serie': aluno.serie,
                    'turno': aluno.turno,
                    'ano': aluno.ano,
                    'foto_url': aluno.foto.url if aluno.foto else None
                }
                
                # Atualiza no Supabase
                supabase_service = SupabaseService()
                supabase_service.update_aluno(pk, aluno_data)
                
                messages.success(request, 'Dados do aluno atualizados com sucesso!')
                return redirect('detalhe_aluno', pk=pk)
            except Exception as e:
                messages.error(request, f'Erro ao atualizar aluno: {str(e)}')
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
    p.drawString(100, y, f"Nível: {aluno.get_nivel_display()}")
    y -= 20
    p.drawString(100, y, f"Série: {aluno.serie}")
    y -= 20
    p.drawString(100, y, f"Turno: {aluno.get_turno_display()}")
    y -= 20
    p.drawString(100, y, f"Ano: {aluno.get_ano_display()}")
    
    p.save()
    buffer.seek(0)
    
    # Retornar o PDF como resposta
    return FileResponse(buffer, as_attachment=True, filename=f"aluno_{aluno.pk}.pdf")