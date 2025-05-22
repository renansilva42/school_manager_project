from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('professores', '0005_add_user_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='professor',
            name='data_nascimento',
            field=models.DateField(null=True, blank=True),
        ),
    ]
