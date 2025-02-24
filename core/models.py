from django.db import models

class Professor(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    disciplina = models.CharField(max_length=50)

    def __str__(self):
        return self.nome