from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alunos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aluno',
            name='data_matricula',
            field=models.DateField(blank=True, null=True, verbose_name='Data de Matrícula'),
        ),
    ]
