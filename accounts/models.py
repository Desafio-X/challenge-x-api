
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Perfil(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    ACADEMICO = "ACADEMICO", "Acadêmico"
    PROFESSOR = "PROFESSOR", "Professor"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório.")

        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("perfil", Perfil.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None

    email = models.EmailField(unique=True)
    perfil = models.CharField(max_length=10, choices=Perfil.choices)

    matricula = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )
    curso = models.CharField(max_length=150, blank=True)
    periodo = models.PositiveSmallIntegerField(null=True, blank=True)
    email_confirmado = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()
