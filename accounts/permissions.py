
from rest_framework.permissions import BasePermission

from accounts.models import Perfil


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.perfil == Perfil.ADMIN
        )


class IsAcademico(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.perfil == Perfil.ACADEMICO
        )


class IsProfessor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.perfil == Perfil.PROFESSOR
        )

