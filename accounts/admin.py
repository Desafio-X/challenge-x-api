
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "perfil",
        "matricula",
        "curso",
        "periodo",
        "email_confirmado",
        "is_staff",
        "is_active",
    )
    list_filter = ("perfil", "email_confirmado", "is_staff", "is_active")
    search_fields = ("email", "matricula", "curso")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Informações acadêmicas",
            {
                "fields": (
                    "perfil",
                    "matricula",
                    "curso",
                    "periodo",
                    "email_confirmado",
                )
            },
        ),
        (
            "Permissões",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "perfil",
                    "matricula",
                    "curso",
                    "periodo",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
