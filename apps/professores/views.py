from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Professor, AtribuicaoDisciplina, DisponibilidadeHorario, Disciplina
from .forms import ProfessorForm, AtribuicaoDisciplinaForm, DisponibilidadeHorarioForm, DisciplinaForm
from django.core.exceptions import ValidationError

from django.shortcuts import render, redirect

class ProfessorListView(LoginRequiredMixin, ListView):
    model = Professor
    template_name = 'professores/professor_list.html'
    context_object_name = 'professores'
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        professores = Professor.objects.all()
        if not professores.exists():
            return redirect('professores:sem_professores')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Professor.objects.all()
    
class DisciplinaListView(LoginRequiredMixin, ListView):
    model = Disciplina
    template_name = 'professores/disciplina_list.html'
    context_object_name = 'disciplinas'
    
    def get_queryset(self):
        return Disciplina.objects.filter(ativo=True)

def sem_professores(request):
    return render(request, 'professores/sem_professores.html')
class DisciplinaCreateView(LoginRequiredMixin, CreateView):
    model = Disciplina
    form_class = DisciplinaForm
    template_name = 'professores/disciplina_form.html'
    success_url = reverse_lazy('professores:disciplina_list')

class DisciplinaUpdateView(LoginRequiredMixin, UpdateView):
    model = Disciplina
    form_class = DisciplinaForm
    template_name = 'professores/disciplina_form.html'
    success_url = reverse_lazy('professores:disciplina_list')
    
def desativar_professor(request, pk):
    professor = get_object_or_404(Professor, pk=pk)
    professor.ativo = False
    professor.save()
    messages.success(request, 'Professor desativado com sucesso.')
    return redirect('professores:professor_list')
    
class ProfessorCreateView(LoginRequiredMixin, CreateView):
    model = Professor
    form_class = ProfessorForm
    template_name = 'professores/cadastro_professor.html'
    success_url = reverse_lazy('professores:professor_list')  # Adicione o namespace 'professores:'



from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.utils import timezone
from django.contrib import messages

class AtribuicaoDisciplinaCreateView(LoginRequiredMixin, View):
    template_name = 'professores/atribuir_disciplina.html'
    success_url = reverse_lazy('professores:atribuicao_create')

    def get(self, request, *args, **kwargs):
        professores = Professor.objects.all()
        disciplinas = Disciplina.objects.filter(ativo=True)
        turmas = AtribuicaoDisciplina.objects.values_list('turma', flat=True).distinct()
        atribuicoes = AtribuicaoDisciplina.objects.all()

        # Filtering
        professor_filter = request.GET.get('professor')
        turma_filter = request.GET.get('turma')

        if professor_filter:
            atribuicoes = atribuicoes.filter(professor_id=professor_filter)
        if turma_filter:
            atribuicoes = atribuicoes.filter(turma=turma_filter)

        form = AtribuicaoDisciplinaForm()

        context = {
            'professores': professores,
            'disciplinas': disciplinas,
            'turmas': turmas,
            'atribuicoes': atribuicoes,
            'form': form,
            'professor_filter': professor_filter,
            'turma_filter': turma_filter,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = AtribuicaoDisciplinaForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Atribuições criadas com sucesso.')
                return redirect(self.success_url)
            except ValidationError as e:
                form.add_error(None, e)
        professores = Professor.objects.all()
        disciplinas = Disciplina.objects.filter(ativo=True)
        turmas = AtribuicaoDisciplina.objects.values_list('turma', flat=True).distinct()
        atribuicoes = AtribuicaoDisciplina.objects.all()
        context = {
            'professores': professores,
            'disciplinas': disciplinas,
            'turmas': turmas,
            'atribuicoes': atribuicoes,
            'form': form,
        }
        return render(request, self.template_name, context)

class AtribuicaoDisciplinaDeleteView(LoginRequiredMixin, DeleteView):
    model = AtribuicaoDisciplina
    template_name = 'professores/atribuir_disciplina_confirm_delete.html'
    success_url = reverse_lazy('professores:atribuicao_create')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Atribuição removida com sucesso.')
        return super().delete(request, *args, **kwargs)

class DisponibilidadeHorarioCreateView(LoginRequiredMixin, CreateView):
    model = DisponibilidadeHorario
    form_class = DisponibilidadeHorarioForm
    template_name = 'professores/horarios_disponibilidade.html'
    success_url = reverse_lazy('professores:professor_list')  # Ajuste para uma URL existente

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['horarios'] = ['07:00', '08:00', '09:00', '10:00', '11:00',
                             '13:00', '14:00', '15:00', '16:00', '17:00']
        context['dias_semana'] = dict(DisponibilidadeHorario.DIAS_SEMANA)
        return context
