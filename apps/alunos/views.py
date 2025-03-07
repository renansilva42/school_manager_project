from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse, Http404
from services.database import SupabaseService
from .forms import AlunoForm
import uuid
from .forms import AlunoForm, NotaForm

def is_admin(user):
    return user.groups.filter(name='Administradores').exists()

@login_required
def lista_alunos(request):
    nivel = request.GET.get('nivel', '')
    turno = request.GET.get('turno', '')
    ano = request.GET.get('ano', '')
    search = request.GET.get('search', '')
    
    supabase = SupabaseService()
    response = supabase.list_alunos({
        'nivel': nivel,
        'turno': turno,
        'ano': ano,
        'search': search
    })
    
    alunos = response.data if response else []
    
    paginator = Paginator(alunos, 12)
    page_number = request.GET.get('page')
    alunos_page = paginator.get_page(page_number)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string(
            'alunos/partials/lista_alunos_partial.html',
            {'alunos': alunos_page}
        )
        return JsonResponse({'html': html})
    
    return render(request, 'alunos/lista_alunos.html', {
        'alunos': alunos_page
    })

@login_required
def exportar_detalhes_aluno_pdf(request, aluno_pk):
    supabase = SupabaseService()
    response = supabase.get_aluno(aluno_pk)
    aluno = response.data[0] if response and response.data else None
    
    if not aluno:
        raise Http404("Aluno não encontrado")
    
    # Aqui você pode implementar a lógica de exportação para PDF
    # Por exemplo, usando uma biblioteca como reportlab ou weasyprint
    
    # Por enquanto, vamos apenas redirecionar para a página de detalhes
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('detalhe_aluno', pk=aluno_pk)

@login_required
def detalhe_aluno(request, pk):
    supabase = SupabaseService()
    response = supabase.get_aluno(pk)
    aluno = response.data[0] if response and response.data else None
    
    if not aluno:
        raise Http404("Aluno não encontrado")
    
    # Adicionar o ID ao dicionário do aluno
    aluno['pk'] = pk  # ou usar o ID que já existe nos dados
    
    return render(request, 'alunos/detalhe_aluno.html', {'aluno': aluno})

@login_required
@user_passes_test(is_admin)
def cadastrar_aluno(request):
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                aluno_data = {
                    'id': str(uuid.uuid4()),
                    'nome': form.cleaned_data['nome'],
                    'matricula': form.cleaned_data['matricula'],
                    'data_nascimento': form.cleaned_data['data_nascimento'].strftime('%Y-%m-%d'),
                    'nivel': form.cleaned_data['nivel'],
                    'turno': form.cleaned_data['turno'],
                    'ano': form.cleaned_data['ano'],
                    'cpf': form.cleaned_data['cpf'],
                    'rg': form.cleaned_data['rg'],
                    'email': form.cleaned_data['email'],
                    'telefone': form.cleaned_data['telefone'],
                    'endereco': form.cleaned_data['endereco'],
                    'cidade': form.cleaned_data['cidade'],
                    'uf': form.cleaned_data['uf'],
                    'nome_responsavel1': form.cleaned_data['nome_responsavel1'],
                    'telefone_responsavel1': form.cleaned_data['telefone_responsavel1'],
                    'nome_responsavel2': form.cleaned_data['nome_responsavel2'],
                    'telefone_responsavel2': form.cleaned_data['telefone_responsavel2'],
                    'data_matricula': form.cleaned_data['data_matricula'].strftime('%Y-%m-%d'),
                    'observacoes': form.cleaned_data['observacoes'],
                    'turma': form.cleaned_data['turma'],
                }

                supabase = SupabaseService()
                
                if 'foto' in request.FILES:
                    photo_url = supabase.upload_photo(
                        request.FILES['foto'],
                        aluno_data['id']
                    )
                    if photo_url:
                        aluno_data['foto_url'] = photo_url

                response = supabase.create_aluno(aluno_data)
                
                if response:
                    messages.success(request, 'Aluno cadastrado com sucesso!')
                    return redirect('lista_alunos')
                else:
                    messages.error(request, 'Erro ao cadastrar aluno')
                    
            except Exception as e:
                messages.error(request, f'Erro ao cadastrar aluno: {str(e)}')
    else:
        form = AlunoForm()
    
    return render(request, 'alunos/cadastrar_aluno.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def editar_aluno(request, pk):
    supabase = SupabaseService()
    response = supabase.get_aluno(pk)
    aluno = response.data[0] if response and response.data else None
    
    if not aluno:
        raise Http404("Aluno não encontrado")
    
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                aluno_data = {
                    'nome': form.cleaned_data['nome'],
                    'matricula': form.cleaned_data['matricula'],
                    'data_nascimento': form.cleaned_data['data_nascimento'].strftime('%Y-%m-%d'),
                    'nivel': form.cleaned_data['nivel'],
                    'turno': form.cleaned_data['turno'],
                    'ano': form.cleaned_data['ano'],
                    # Add other fields...
                }
                
                if 'foto' in request.FILES:
                    photo_url = supabase.upload_photo(
                        request.FILES['foto'],
                        pk
                    )
                    if photo_url:
                        aluno_data['foto_url'] = photo_url

                response = supabase.update_aluno(pk, aluno_data)
                
                if response:
                    messages.success(request, 'Aluno atualizado com sucesso!')
                    return redirect('detalhe_aluno', pk=pk)
                    
            except Exception as e:
                messages.error(request, f'Erro ao atualizar aluno: {str(e)}')
    else:
        form = AlunoForm(initial=aluno)
    
    return render(request, 'alunos/editar_aluno.html', {
        'form': form,
        'aluno': aluno
    })
    

@login_required
@user_passes_test(is_admin)
def excluir_aluno(request, pk):
    supabase = SupabaseService()
    response = supabase.get_aluno(pk)
    aluno = response.data[0] if response and response.data else None
    
    if not aluno:
        raise Http404("Aluno não encontrado")
    
    if request.method == 'POST':
        try:
            supabase.delete_aluno(pk)
            messages.success(request, f'Aluno "{aluno["nome"]}" excluído com sucesso!')
            return redirect('lista_alunos')
        except Exception as e:
            messages.error(request, f'Erro ao excluir aluno: {str(e)}')
            return redirect('detalhe_aluno', pk=pk)
    
    return render(request, 'alunos/confirmar_exclusao.html', {'aluno': aluno})

def create_nota(self, data):
    return self.client.table('notas').insert(data).execute()

@login_required
@user_passes_test(is_admin)
def adicionar_nota(request, aluno_pk):
    supabase = SupabaseService()
    response = supabase.get_aluno(aluno_pk)
    aluno = response.data[0] if response and response.data else None
    
    if not aluno:
        raise Http404("Aluno não encontrado")

    if request.method == 'POST':
        form = NotaForm(request.POST)
        if form.is_valid():
            try:
                nota_data = {
                    'id': str(uuid.uuid4()),
                    'aluno_id': aluno_pk,
                    'disciplina': form.cleaned_data['disciplina'],
                    'nota': form.cleaned_data['nota'],
                    'data': form.cleaned_data['data'].strftime('%Y-%m-%d'),
                    'bimestre': form.cleaned_data['bimestre']
                }
                
                response = supabase.create_nota(nota_data)
                
                if response:
                    messages.success(request, 'Nota adicionada com sucesso!')
                    return redirect('detalhe_aluno', pk=aluno_pk)
                else:
                    messages.error(request, 'Erro ao adicionar nota')
                    
            except Exception as e:
                messages.error(request, f'Erro ao adicionar nota: {str(e)}')
    else:
        form = NotaForm()
    
    return render(request, 'alunos/adicionar_nota.html', {
        'form': form,
        'aluno': aluno
    })