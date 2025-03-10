from django.db.models import Q
from apps.alunos.models import Aluno

class DatabaseService:
    def list_alunos(self, filters=None):
        queryset = Aluno.objects.all()
        
        if filters:
            if filters.get('nivel'):
                queryset = queryset.filter(nivel=filters['nivel'])
            if filters.get('turno'):
                queryset = queryset.filter(turno=filters['turno'])
            if filters.get('ano'):
                queryset = queryset.filter(ano=filters['ano'])
            if filters.get('search'):
                queryset = queryset.filter(
                    Q(nome__icontains=filters['search']) |
                    Q(matricula__icontains=filters['search'])
                )
        
        return queryset.order_by('nivel', 'turno', 'ano', 'nome')

    def get_aluno(self, id):
        return Aluno.objects.get(id=id)

    def create_aluno(self, data):
        return Aluno.objects.create(**data)

    def update_aluno(self, id, data):
        aluno = Aluno.objects.get(id=id)
        for key, value in data.items():
            setattr(aluno, key, value)
        aluno.save()
        return aluno

    def delete_aluno(self, id):
        aluno = Aluno.objects.get(id=id)
        aluno.delete()
        return True