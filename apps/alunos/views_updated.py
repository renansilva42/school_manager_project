#/apps/alunos/views_updated.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.template.loader import render_to_string, get_template
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db.models import Avg, Q, Case, When
from django.db import NotSupportedError, OperationalError
from collections import OrderedDict
from django.http import Http404
from django.core.paginator import InvalidPage
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.views import View
from services.database import DatabaseService
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
from django.http import Http404
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from .serializers import AlunoFotoSerializer
from .models import Aluno
from rest_framework import serializers


success_url = reverse_lazy('alunos:lista')

logger = logging.getLogger(__name__)

class AlunoFotoView(generics.UpdateAPIView):
    serializer_class = AlunoFotoSerializer
    parser_classes = (MultiPartParser,)
    
    def get_object(self):
        return get_object_or_404(Aluno, pk=self.kwargs['pk'])
    
    def perform_update(self, serializer):
        try:
            aluno = self.get_object()
            
            # Remove foto antiga se existir
            if aluno.foto:
                try:
                    default_storage.delete(aluno.foto.name)
                except Exception as e:
                    logger.warning(f"Erro ao deletar foto antiga: {e}")
            
            # Gera nome único para arquivo
            foto = serializer.validated_data['foto']
            ext = foto.name.split('.')[-1].lower()
            novo_nome = f"alunos/fotos/{aluno.id}_{uuid.uuid4().hex[:8]}.{ext}"
            
            # Salva nova foto
            serializer.save(foto=novo_nome)
            
        except Exception as e:
            logger.error(f"Erro ao processar foto: {e}")
            raise serializers.ValidationError(f"Erro ao processar imagem: {str(e)}")


class AlunoExportPDFView(LoginRequiredMixin, View):
    """View for exporting student data to PDF"""
    
    def get_object(self, queryset=None):
        try:
            aluno = super().get_object(queryset)
            return aluno
        except Aluno.DoesNotExist:
            messages.error(self.request, 'Aluno não encontrado')
            return redirect('alunos:lista')
    
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
    def get_object(self, queryset=None):
        try:
            aluno = super().get_object(queryset)
            return aluno
        except Aluno.DoesNotExist:
            messages.error(self.request, 'Aluno não encontrado')
            return redirect('alunos:lista')
    
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
    paginate_by = 20  # Aumentado para otimizar a experiência de scroll
    
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
                    Q(cpf__icontains=search) & ~Q(cpf__isnull=True) & ~Q(cpf='')  # Only search non-empty CPFs
                )
            
            # Otimização: selecione apenas os campos necessários para a exibição na lista
            queryset = queryset.only('id', 'nome', 'matricula', 'nivel', 'turno', 'ano', 'foto')
            
            # Garantir que não existam duplicatas usando uma solução que funcione em qualquer banco de dados
            try:
                # Tentar usar distinct com campo específico (funciona no PostgreSQL)
                distinct_queryset = queryset.order_by('id').distinct('id')
                
                # Verificar se o método distinct realmente removeu duplicatas
                # Um teste simples é comparar a contagem antes e depois
                count_before = queryset.count()
                count_after = distinct_queryset.count()
                
                if count_before != count_after:
                    logger.debug(f"PostgreSQL distinct por ID aplicado com sucesso: {count_before} -> {count_after}")
                    queryset = distinct_queryset
                else:
                    # Se a contagem não mudou, podemos precisar da abordagem alternativa
                    raise NotSupportedError("Distinct não removeu duplicatas, usando abordagem alternativa")
                
            except (NotSupportedError, OperationalError) as e:
                logger.debug(f"Distinct por ID não suportado: {str(e)}. Usando abordagem alternativa.")
                
                # Usar uma abordagem em memória para garantir resultados distintos sem perder a ordenação
                # Obter IDs únicos, preservando a ordem original
                id_list = list(queryset.values_list('id', flat=True))
                unique_ids = list(OrderedDict.fromkeys(id_list))
                
                # Usar Case/When para preservar a ordem original dos IDs
                preserved_order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(unique_ids)])
                
                # Aplicar o filtro e ordenação
                queryset = queryset.filter(id__in=unique_ids).order_by(preserved_order)
                
                logger.debug(f"Deduplicated usando abordagem alternativa: {len(id_list)} -> {len(unique_ids)}")
            
            # Registrar a contagem final após todos os filtros e otimizações
            final_count = queryset.count()
            logger.debug(f"Queryset final count: {final_count}")
            
            return queryset
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}", exc_info=True)
            return Aluno.objects.none()
    
    def paginate_queryset(self, queryset, page_size):
        """
        Sobrescrever método de paginação para adicionar log
        e verificar duplicatas.
        """
        paginator = self.get_paginator(
            queryset, page_size, orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty())
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                page_number = 1
        try:
            page = paginator.page(page_number)
            
            # Registro adicional para depuração da paginação
            logger.debug(f"Página {page_number}: {len(page.object_list)} objetos")
            
            # Verificação extra para duplicatas no conjunto de resultados paginados
            paginated_ids = [obj.id for obj in page.object_list]
            unique_paginated_ids = set(paginated_ids)
            
            if len(paginated_ids) != len(unique_paginated_ids):
                logger.warning(
                    f"Duplicatas detectadas na página {page_number}: "
                    f"{len(paginated_ids) - len(unique_paginated_ids)} duplicatas."
                )
                
                # Se detectarmos duplicatas, vamos fazer uma deduplação final
                seen_ids = set()
                unique_objs = []
                
                for obj in page.object_list:
                    if obj.id not in seen_ids:
                        seen_ids.add(obj.id)
                        unique_objs.append(obj)
                
                page.object_list = unique_objs
                logger.debug(f"Objetos após deduplação final: {len(unique_objs)}")
            
            return (paginator, page, page.object_list, page.has_other_pages())
        except InvalidPage as e:
            logger.error(f"Página inválida ({page_number}): {str(e)}")
            raise Http404("Página inválida.")
    
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
                Q(cpf__icontains=search_query) & ~Q(cpf__isnull=True) & ~Q(cpf='')  # Only search non-empty CPFs
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AlunoFilterForm(self.request.GET)
        
        # Verificar se estamos no modo de scroll infinito
        context['infinite_scroll'] = True  # Definir como padrão para melhorar experiência mobile
        
        # Permitir que o JavaScript identifique que a página usa scroll infinito
        context['has_infinite_scroll'] = True
        
        # Verificar e adicionar se há mais páginas
        if 'page_obj' in context:
            context['has_more'] = context['page_obj'].has_next()
        
        # Detectar dispositivo móvel
        user_agent = self.request.META.get('HTTP_USER_AGENT', '').lower()
        is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
        context['is_mobile'] = is_mobile
        
        # Ajustar layout com base no dispositivo
        if is_mobile:
            context['card_columns'] = 1
        else:
            context['card_columns'] = 3
            
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            current_page = context['page_obj'].number
            
            # Extrair ID de todos os alunos nesta página para debugging
            if logger.isEnabledFor(logging.DEBUG):
                alunos_ids = [aluno.id for aluno in context['alunos']]
                logger.debug(f"IDs dos alunos na resposta AJAX (página {current_page}): {alunos_ids}")
                
                # Verificar duplicatas
                if len(alunos_ids) != len(set(alunos_ids)):
                    logger.warning(f"AVISO: Duplicatas detectadas na resposta AJAX (página {current_page})")
            
            # Renderizar os cards de alunos com otimizações para mobile
            html = render_to_string(
                'alunos/partials/lista_alunos_partial.html',
                {
                    'alunos': context['page_obj'],
                    'paginator': context['paginator'],
                    'page_obj': context['page_obj'],
                    'is_paginated': context['is_paginated'],
                    'request': self.request,
                    'is_mobile': context.get('is_mobile', False),
                    'has_more': context['page_obj'].has_next(),
                    'infinite_scroll': True
                },
                request=self.request
            )
            
            # Construir a resposta otimizada
            response_data = {
                'html': html,
                'total_alunos': context['paginator'].count,
                'current_page': current_page,
                'total_pages': context['paginator'].num_pages,
                'has_more': context['page_obj'].has_next(),
                'mode': 'replace' if current_page == 1 else 'append',
                'aluno_ids': [str(aluno.id) for aluno in context['page_obj']]  # Incluir IDs para verificação de duplicatas no frontend
            }
            
            return JsonResponse(response_data)
        
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
            
            # Atualizar colunas obrigatórias (remover data_nascimento e cpf)
            required_columns = [
                'nome', 'matricula', 
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
                        'matricula': str(row['matricula']),
                        'nivel': row['nivel'],
                        'turno': row['turno'],
                        'ano': str(row['ano']),
                        # Tornar data_nascimento opcional
                        'data_nascimento': pd.to_datetime(row['data_nascimento']).date() if pd.notna(row.get('data_nascimento')) else None,
                        # Tornar CPF opcional
                        'cpf': str(row['cpf']) if pd.notna(row.get('cpf')) else None,
                        # Tornar data_matricula opcional
                        'data_matricula': pd.to_datetime(row['data_matricula']).date() if pd.notna(row.get('data_matricula')) else None,
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
    success_url = reverse_lazy('alunos:lista')
    
    def get(self, request, *args, **kwargs):
        storage = messages.get_messages(request)
        storage.used = True
        return super().get(request, *args, **kwargs)
        
    def form_invalid(self, form):
        """
        If the form is invalid, preserve the photo data so it doesn't disappear
        when the form is resubmitted.
        """
        # Get the photo data from the request
        foto_base64 = self.request.POST.get('foto_base64')
        if foto_base64 and foto_base64.startswith('data:image'):
            # Add the base64 data back to the form so it's available in the template
            form.data = form.data.copy()
            form.data['foto_base64'] = foto_base64
            
            # Log that we're preserving the photo
            logger.info("Preservando foto após erro de validação do formulário")
            
        # Log form errors for debugging
        logger.error(f"Erros de validação do formulário: {form.errors}")
            
        return super().form_invalid(form)
    
    def form_valid(self, form):
        try:
            logger.info("Iniciando processo de cadastro de aluno")
            
            with transaction.atomic():
                # Generate new UUID for student
                aluno_id = str(uuid.uuid4())
                
                # Prepare student data
                data = form.cleaned_data.copy()
                data['id'] = aluno_id
                
                # Initialize Supabase service
                db = DatabaseService()
                
                # Handle photo upload
                photo_file = None
                photo_url = None
                
                # Process base64 photo from camera
                foto_base64 = self.request.POST.get('foto_base64')
                if foto_base64 and foto_base64.startswith('data:image'):
                    try:
                        logger.debug("Processing base64 photo from camera")
                        format, imgstr = foto_base64.split(';base64,')
                        ext = format.split('/')[-1]
                        
                        # Convert base64 to bytes
                        imgdata = base64.b64decode(imgstr)
                        buffer = BytesIO(imgdata)
                        
                        # Process image
                        img = Image.open(buffer)
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                        
                        # Resize if necessary
                        if img.height > 800 or img.width > 800:
                            output_size = (800, 800)
                            img.thumbnail(output_size)
                        
                        # Save processed image
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85)
                        output.seek(0)
                        
                        photo_file = InMemoryUploadedFile(
                            output,
                            'foto',
                            f'camera_photo_{aluno_id}.jpg',
                            'image/jpeg',
                            output.getbuffer().nbytes,
                            None
                        )
                        
                    except Exception as e:
                        logger.error(f"Error processing base64 photo: {str(e)}")
                
                # Process photo from file upload
                elif 'foto' in self.request.FILES:
                    try:
                        photo_file = self.request.FILES['foto']
                        if not photo_file.content_type.startswith('image/'):
                            raise ValidationError("Invalid image file")
                        
                        img = Image.open(photo_file)
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                        
                        if img.height > 800 or img.width > 800:
                            output_size = (800, 800)
                            img.thumbnail(output_size)
                        
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85)
                        output.seek(0)
                        
                        photo_file = InMemoryUploadedFile(
                            output,
                            'foto',
                            f"{photo_file.name.split('.')[0]}.jpg",
                            'image/jpeg',
                            output.getbuffer().nbytes,
                            None
                        )
                        
                    except Exception as e:
                        logger.error(f"Error processing uploaded photo: {str(e)}")
                
                # Upload photo to Supabase if exists
                if photo_file:
                    photo_url = db.upload_photo(photo_file, aluno_id)
                    if photo_url:
                        data['foto'] = photo_url
                    else:
                        messages.warning(self.request, 'Aluno criado, mas houve um problema ao salvar a foto.')
                
                # Create student in Supabase
                response = db.create_aluno(data)
                
                if not response:
                    raise Exception("Falha ao criar aluno no Supabase")
                
                messages.success(self.request, 'Aluno cadastrado com sucesso!')
                return redirect('alunos:detalhe', pk=aluno_id)
                
        except Exception as e:
            logger.error(f"Error creating student: {str(e)}", exc_info=True)
            messages.error(self.request, f'Erro ao cadastrar aluno: {str(e)}')
            return self.form_invalid(form)

        
class AlunoDetailView(BaseAlunoView, DetailView):
    """View for displaying detailed student information"""
    template_name = 'alunos/detalhe_aluno.html'
    context_object_name = 'aluno'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = self.get_object()
        context['notas'] = aluno.nota_set.all().order_by('disciplina', 'bimestre')
        return context
    
    def get_object(self, queryset=None):
        try:
            aluno = super().get_object(queryset)
            return aluno
        except Aluno.DoesNotExist:
            messages.error(self.request, 'Aluno não encontrado')
            return redirect('alunos:lista')

class AlunoUpdateView(AdminRequiredMixin, BaseAlunoView, UpdateView):
    template_name = 'alunos/editar_aluno.html'
    form_class = AlunoForm
    
    def get_object(self, queryset=None):
        try:
            aluno = super().get_object(queryset)
            return aluno
        except Aluno.DoesNotExist:
            messages.error(self.request, 'Aluno não encontrado')
            return redirect('alunos:lista')
            
    def form_invalid(self, form):
        """
        If the form is invalid, preserve the photo data so it doesn't disappear
        when the form is resubmitted.
        """
        # Get the photo data from the request
        foto_base64 = self.request.POST.get('foto_base64')
        if foto_base64 and foto_base64.startswith('data:image'):
            # Add the base64 data back to the form so it's available in the template
            form.data = form.data.copy()
            form.data['foto_base64'] = foto_base64
            
            # Log that we're preserving the photo
            logger.info("Preservando foto após erro de validação do formulário")
            
        # Log form errors for debugging
        logger.error(f"Erros de validação do formulário: {form.errors}")
            
        return super().form_invalid(form)
    
    def form_valid(self, form):
        try:
            logger.info("Iniciando processo de atualização de aluno")
            
            with transaction.atomic():
                aluno_id = self.object.id
                data = form.cleaned_data.copy()
                
                db = DatabaseService()
                
                # Processamento da foto
                photo_file = self.request.FILES.get('foto')
                photo_url = None
                
                # Process base64 photo from camera
                foto_base64 = self.request.POST.get('foto_base64')
                if foto_base64 and foto_base64.startswith('data:image'):
                    try:
                        logger.debug("Processing base64 photo from camera")
                        format, imgstr = foto_base64.split(';base64,')
                        ext = format.split('/')[-1]
                        
                        # Convert base64 to bytes
                        imgdata = base64.b64decode(imgstr)
                        buffer = BytesIO(imgdata)
                        
                        # Process image
                        img = Image.open(buffer)
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                        
                        # Resize if necessary
                        if img.height > 800 or img.width > 800:
                            output_size = (800, 800)
                            img.thumbnail(output_size)
                        
                        # Save processed image
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85)
                        output.seek(0)
                        
                        photo_file = InMemoryUploadedFile(
                            output,
                            'foto',
                            f'camera_photo_{aluno_id}.jpg',
                            'image/jpeg',
                            output.getbuffer().nbytes,
                            None
                        )
                        
                    except Exception as e:
                        logger.error(f"Error processing base64 photo: {str(e)}")
                
                # Process photo from file upload
                if photo_file:
                    try:
                        # Gere um nome de arquivo relativo
                        filename = f"alunos/fotos/{uuid.uuid4().hex}.jpg"
                        
                        # Use o storage do Django para salvar o arquivo
                        from django.core.files.storage import default_storage
                        path = default_storage.save(filename, photo_file)
                        
                        # Atualize o caminho da foto nos dados
                        data['foto'] = path
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar foto: {str(e)}")
                        messages.warning(self.request, 'Erro ao processar a foto.')
                
                # Check if photo should be removed
                if 'foto-clear' in self.request.POST:
                    data['foto'] = None
                        
                # Atualize o aluno no banco de dados
                response = db.update_aluno(aluno_id, data)
                
                if not response:
                    raise Exception("Falha ao atualizar aluno no banco de dados")
                
                messages.success(self.request, 'Aluno atualizado com sucesso!')
                return redirect('alunos:detalhe', pk=aluno_id)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar aluno: {str(e)}")
            messages.error(self.request, 'Erro ao atualizar aluno.')
            return self.form_invalid(form)

class AlunoDeleteView(BaseAlunoView, DeleteView):
    template_name = 'alunos/confirmar_exclusao.html'
    success_url = reverse_lazy('alunos:lista')
    
    def get_object(self, queryset=None):
        try:
            aluno = super().get_object(queryset)
            return aluno
        except Aluno.DoesNotExist:
            messages.error(self.request, 'Aluno não encontrado')
            return redirect('alunos:lista')
    
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            aluno_id = self.object.id
            
            db = DatabaseService()
            
            # Delete photo from Supabase if exists
            if self.object.foto:
                db.delete_photo(aluno_id)
            
            # Delete student from Supabase
            response = db.delete_aluno(aluno_id)
            
            if not response:
                raise Exception("Falha ao excluir aluno no Supabase")
            
            messages.success(request, 'Aluno excluído com sucesso!')
            return HttpResponseRedirect(self.success_url)
            
        except Exception as e:
            logger.error(f"Error deleting student: {str(e)}")
            messages.error(request, 'Erro ao excluir aluno.')
            return redirect('alunos:lista')



class NotaCreateView(AdminRequiredMixin, CreateView):
    """View for adding grades"""
    model = Nota
    form_class = NotaForm
    template_name = 'alunos/adicionar_nota.html'
    
    def get_object(self, queryset=None):
        try:
            aluno = super().get_object(queryset)
            return aluno
        except Aluno.DoesNotExist:
            messages.error(self.request, 'Aluno não encontrado')
            return redirect('alunos:lista')
    
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

class ListaAlunosView(LoginRequiredMixin, ListView):
    model = Aluno
    template_name = 'alunos/lista_alunos.html'
    context_object_name = 'alunos'
    paginate_by = 9
