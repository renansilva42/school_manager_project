from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.template.loader import render_to_string, get_template
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db.models import Avg, Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.views import View
from services.database import SupabaseService
from .forms import AlunoForm, NotaForm, AlunoFilterForm
from .models import Aluno, Nota
from .mixins import AdminRequiredMixin
from xhtml2pdf import pisa
import xlsxwriter
import pandas as pd
from io import BytesIO
import uuid
import logging
import os
from django.urls import reverse_lazy
from django.conf import settings
import os
import base64
from io import BytesIO
import uuid
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

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
            
            # Obter parâmetros da requisição
            nivel = self.request.GET.get('nivel')
            turno = self.request.GET.get('turno')
            ano = self.request.GET.get('ano')
            search = self.request.GET.get('search')
            
            # Aplicar filtros
            if nivel:
                queryset = queryset.filter(nivel=nivel)
            if turno:
                queryset = queryset.filter(turno=turno)
            if ano:
                queryset = queryset.filter(ano=ano)
            if search:
                queryset = queryset.filter(
                    Q(nome__icontains=search) |
                    Q(matricula__icontains=search) |
                    Q(cpf__icontains=search)
                )
                
            logger.debug(f"Queryset final count: {queryset.count()}")
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
            # Adicione o total de alunos na resposta JSON
            return JsonResponse({
                'html': html,
                'total_alunos': context['paginator'].count  # Adiciona o total de alunos
            })
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


class AlunoImportExcelView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View for importing students from Excel file"""
    
    def post(self, request):
        try:
            excel_file = request.FILES.get('file')
            
            if not excel_file:
                raise ValidationError('Nenhum arquivo foi enviado')
                
            if not excel_file.name.endswith(('.xls', '.xlsx')):
                raise ValidationError('O arquivo deve ser no formato Excel (.xls ou .xlsx)')

            # Read Excel file
            df = pd.read_excel(excel_file)
            
            required_columns = [
                'nome', 'data_nascimento', 'cpf', 'matricula', 
                'nivel', 'turno', 'ano'
            ]
            
            # Validate columns
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise ValidationError(f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}')

            success_count = 0
            errors = []
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    aluno_data = {
                        'nome': row['nome'],
                        'data_nascimento': pd.to_datetime(row['data_nascimento']).date(),
                        'cpf': str(row['cpf']),
                        'matricula': str(row['matricula']),
                        'nivel': row['nivel'],
                        'turno': row['turno'],
                        'ano': str(row['ano']),
                        'email': row.get('email', ''),
                        'telefone': row.get('telefone', ''),
                        'endereco': row.get('endereco', ''),
                        'cidade': row.get('cidade', ''),
                        'uf': row.get('uf', ''),
                        'nome_responsavel1': row.get('nome_responsavel1', ''),
                        'telefone_responsavel1': row.get('telefone_responsavel1', ''),
                        'nome_responsavel2': row.get('nome_responsavel2', ''),
                        'telefone_responsavel2': row.get('telefone_responsavel2', ''),
                        'observacoes': row.get('observacoes', '')
                    }
                    
                    form = AlunoForm(aluno_data)
                    if form.is_valid():
                        form.save()
                        success_count += 1
                    else:
                        errors.append(f'Linha {index + 2}: {form.errors}')
                        
                except Exception as e:
                    errors.append(f'Linha {index + 2}: {str(e)}')

            # Prepare response message
            if success_count > 0:
                messages.success(request, f'{success_count} alunos importados com sucesso!')
            
            if errors:
                error_message = "Erros durante a importação:\n" + "\n".join(errors)
                messages.error(request, error_message)
                
            return JsonResponse({
                'success': True,
                'imported_count': success_count,
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"Error importing Excel: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


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
    
    def get(self, request, *args, **kwargs):
        storage = messages.get_messages(request)
        storage.used = True
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            logger.info("Iniciando processo de cadastro de aluno")
            
            with transaction.atomic():
                aluno = form.save(commit=False)
                aluno.id = str(uuid.uuid4())
                
                # Log dos dados recebidos
                logger.debug(f"Dados do formulário: {form.cleaned_data}")
                logger.debug(f"Arquivos recebidos: {self.request.FILES}")
                logger.debug(f"Dados do aluno antes de salvar: {aluno.__dict__}")
                
                # Processa foto base64 se existir
                foto_base64 = self.request.POST.get('foto_base64')
                if foto_base64 and foto_base64.startswith('data:image'):
                    try:
                        logger.debug("Processando foto base64 da câmera")
                        # Extrai os dados base64
                        format, imgstr = foto_base64.split(';base64,')
                        ext = format.split('/')[-1]
                        
                        # Converte base64 para bytes
                        imgdata = base64.b64decode(imgstr)
                        
                        # Processa a imagem
                        buffer = BytesIO(imgdata)
                        img = Image.open(buffer)
                        
                        # Converte para RGB se necessário
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                            logger.debug("Imagem convertida para RGB")
                        
                        # Redimensiona se necessário
                        if img.height > 800 or img.width > 800:
                            output_size = (800, 800)
                            img.thumbnail(output_size)
                            logger.debug(f"Imagem redimensionada para {output_size}")
                        
                        # Salva a imagem processada
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85, optimize=True)
                        output.seek(0)
                        
                        # Cria um arquivo para o Django
                        aluno.foto = InMemoryUploadedFile(
                            output,
                            'foto',
                            f'camera_photo_{uuid.uuid4().hex[:8]}.jpg',
                            'image/jpeg',
                            output.getbuffer().nbytes,
                            None
                        )
                        logger.info("Foto da câmera processada com sucesso")
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar foto base64: {str(e)}")
                        raise ValidationError(f"Erro ao processar foto da câmera: {str(e)}")
                
                # Processa foto do arquivo se existir
                elif 'foto' in self.request.FILES:
                    try:
                        foto = self.request.FILES['foto']
                        logger.debug(f"Processando foto do arquivo: tamanho={foto.size}, tipo={foto.content_type}")
                        
                        if not foto.content_type.startswith('image/'):
                            raise ValidationError("Arquivo não é uma imagem válida")
                        
                        # Processa a imagem
                        img = Image.open(foto)
                        
                        # Converte para RGB se necessário
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                        
                        # Redimensiona se necessário
                        if img.height > 800 or img.width > 800:
                            output_size = (800, 800)
                            img.thumbnail(output_size)
                        
                        # Salva a imagem processada
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85, optimize=True)
                        output.seek(0)
                        
                        aluno.foto = InMemoryUploadedFile(
                            output,
                            'foto',
                            f"{foto.name.split('.')[0]}.jpg",
                            'image/jpeg',
                            output.getbuffer().nbytes,
                            None
                        )
                        logger.info("Foto do arquivo processada com sucesso")
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar foto do arquivo: {str(e)}")
                        raise ValidationError(f"Erro ao processar foto: {str(e)}")
                
                # Salva o aluno
                aluno.save()
                logger.info(f"Aluno salvo com ID: {aluno.id}")
                
                messages.success(self.request, 'Aluno cadastrado com sucesso!')
                logger.info(f"Cadastro do aluno {aluno.nome} finalizado com sucesso")
                return redirect('alunos:detalhe', pk=aluno.id)
                
        except ValidationError as e:
            logger.error(f"Erro de validação: {str(e)}")
            messages.error(self.request, str(e))
            return self.form_invalid(form)
            
        except Exception as e:
            logger.error(f"Erro no cadastro do aluno: {str(e)}", exc_info=True)
            messages.error(self.request, f'Erro ao cadastrar aluno: {str(e)}')
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Confirmar Exclusão'
        return context
    
class AlunoDetailView(BaseAlunoView, DetailView):
    """View for displaying detailed student information"""
    template_name = 'alunos/detalhe_aluno.html'
    context_object_name = 'aluno'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = self.get_object()
        context['notas'] = aluno.nota_set.all().order_by('disciplina', 'bimestre')
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
                # Change this line to use the correct URL name
                return redirect('alunos:detalhe', pk=aluno.id)
                
        except Exception as e:
            logger.error(f"Error updating student: {str(e)}")
            messages.error(self.request, 'Erro ao atualizar aluno.')
            return self.form_invalid(form)


class AlunoDeleteView(BaseAlunoView, DeleteView):
    template_name = 'alunos/confirmar_exclusao.html'
    success_url = reverse_lazy('alunos:lista')
    
    def delete(self, request, *args, **kwargs):
        try:
            logger.info(f"Iniciando processo de exclusão de aluno")
            
            self.object = self.get_object()
            nome_aluno = self.object.nome
            aluno_id = self.object.id
            
            logger.info(f"Aluno encontrado - ID: {aluno_id}, Nome: {nome_aluno}")
            
            # Remove a foto se existir
            if self.object.foto:
                try:
                    logger.debug(f"Tentando remover foto do aluno {nome_aluno}")
                    if os.path.exists(self.object.foto.path):
                        os.remove(self.object.foto.path)
                        logger.info(f"Foto do aluno {nome_aluno} removida com sucesso")
                except Exception as e:
                    logger.warning(f"Erro ao remover foto do aluno {nome_aluno}: {str(e)}")
            
            # Executa a deleção dentro de uma transação
            with transaction.atomic():
                logger.debug(f"Iniciando transação para exclusão do aluno {nome_aluno}")
                
                # Remove notas relacionadas
                notas_count = self.object.nota_set.count()
                logger.info(f"Removendo {notas_count} notas relacionadas ao aluno {nome_aluno}")
                self.object.nota_set.all().delete()
                
                # Remove o aluno
                logger.debug(f"Executando exclusão do aluno {nome_aluno}")
                self.object.delete()
                
                logger.info(f"Aluno {nome_aluno} e seus dados relacionados foram excluídos com sucesso")
                
                messages.success(
                    request,
                    f'O aluno "{nome_aluno}" foi excluído com sucesso!'
                )
                
                return HttpResponseRedirect(self.success_url)
                
        except Exception as e:
            logger.error(f"Erro crítico ao excluir aluno: {str(e)}", exc_info=True)
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

class DownloadTemplateExcelView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            file_path = os.path.join(settings.STATIC_ROOT, 'excel', 'alunos_template.xlsx')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(
                        fh.read(),
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    response['Content-Disposition'] = 'attachment; filename=modelo_importacao_alunos.xlsx'
                    return response
            raise FileNotFoundError
            
        except Exception as e:
            messages.error(request, 'Erro ao baixar o modelo de importação.')
            return redirect('alunos:lista')

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