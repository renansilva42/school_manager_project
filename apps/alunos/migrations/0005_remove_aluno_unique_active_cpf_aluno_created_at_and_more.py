# Generated by Django 4.2.19 on 2025-05-22 16:45

import django.core.validators
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('alunos', '0004_merge_20250504_1338'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='aluno',
            name='unique_active_cpf',
        ),
        migrations.AddField(
            model_name='aluno',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Data de Criação'),
        ),
        migrations.AddField(
            model_name='aluno',
            name='dados_adicionais',
            field=models.JSONField(blank=True, null=True, verbose_name='Dados Adicionais'),
        ),
        migrations.AlterField(
            model_name='aluno',
            name='cpf',
            field=models.CharField(blank=True, help_text='CPF no formato: 999.999.999-99. Este campo é opcional.', max_length=14, null=True, unique=True, validators=[django.core.validators.RegexValidator(message='Formato do CPF deve ser: 999.999.999-99', regex='^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$')], verbose_name='CPF'),
        ),
        migrations.AddConstraint(
            model_name='aluno',
            constraint=models.UniqueConstraint(condition=models.Q(('ativo', True), ('cpf__isnull', False), models.Q(('cpf', ''), _negated=True)), fields=('cpf',), name='unique_active_cpf'),
        ),
    ]
