from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Avg, Q  # Adicionei Q aqui
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.core.exceptions import PermissionDenied
from services.database import SupabaseService
from .forms import AlunoForm, NotaForm, AlunoFilterForm
from .models import Aluno, Nota
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

def is_admin(user):
    """Check if user is in Administrators group"""
    return user.groups.filter(name='Administradores').exists()

class AlunoListView(ListView):
    model = Aluno
    template_name = 'alunos/lista_alunos.html'
    context_object_name = 'alunos'
    paginate_by = 12

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        queryset = Aluno.objects.all()
        
        # Apply filters
        filter_form = AlunoFilterForm(self.request.GET)
        if filter_form.is_valid():
            if filter_form.cleaned_data.get('nivel'):
                queryset = queryset.filter(nivel=filter_form.cleaned_data['nivel'])
            if filter_form.cleaned_data.get('turno'):
                queryset = queryset.filter(turno=filter_form.cleaned_data['turno'])
            if filter_form.cleaned_data.get('ano'):
                queryset = queryset.filter(ano=filter_form.cleaned_data['ano'])
            if filter_form.cleaned_data.get('search'):
                search_query = filter_form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(nome__icontains=search_query) |
                    Q(matricula__icontains=search_query) |
                    Q(cpf__icontains=search_query)
                )
        
        return queryset.order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AlunoFilterForm(self.request.GET)
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(
                'alunos/partials/lista_alunos_partial.html',
                context,
                request=self.request
            )
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)

@login_required
@user_passes_test(is_admin)
def cadastrar_aluno(request):
    """View for creating a new student"""
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                aluno = form.save(commit=False)
                aluno.id = uuid.uuid4()
                
                # Handle photo upload
                if 'foto' in request.FILES:
                    supabase = SupabaseService()
                    photo_url = supabase.upload_photo(request.FILES['foto'], str(aluno.id))
                    if photo_url:
                        aluno.foto_url = photo_url

                aluno.save()
                messages.success(request, 'Aluno cadastrado com sucesso!')
                return redirect('detalhe_aluno', pk=aluno.id)
                
            except Exception as e:
                logger.error(f"Error creating student: {str(e)}")
                messages.error(request, 'Erro ao cadastrar aluno. Por favor, tente novamente.')
    else:
        form = AlunoForm()
    
    return render(request, 'alunos/cadastrar_aluno.html', {'form': form})

class AlunoDetailView(DetailView):
    model = Aluno
    template_name = 'alunos/detalhe_aluno.html'
    context_object_name = 'aluno'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = self.get_object()
        context['notas'] = Nota.objects.filter(aluno=aluno).order_by('-data')
        context['media_geral'] = aluno.get_media_geral()
        return context

@login_required
@user_passes_test(is_admin)
def editar_aluno(request, pk):
    """View for editing an existing student"""
    aluno = get_object_or_404(Aluno, pk=pk)
    
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES, instance=aluno)
        if form.is_valid():
            try:
                aluno = form.save(commit=False)
                
                # Handle photo upload
                if 'foto' in request.FILES:
                    supabase = SupabaseService()
                    photo_url = supabase.upload_photo(request.FILES['foto'], str(aluno.id))
                    if photo_url:
                        aluno.foto_url = photo_url

                aluno.save()
                messages.success(request, 'Aluno atualizado com sucesso!')
                return redirect('detalhe_aluno', pk=aluno.id)
                
            except Exception as e:
                logger.error(f"Error updating student: {str(e)}")
                messages.error(request, 'Erro ao atualizar aluno. Por favor, tente novamente.')
    else:
        form = AlunoForm(instance=aluno)
    
    return render(request, 'alunos/editar_aluno.html', {
        'form': form,
        'aluno': aluno
    })

@login_required
@user_passes_test(is_admin)
def excluir_aluno(request, pk):
    """View for deleting a student"""
    aluno = get_object_or_404(Aluno, pk=pk)
    
    if request.method == 'POST':
        try:
            nome_aluno = aluno.nome
            aluno.delete()
            messages.success(request, f'Aluno "{nome_aluno}" excluído com sucesso!')
            return redirect('lista_alunos')
        except Exception as e:
            logger.error(f"Error deleting student: {str(e)}")
            messages.error(request, 'Erro ao excluir aluno. Por favor, tente novamente.')
            return redirect('detalhe_aluno', pk=pk)
    
    return render(request, 'alunos/confirmar_exclusao.html', {'aluno': aluno})

@login_required
@user_passes_test(is_admin)
def adicionar_nota(request, aluno_pk):
    """View for adding a grade to a student"""
    aluno = get_object_or_404(Aluno, pk=aluno_pk)

    if request.method == 'POST':
        form = NotaForm(request.POST)
        if form.is_valid():
            try:
                nota = form.save(commit=False)
                nota.aluno = aluno
                nota.save()
                
                messages.success(request, 'Nota adicionada com sucesso!')
                return redirect('detalhe_aluno', pk=aluno_pk)
                
            except Exception as e:
                logger.error(f"Error adding grade: {str(e)}")
                messages.error(request, 'Erro ao adicionar nota. Por favor, tente novamente.')
    else:
        form = NotaForm()
    
    return render(request, 'alunos/adicionar_nota.html', {
        'form': form,
        'aluno': aluno
    })

@login_required
def exportar_detalhes_aluno_pdf(request, aluno_pk):
    """View for exporting student details to PDF"""
    aluno = get_object_or_404(Aluno, pk=aluno_pk)
    
    try:
        # Implementation for PDF export would go here
        # Using a library like ReportLab or WeasyPrint
        messages.info(request, 'Funcionalidade em desenvolvimento')
        return redirect('detalhe_aluno', pk=aluno_pk)
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}")
        messages.error(request, 'Erro ao gerar PDF. Por favor, tente novamente.')
        return redirect('detalhe_aluno', pk=aluno_pk)

# API Views for AJAX requests
@login_required
def get_aluno_notas(request, aluno_pk):
    """API view to get student grades"""
    try:
        aluno = get_object_or_404(Aluno, pk=aluno_pk)
        notas = Nota.objects.filter(aluno=aluno).values(
            'disciplina', 'valor', 'bimestre', 'data'
        )
        return JsonResponse({'notas': list(notas)})
    except Exception as e:
        logger.error(f"Error fetching grades: {str(e)}")
        return JsonResponse({'error': 'Erro ao buscar notas'}, status=400)

@login_required
def get_aluno_media(request, aluno_pk):
    """API view to get student average grades"""
    try:
        aluno = get_object_or_404(Aluno, pk=aluno_pk)
        medias = Nota.objects.filter(aluno=aluno).values('disciplina').annotate(
            media=Avg('valor')
        )
        return JsonResponse({'medias': list(medias)})
    except Exception as e:
        logger.error(f"Error calculating averages: {str(e)}")
        return JsonResponse({'error': 'Erro ao calcular médias'}, status=400)