# apps/alunos/models.py
from django.db import models
from services.database import SupabaseService


class AlunoManager:
    def __init__(self):
        self.db = SupabaseService()

    def create(self, **kwargs):
        return self.db.create_aluno(kwargs)

    def get(self, id):
        return self.db.get_aluno(id)

    def update(self, id, data):
        return self.db.update_aluno(id, data)

    def delete(self, id):
        return self.db.delete_aluno(id)

    def filter(self, **kwargs):
        return self.db.list_alunos(kwargs)

    def all(self):
        return self.filter()  # Using the existing filter method without parameters

class Aluno:
    objects = AlunoManager()

    TURNO_CHOICES = [
        ('M', 'Manhã'),
        ('T', 'Tarde'),
    ]

    NIVEL_CHOICES = [
        ('EFI', 'Ensino Fundamental Anos Iniciais'),
        ('EFF', 'Ensino Fundamental Anos Finais'),
    ]

    ANO_CHOICES = [
        ('3', '3º Ano'),
        ('4', '4º Ano'),
        ('5', '5º Ano'),
        ('6', '6º Ano'),
        ('7', '7º Ano'),
        ('8', '8º Ano'),
        ('901', '9º Ano - Turma 901'),
        ('902', '9º Ano - Turma 902'),
    ]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class NotaManager:
    def __init__(self):
        self.db = SupabaseService()

    def create(self, **kwargs):
        return self.db.create_nota(kwargs)

    def get_for_aluno(self, aluno_id):
        return self.db.get_notas_aluno(aluno_id)

class Nota:
    objects = NotaManager()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)