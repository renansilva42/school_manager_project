from django.core.management.base import BaseCommand
from django.db import models  # Adicione esta importação
from apps.professores.models import AtribuicaoDisciplina

class Command(BaseCommand):
    help = 'Remove registros duplicados de AtribuicaoDisciplina'

    def handle(self, *args, **options):
        # Identificar e remover duplicatas
        duplicates = (
            AtribuicaoDisciplina.objects.values(
                'professor', 'disciplina', 'turma', 'ano_letivo'
            )
            .annotate(count=models.Count('id'))
            .filter(count__gt=1)
        )

        for dup in duplicates:
            # Manter o registro mais antigo
            registros = AtribuicaoDisciplina.objects.filter(
                professor=dup['professor'],
                disciplina=dup['disciplina'],
                turma=dup['turma'],
                ano_letivo=dup['ano_letivo']
            ).order_by('created_at')
            
            # Deletar duplicatas mantendo o primeiro registro
            for reg in registros[1:]:
                reg.delete()

        self.stdout.write(
            self.style.SUCCESS('Registros duplicados removidos com sucesso!')
        )