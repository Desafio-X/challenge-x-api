
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User, Perfil
from accounts.services import perfil_pelo_dominio, DominioInvalido
from django.middleware.csrf import get_token

from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from accounts.permissions import IsAdmin


class CadastroView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        dados = request.data

        email = str(dados.get("email", "")).strip().lower()
        senha = dados.get("senha")
        matricula = str(dados.get("matricula", "")).strip()
        curso = str(dados.get("curso", "")).strip()
        periodo = dados.get("periodo")

        if not all([email, senha, matricula, curso, periodo]):
            return Response(
                {
                    "erro": (
                        "Informe e-mail, senha, matrícula, "
                        "curso e período."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            perfil = perfil_pelo_dominio(email)
        except DominioInvalido as erro:
            return Response(
                {"erro": str(erro)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # O cadastro público é exclusivo para acadêmicos.
        if perfil != Perfil.ACADEMICO:
            return Response(
                {"erro": "Este perfil não pode realizar cadastro público."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            User.objects.filter(email__iexact=email).exists()
            or User.objects.filter(matricula=matricula).exists()
        ):
            return Response(
                {
                    "erro": (
                        "Não foi possível realizar o cadastro "
                        "com esses dados."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            periodo = int(periodo)
            if periodo < 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"erro": "O período deve ser um número inteiro positivo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(senha)
        except ValidationError as erro:
            return Response(
                {"erro": list(erro.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                usuario = User.objects.create_user(
                    email=email,
                    password=senha,
                    perfil=Perfil.ACADEMICO,
                    matricula=matricula,
                    curso=curso,
                    periodo=periodo,
                    is_active=False,
                    email_confirmado=False,
                )
        except IntegrityError:
            return Response(
                {
                    "erro": (
                        "Não foi possível realizar o cadastro "
                        "com esses dados."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = signing.dumps(
            {"user_id": usuario.pk},
            salt="confirmacao-email",
        )

        link = request.build_absolute_uri(
            reverse("confirmar-email") + f"?token={token}"
        )

        try:
            send_mail(
                subject="Confirme seu e-mail - Desafio X",
                message=f"Para confirmar seu e-mail, acesse: {link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            # Evita deixar uma conta pendente se o envio falhar.
            usuario.delete()
            return Response(
                {"erro": "Não foi possível enviar o e-mail de confirmação."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "mensagem": (
                    "Cadastro iniciado. Confira o e-mail "
                    "para confirmar a conta."
                )
            },
            status=status.HTTP_201_CREATED,
        )


class ConfirmarEmailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        token = request.query_params.get("token")

        if not token:
            return Response(
                {"erro": "Token não informado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dados = signing.loads(
                token,
                salt="confirmacao-email",
                max_age=60 * 60 * 24,
            )
        except signing.SignatureExpired:
            return Response(
                {"erro": "O link de confirmação expirou."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {"erro": "Token de confirmação inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = get_object_or_404(
            User,
            pk=dados.get("user_id"),
        )

        if usuario.email_confirmado:
            return Response(
                {"mensagem": "E-mail já confirmado."},
                status=status.HTTP_200_OK,
            )

        usuario.email_confirmado = True
        usuario.is_active = True
        usuario.save(
            update_fields=["email_confirmado", "is_active"]
        )

        return Response(
            {"mensagem": "E-mail confirmado com sucesso."},
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        senha = request.data.get("senha")

        if not email or not senha:
            return Response(
                {"erro": "Informe e-mail e senha."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = authenticate(
            request,
            username=email,
            password=senha,
        )

        if usuario is None:
            return Response(
                {"erro": "Credenciais inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not usuario.is_active:
            return Response(
                {"erro": "Conta inativa ou e-mail não confirmado."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            usuario.perfil == Perfil.ACADEMICO
            and not usuario.email_confirmado
        ):
            return Response(
                {"erro": "Confirme seu e-mail antes de entrar."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Revalida o domínio institucional, exceto para administradores.
        if usuario.perfil != Perfil.ADMIN:
            try:
                perfil_atual = perfil_pelo_dominio(usuario.email)
            except DominioInvalido:
                return Response(
                    {"erro": "Domínio institucional não autorizado."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if perfil_atual != usuario.perfil:
                return Response(
                    {"erro": "Perfil não autorizado para este domínio."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        login(request, usuario)

        return Response(
            {
                "mensagem": "Login realizado com sucesso.",
                "email": usuario.email,
                "perfil": usuario.perfil,
            },
            status=status.HTTP_200_OK,
        )




class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "email": request.user.email,
            "perfil": request.user.perfil,
            "email_confirmado": request.user.email_confirmado,
        })


    
class CsrfView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        token = get_token(request)
        return Response({"csrfToken": token})
    

class RotaAdministrativaView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({"mensagem": "Acesso administrativo autorizado."})
    
    
