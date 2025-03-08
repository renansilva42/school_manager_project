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
from django.core.exceptions import ValidationError
import os


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
            
            # Add your filtering logic here
            nivel = self.request.GET.get('nivel')
            if nivel:
                queryset = queryset.filter(nivel=nivel)
                logger.debug(f"Alunos após filtro nivel={nivel}: {queryset.count()}")
                
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


class NotaDeleteView(AdminRequiredMixin, DeleteView):
    """View para exclusão de notas"""
    model = Nota
    template_name = 'alunos/confirmar_exclusao_nota.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.aluno = get_object_or_404(Aluno, pk=self.kwargs['aluno_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            nota = self.get_object()
            nota.delete()
            messages.success(request, 'Nota excluída com sucesso!')
            return redirect('detalhe_aluno', pk=self.aluno.pk)
        except Exception as e:
            logger.error(f"Erro ao excluir nota: {str(e)}")
            messages.error(request, 'Erro ao excluir nota.')
            return redirect('detalhe_aluno', pk=self.aluno.pk)

# Em /apps/alunos/views.py


class AlunoImportExcelView(LoginRequiredMixin, View):
    """View for importing student data from Excel"""
    def post(self, request):
        try:
            # Implementar lógica de importação aqui
            messages.success(request, 'Dados importados com sucesso!')
            return redirect('alunos:lista')
        except Exception as e:
            logger.error(f"Error importing Excel: {str(e)}")
            messages.error(request, 'Erro ao importar Excel')
            return redirect('alunos:lista')    


class NotaUpdateView(LoginRequiredMixin, UpdateView):
    model = Nota
    form_class = NotaForm
    template_name = 'alunos/nota_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.aluno = get_object_or_404(Aluno, pk=kwargs['aluno_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('alunos:detalhe', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        
        form.instance.aluno = self.aluno
        messages.success(self.request, 'Nota atualizada com sucesso!')
        return super().form_valid(form)

class AlunoCreateView(AdminRequiredMixin, BaseAlunoView, CreateView):
    template_name = 'alunos/cadastrar_aluno.html'
    form_class = AlunoForm
    
    def form_valid(self, form):
        try:
            logger.info("Iniciando processo de cadastro de aluno")
            with transaction.atomic():
                aluno = form.save(commit=False)
                # Convertendo UUID para string antes de salvar
                aluno.id = str(uuid.uuid4())
                
                logger.debug(f"Dados do aluno antes de salvar: {aluno.__dict__}")
                
                # Salva primeiro o aluno para ter o ID
                aluno.save()
                logger.info(f"Aluno salvo com ID: {aluno.id}")
                
                # Processa a foto se existir
                if 'foto' in self.request.FILES:
                    try:
                        foto = self.request.FILES['foto']
                        logger.debug(f"Processando foto: tamanho={foto.size}, tipo={foto.content_type}")
                        
                        # Validação adicional da foto
                        if not foto.content_type.startswith('image/'):
                            raise ValidationError("Arquivo não é uma imagem válida")
                        
                        aluno.foto = foto
                        aluno.save()
                        logger.info("Foto do aluno processada e salva com sucesso")
                    except Exception as e:
                        logger.error(f"Erro ao processar foto: {str(e)}")
                        raise
                
                messages.success(self.request, 'Aluno cadastrado com sucesso!')
                logger.info(f"Cadastro do aluno {aluno.nome} finalizado com sucesso")
                return redirect('alunos:detalhe', pk=aluno.id)
                
        except Exception as e:
            logger.error(f"Erro no cadastro do aluno: {str(e)}")
            messages.error(self.request, f'Erro ao cadastrar aluno: {str(e)}')
            return self.form_invalid(form)


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

class AlunoDeleteView(BaseAlunoView, DeleteView):
    template_name = 'alunos/confirmar_exclusao.html'
    success_url = reverse_lazy('alunos:lista')
    
    def delete(self, request, *args, **kwargs):
        try:
            aluno = self.get_object()
            nome_aluno = aluno.nome
            
            # Remove a foto se existir
            if aluno.foto:
                try:
                    os.remove(aluno.foto.path)
                except Exception as e:
                    logger.error(f"Erro ao remover foto: {str(e)}")
            
            # Exclui o aluno
            response = super().delete(request, *args, **kwargs)
            
            messages.success(
                request,
                f'O aluno "{nome_aluno}" foi excluído com sucesso!'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao excluir aluno: {str(e)}")
            messages.error(
                request,
                'Não foi possível excluir o aluno. Por favor, tente novamente.'
            )
            return redirect('alunos:lista')

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