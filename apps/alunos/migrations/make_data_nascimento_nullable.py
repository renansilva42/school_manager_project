from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alunos', '0001_initial'),  # Replace with the actual last migration
    ]

    operations = [
        migrations.AlterField(
            model_name='aluno',
            name='data_nascimento',
            field=models.DateField(blank=True, help_text='Data de nascimento do aluno', null=True, verbose_name='Data de Nascimento'),
        ),
    ]
