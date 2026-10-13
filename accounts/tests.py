from django.test import TestCase

from accounts.permissions import IsAdmin, IsAcademico, IsProfessor
from django.test import TestCase
from rest_framework.test import APIClient
from config_edicao.models import DominioInstitucional
from accounts.models import User, Perfil
from django.core import signing
from rest_framework.test import APIRequestFactory


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.usuario = User.objects.create_user(
            email="teste@login.com",
            password="TesteForte!2026x",
            perfil=Perfil.ADMIN,
            is_active=True,
            is_staff=True,
            is_superuser=True,
            
        )

    def test_login_com_senha_incorreta(self):
        resposta = self.client.post(
            "/api/auth/login",
            {
                "email": "teste@login.com",
                "senha": "SenhaErrada!2026",
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 401)
        self.assertEqual(
            resposta.data["erro"],
            "Credenciais inválidas.",
        )


    def test_login_com_credenciais_validas(self):
        resposta = self.client.post(
            "/api/auth/login",
            {
                "email": "teste@login.com",
                "senha": "TesteForte!2026x",
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.data["email"],
            "teste@login.com",
        )
        self.assertTrue("_auth_user_id" in self.client.session)

class CadastroTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_cadastro_com_dominio_nao_autorizado(self):
        resposta = self.client.post(
            "/api/auth/register",
            {
                "email": "aluno@gmail.com",
                "senha": "TesteForte!2026x",
                "matricula": "TESTE001",
                "curso": "Engenharia de Software",
                "periodo": 6,
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("erro", resposta.data)


    def test_cadastro_com_dominio_autorizado(self):
        DominioInstitucional.objects.create(
            nome="aluno.unicatolica.edu.br",
            ativo=True,
            perfil=Perfil.ACADEMICO,
        )

        resposta = self.client.post(
            "/api/auth/register",
            {
                "email": "novo@aluno.unicatolica.edu.br",
                "senha": "TesteForte!2026x",
                "matricula": "TESTE002",
                "curso": "Engenharia de Software",
                "periodo": 6,
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertTrue(
            User.objects.filter(
                email="novo@aluno.unicatolica.edu.br",
                email_confirmado=False,
                is_active=False,
            ).exists()
        )

    def test_confirmacao_de_email_ativa_conta(self):
        usuario = User.objects.create_user(
            email="confirmar@aluno.unicatolica.edu.br",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            matricula="TESTE003",
            curso="Engenharia de Software",
            periodo=6,
            is_active=False,
            email_confirmado=False,
        )

        token = signing.dumps(
            {"user_id": usuario.pk},
            salt="confirmacao-email",
        )

        resposta = self.client.get(
            "/api/auth/confirm-email",
            {"token": token},
        )

        self.assertEqual(resposta.status_code, 200)

        usuario.refresh_from_db()
        self.assertTrue(usuario.email_confirmado)
        self.assertTrue(usuario.is_active)


    def test_confirmacao_com_token_invalido(self):
        resposta = self.client.get(
            "/api/auth/confirm-email",
            {"token": "token-invalido"},
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.data["erro"],
            "Token de confirmação inválido.",
        )


    def test_cadastro_com_dominio_desativado(self):
        DominioInstitucional.objects.create(
            nome="aluno.unicatolica.edu.br",
            ativo=False,
            perfil=Perfil.ACADEMICO,
        )

        resposta = self.client.post(
            "/api/auth/register",
            {
                "email": "bloqueado@aluno.unicatolica.edu.br",
                "senha": "TesteForte!2026x",
                "matricula": "TESTE004",
                "curso": "Engenharia de Software",
                "periodo": 6,
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(
            User.objects.filter(
                email="bloqueado@aluno.unicatolica.edu.br"
            ).exists()
        )

    def test_cadastro_com_matricula_duplicada(self):
        DominioInstitucional.objects.create(
            nome="aluno.unicatolica.edu.br",
            ativo=True,
            perfil=Perfil.ACADEMICO,
        )

        User.objects.create_user(
            email="existente@aluno.unicatolica.edu.br",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            matricula="TESTE005",
            curso="Engenharia de Software",
            periodo=6,
        )

        resposta = self.client.post(
            "/api/auth/register",
            {
                "email": "outro@aluno.unicatolica.edu.br",
                "senha": "TesteForte!2026x",
                "matricula": "TESTE005",
                "curso": "Engenharia de Software",
                "periodo": 6,
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(User.objects.count(), 1)


    def test_cadastro_com_periodo_invalido(self):
        DominioInstitucional.objects.create(
            nome="aluno.unicatolica.edu.br",
            ativo=True,
            perfil=Perfil.ACADEMICO,
        )

        resposta = self.client.post(
            "/api/auth/register",
            {
                "email": "periodo@aluno.unicatolica.edu.br",
                "senha": "TesteForte!2026x",
                "matricula": "TESTE006",
                "curso": "Engenharia de Software",
                "periodo": 0,
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(
            User.objects.filter(
                email="periodo@aluno.unicatolica.edu.br"
            ).exists()
        )


class PermissoesTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email="admin@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.ADMIN,
            is_active=True,
        )

        self.academico = User.objects.create_user(
            email="academico@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            is_active=True,
        )

        self.professor = User.objects.create_user(
            email="professor@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.PROFESSOR,
            is_active=True,
        )

    
    def test_is_admin(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.admin

        self.assertTrue(
            IsAdmin().has_permission(request, None)
        )

    def test_is_academico(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.academico

        self.assertTrue(
            IsAcademico().has_permission(request, None)
        )

    def test_is_professor(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.professor

        self.assertTrue(
            IsProfessor().has_permission(request, None)
        )


    def test_academico_nao_pode_ser_admin(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.academico

        self.assertFalse(
            IsAdmin().has_permission(request, None)
        )

    def test_professor_nao_pode_ser_admin(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.professor

        self.assertFalse(
            IsAdmin().has_permission(request, None)
        )

    def test_academico_nao_pode_ser_professor(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.academico

        self.assertFalse(
            IsProfessor().has_permission(request, None)
        )

    def test_professor_nao_pode_ser_admin(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.professor

        self.assertFalse(
            IsAdmin().has_permission(request, None)
        )

    def test_academico_nao_pode_ser_professor(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.academico

        self.assertFalse(
            IsProfessor().has_permission(request, None)
        )

class SessaoTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.usuario = User.objects.create_user(
            email="sessao@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.ADMIN,
            is_active=True,
            is_staff=True,
            is_superuser=True,
            email_confirmado=True,
        )

    def test_me_com_usuario_autenticado(self):
        self.client.force_authenticate(user=self.usuario)

        resposta = self.client.get("/api/auth/me")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["email"], self.usuario.email)
        self.assertEqual(resposta.data["perfil"], Perfil.ADMIN)

    def test_me_sem_autenticacao(self):
        resposta = self.client.get("/api/auth/me")

        self.assertIn(resposta.status_code, [401, 403])

    def test_logout_com_usuario_autenticado(self):
        self.client.force_authenticate(user=self.usuario)

        resposta = self.client.post("/api/auth/logout")

        self.assertEqual(resposta.status_code, 204)

    def test_logout_sem_autenticacao(self):
        resposta = self.client.post("/api/auth/logout")

        self.assertIn(resposta.status_code, [401, 403])




