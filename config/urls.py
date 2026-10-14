from django.contrib import admin
from django.urls import path

from accounts.views import (
    CadastroView,
    ConfirmarEmailView,
    LoginView,
    LogoutView,
    MeView,
    CsrfView,
    RotaAdministrativaView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register", CadastroView.as_view(), name="cadastro"),
    path("api/auth/confirm-email", ConfirmarEmailView.as_view(), name="confirmar-email"),
    path("api/auth/login", LoginView.as_view(), name="login"),
    path("api/auth/logout", LogoutView.as_view(), name="logout"),
    path("api/auth/me", MeView.as_view(), name="me"),
    path("api/auth/csrf", CsrfView.as_view(), name="csrf"),
    path("api/admin/teste-acesso", RotaAdministrativaView.as_view(), name="teste-acesso-admin"),
]