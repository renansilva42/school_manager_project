from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Avg, Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.views import View  # Adicione este import
from services.database import SupabaseService
from .forms import AlunoForm, NotaForm, AlunoFilterForm
from .models import Aluno, Nota
from .mixins import AdminRequiredMixin
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import xlsxwriter
from io import BytesIO
import uuid
import logging

from django.urls import reverse_lazy
success_url = reverse_lazy('alunos:lista')

logger = logging.getLogger(__name__)


class AlunoExportPDFView(LoginRequiredMixin, View):
    """View for exporting student data to PDF"""
    def get(self, request, aluno_pk):
        try:
            aluno = get_object_or_404(Aluno, pk=aluno_pk)
            template = get_template('alunos/pdf_template.html')
            context = {'aluno': aluno}
            html = template.render(context)
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{aluno.nome}_dados.pdf"'
            
            pisa.CreatePDF(html, dest=response)
            return response
            
        except Exception as e:
            logger.error(f"Error exporting PDF: {str(e)}")
            messages.error(request, 'Erro ao exportar PDF')
            return redirect('alunos:detalhe', pk=aluno_pk)

class AlunoExportExcelView(LoginRequiredMixin, View):
    """View for exporting student data to Excel"""
    def get(self, request, aluno_pk):
        try:
            aluno = get_object_or_404(Aluno, pk=aluno_pk)
            
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()
            
            # Add data to Excel
            worksheet.write(0, 0, "Nome")
            worksheet.write(0, 1, aluno.nome)
            # Add more fields as needed
            
            workbook.close()
            output.seek(0)
            
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{aluno.nome}_dados.xlsx"'
            return response
            
        except Exception as e:
            logger.error(f"Error exporting Excel: {str(e)}")
            messages.error(request, 'Erro ao exportar Excel')
            return redirect('alunos:detalhe', pk=aluno_pk)


class BaseAlunoView(LoginRequiredMixin):
    """Base view for all student-related views"""
    model = Aluno
    
    def handle_exception(self, exc):
        logger.error(f"{self.__class__.__name__} Error: {str(exc)}")
        messages.error(self.request, f"Erro: {str(exc)}")
        return super().handle_exception(exc)

class AlunoListView(BaseAlunoView, ListView):
    """View for listing students with filtering and search capabilities"""
    template_name = 'alunos/lista_alunos.html'
    context_object_name = 'alunos'
    paginate_by = 12
    
    def get_queryset(self):
        logger.debug("Starting get_queryset")
        try:
            queryset = super().get_queryset()
            logger.debug(f"Queryset count: {queryset.count()}")
            return queryset
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            return Aluno.objects.none()
    
    def apply_filters(self, queryset, cleaned_data):
        """Apply filters to queryset based on form data"""
        filters = {
            'nivel': cleaned_data.get('nivel'),
            'turno': cleaned_data.get('turno'),
            'ano': cleaned_data.get('ano')
        }
        
        # Apply basic filters
        for field, value in filters.items():
            if value:
                queryset = queryset.filter(**{field: value})
        
        # Apply search filter
        search_query = cleaned_data.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(nome__icontains=search_query) |
                Q(matricula__icontains=search_query) |
                Q(cpf__icontains=search_query)
            )
        
        return queryset

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

class AlunoCreateView(AdminRequiredMixin, BaseAlunoView, CreateView):
    """View for creating new students"""
    template_name = 'alunos/cadastrar_aluno.html'
    form_class = AlunoForm
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                aluno = form.save(commit=False)
                aluno.id = uuid.uuid4()
                
                if 'foto' in self.request.FILES:
                    photo_url = self.handle_photo_upload(aluno.id)
                    if photo_url:
                        aluno.foto_url = photo_url
                
                aluno.save()
                messages.success(self.request, 'Aluno cadastrado com sucesso!')
                return redirect('detalhe_aluno', pk=aluno.id)
                
        except Exception as e:
            logger.error(f"Error creating student: {str(e)}")
            messages.error(self.request, 'Erro ao cadastrar aluno.')
            return self.form_invalid(form)
    
    def handle_photo_upload(self, aluno_id):
        """Handle photo upload to Supabase"""
        try:
            supabase = SupabaseService()
            return supabase.upload_photo(self.request.FILES['foto'], str(aluno_id))
        except Exception as e:
            logger.error(f"Photo upload error: {str(e)}")
            return None

class AlunoDetailView(BaseAlunoView, DetailView):
    """View for displaying student details"""
    template_name = 'alunos/detalhe_aluno.html'
    context_object_name = 'aluno'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = self.get_object()
        context.update({
            'notas': Nota.objects.filter(aluno=aluno).order_by('-data'),
            'media_geral': aluno.get_media_geral(),
            'form_nota': NotaForm()
        })
        return context

class AlunoUpdateView(AdminRequiredMixin, BaseAlunoView, UpdateView):
    """View for updating student information"""
    template_name = 'alunos/editar_aluno.html'
    form_class = AlunoForm
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                aluno = form.save(commit=False)
                
                if 'foto' in self.request.FILES:
                    photo_url = self.handle_photo_upload(aluno.id)
                    if photo_url:
                        aluno.foto_url = photo_url
                
                aluno.save()
                messages.success(self.request, 'Aluno atualizado com sucesso!')
                return redirect('detalhe_aluno', pk=aluno.id)
                
        except Exception as e:
            logger.error(f"Error updating student: {str(e)}")
            messages.error(self.request, 'Erro ao atualizar aluno.')
            return self.form_invalid(form)

class AlunoDeleteView(AdminRequiredMixin, BaseAlunoView, DeleteView):
    """View for deleting students"""
    template_name = 'alunos/confirmar_exclusao.html'
    success_url = reverse_lazy('lista_alunos')
    
    def delete(self, request, *args, **kwargs):
        try:
            aluno = self.get_object()
            nome_aluno = aluno.nome
            aluno.delete()
            messages.success(request, f'Aluno "{nome_aluno}" excluído com sucesso!')
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error deleting student: {str(e)}")
            messages.error(request, 'Erro ao excluir aluno.')
            return redirect('detalhe_aluno', pk=self.kwargs['pk'])

class NotaCreateView(AdminRequiredMixin, CreateView):
    """View for adding grades"""
    model = Nota
    form_class = NotaForm
    template_name = 'alunos/adicionar_nota.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.aluno = get_object_or_404(Aluno, pk=self.kwargs['aluno_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            nota = form.save(commit=False)
            nota.aluno = self.aluno
            nota.save()
            messages.success(self.request, 'Nota adicionada com sucesso!')
            return redirect('detalhe_aluno', pk=self.aluno.pk)
        except Exception as e:
            logger.error(f"Error adding grade: {str(e)}")
            messages.error(self.request, 'Erro ao adicionar nota.')
            return self.form_invalid(form)

# API Views
class AlunoAPIView:
    """Base class for API views"""
    @staticmethod
    def json_response(data, status=200):
        return JsonResponse(data, status=status)
    
    @staticmethod
    def error_response(message, status=400):
        return JsonResponse({'error': message}, status=status)

class AlunoNotasAPIView(LoginRequiredMixin, View):  # Herda diretamente de View
    """API view for student grades"""
    def get(self, request, aluno_pk):
        try:
            aluno = get_object_or_404(Aluno, pk=aluno_pk)
            notas = Nota.objects.filter(aluno=aluno).values(
                'disciplina', 'valor', 'bimestre', 'data'
            )
            return JsonResponse({'notas': list(notas)})
        except Exception as e:
            logger.error(f"Error fetching grades: {str(e)}")
            return JsonResponse({'error': 'Erro ao buscar notas'}, status=400)

class AlunoMediaAPIView(LoginRequiredMixin, View):  # Também atualize esta classe
    """API view for student averages"""
    def get(self, request, aluno_pk):
        try:
            aluno = get_object_or_404(Aluno, pk=aluno_pk)
            medias = Nota.objects.filter(aluno=aluno).values('disciplina').annotate(
                media=Avg('valor')
            )
            return JsonResponse({'medias': list(medias)})
        except Exception as e:
            logger.error(f"Error calculating averages: {str(e)}")
            return JsonResponse({'error': 'Erro ao calcular médias'}, status=400)