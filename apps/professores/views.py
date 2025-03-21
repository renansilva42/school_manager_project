from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Professor, AtribuicaoDisciplina, DisponibilidadeHorario
from .forms import ProfessorForm, AtribuicaoDisciplinaForm, DisponibilidadeHorarioForm

class ProfessorListView(LoginRequiredMixin, ListView):
    model = Professor
    template_name = 'professores/professor_list.html'
    context_object_name = 'professores'
    paginate_by = 10

class ProfessorCreateView(LoginRequiredMixin, CreateView):
    model = Professor
    form_class = ProfessorForm
    template_name = 'professores/cadastro_professor.html'
    success_url = reverse_lazy('professores:professor_list')  # Adicione o namespace 'professores:'

class AtribuicaoDisciplinaCreateView(LoginRequiredMixin, CreateView):
    model = AtribuicaoDisciplina
    form_class = AtribuicaoDisciplinaForm
    template_name = 'professores/atribuir_disciplina.html'
    success_url = reverse_lazy('professores:professor_list')  # Ajuste para uma URL existente

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