# escola_manager/views.py
from django.views import View
from django.http import HttpResponse

class AlunoFotoView(View):
    def get(self, request, pk):
        # Implemente a lógica para retornar a foto do aluno
        pass