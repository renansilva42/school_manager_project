from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('professores', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Disciplina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('carga_horaria', models.IntegerField()),
                ('descricao', models.TextField(blank=True, null=True)),
                ('ativo', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='AtribuicaoDisciplina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turma', models.CharField(max_length=50)),
                ('ano_letivo', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('disciplina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='professores.disciplina')),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='professores.professor')),
            ],
            options={
                'unique_together': {('professor', 'disciplina', 'turma', 'ano_letivo')},
                'indexes': [models.Index(fields=['professor', 'disciplina', 'turma', 'ano_letivo'], name='professor_disciplina_idx')],
            },
        ),
    ]