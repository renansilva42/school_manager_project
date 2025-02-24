from django.db import models

class Aluno(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    data_nascimento = models.DateField()
    email = models.EmailField()

    def __str__(self):
        return self.nome

class Professor(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    disciplina = models.CharField(max_length=50)

    def __str__(self):
        return self.nome