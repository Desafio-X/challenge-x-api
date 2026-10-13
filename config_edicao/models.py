from django.db import models

from django.db import models

from accounts.models import Perfil


class DominioInstitucional(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    ativo = models.BooleanField(default=True)
    perfil = models.CharField(max_length=10, choices=Perfil.choices)

    def __str__(self):
        return f"{self.nome} - {self.perfil}"
