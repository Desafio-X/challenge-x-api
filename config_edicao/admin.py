
from django.contrib import admin
from .models import DominioInstitucional


@admin.register(DominioInstitucional)
class DominioInstitucionalAdmin(admin.ModelAdmin):
    list_display = ("nome", "perfil", "ativo")
    list_filter = ("perfil", "ativo")
    search_fields = ("nome",)
