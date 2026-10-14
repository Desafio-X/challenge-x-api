from django.test import TestCase
from unittest.mock import patch
from accounts.permissions import IsAdmin, IsAcademico, IsProfessor
from django.test import TestCase
from rest_framework.test import APIClient
from config_edicao.models import DominioInstitucional
from accounts.models import User, Perfil
from django.core import signing
from rest_framework.test import APIRequestFactory
from accounts.services import perfil_pelo_dominio
from django.urls import reverse


class LoginTests(TestCase):


    def test_login_com_dominio_desativado(self):
        DominioInstitucional.objects.create(
            nome="aluno.unicatolica.edu.br",
            ativo=False,
            perfil=Perfil.ACADEMICO,
        )

        User.objects.create_user(
            email="aluno@aluno.unicatolica.edu.br",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            matricula="LOGIN001",
            curso="Engenharia de Software",
            periodo=6,
            is_active=True,
            email_confirmado=True,
        )

        resposta = self.client.post(
            "/api/auth/login",
            {
                "email": "aluno@aluno.unicatolica.edu.br",
                "senha": "TesteForte!2026x",
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(
            resposta.data["erro"],
            "Domínio institucional não autorizado.",
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_com_perfil_incompativel_com_dominio(self):
        DominioInstitucional.objects.create(
            nome="aluno.unicatolica.edu.br",
            ativo=True,
            perfil=Perfil.ACADEMICO,
        )

        User.objects.create_user(
            email="professor@aluno.unicatolica.edu.br",
            password="TesteForte!2026x",
            perfil=Perfil.PROFESSOR,
            is_active=True,
        )

        resposta = self.client.post(
            "/api/auth/login",
            {
                "email": "professor@aluno.unicatolica.edu.br",
                "senha": "TesteForte!2026x",
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(
            resposta.data["erro"],
            "Perfil não autorizado para este domínio.",
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_com_campos_vazios(self):
        resposta = self.client.post(
            "/api/auth/login",
            {},
            format="json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.data["erro"],
            "Informe e-mail e senha.",
        )

    def test_login_com_conta_inativa(self):
        User.objects.create_user(
            email="inativo@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.ADMIN,
            is_active=False,
        )

        resposta = self.client.post(
            "/api/auth/login",
            {
                "email": "inativo@teste.com",
                "senha": "TesteForte!2026x",
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 401)
        self.assertNotIn("_auth_user_id", self.client.session)

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
    def test_login_com_email_nao_confirmado(self):
        DominioInstitucional.objects.create(
            nome="a.catolica-to.edu.br",
            ativo=True,
            perfil=Perfil.ACADEMICO,
        )

        User.objects.create_user(
            email="aluno@a.catolica-to.edu.br",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            matricula="LOGIN002",
            curso="Engenharia de Software",
            periodo=6,
            is_active=True,
            email_confirmado=False,
        )

        resposta = self.client.post(
            "/api/auth/login",
            {
                "email": "aluno@a.catolica-to.edu.br",
                "senha": "TesteForte!2026x",
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertNotIn("_auth_user_id", self.client.session)    

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
        usuario = User.objects.get(
            email="novo@aluno.unicatolica.edu.br"
        )
        self.assertEqual(usuario.perfil, Perfil.ACADEMICO)
        self.assertEqual(usuario.matricula, "TESTE002")
        

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

        
    def test_cadastro_com_email_duplicado(self):
        DominioInstitucional.objects.create(
            nome="aluno.unicatolica.edu.br",
            ativo=True,
            perfil=Perfil.ACADEMICO,
        )

        User.objects.create_user(
            email="existente@aluno.unicatolica.edu.br",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            matricula="TESTE008",
            curso="Engenharia de Software",
            periodo=6,
        )

        resposta = self.client.post(
            "/api/auth/register",
            {
                "email": "EXISTENTE@aluno.unicatolica.edu.br",
                "senha": "TesteForte!2026x",
                "matricula": "TESTE009",
                "curso": "Engenharia de Software",
                "periodo": 6,
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(User.objects.count(), 1)



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

class SessaoTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.enforce_csrf_checks = True

        self.usuario = User.objects.create_user(
            email="sessao@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.ADMIN,
            is_active=True,
            is_staff=True,
            is_superuser=True,
            email_confirmado=True,
        )


    def test_login_cria_sessao_real(self):
        resposta_csrf = self.client.get("/api/auth/csrf")
        self.assertEqual(resposta_csrf.status_code, 200)

        token = resposta_csrf.data["csrfToken"]

        resposta = self.client.post(
            "/api/auth/login",
            {
                "email": "sessao@teste.com",
                "senha": "TesteForte!2026x",
            },
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["perfil"], Perfil.ADMIN)
        self.assertIn("_auth_user_id", self.client.session)

        resposta_me = self.client.get("/api/auth/me")
        self.assertEqual(resposta_me.status_code, 200)
        self.assertEqual(resposta_me.data["perfil"], Perfil.ADMIN)

        
    def test_login_logout_nos_tres_perfis(self):
        DominioInstitucional.objects.create(
            nome="aluno.unicatolica.edu.br",
            ativo=True,
            perfil=Perfil.ACADEMICO,
        )
        DominioInstitucional.objects.create(
            nome="professor.unicatolica.edu.br",
            ativo=True,
            perfil=Perfil.PROFESSOR,
        )

        usuarios = [
            (
                self.usuario,
                "TesteForte!2026x",
                Perfil.ADMIN,
            ),
            (
                User.objects.create_user(
                    email="aluno@aluno.unicatolica.edu.br",
                    password="TesteForte!2026x",
                    perfil=Perfil.ACADEMICO,
                    matricula="TESTE001",
                    curso="Engenharia de Software",
                    periodo=6,
                    is_active=True,
                    email_confirmado=True,
                ),
                "TesteForte!2026x",
                Perfil.ACADEMICO,
            ),
            (
                User.objects.create_user(
                    email="professor@professor.unicatolica.edu.br",
                    password="TesteForte!2026x",
                    perfil=Perfil.PROFESSOR,
                    is_active=True,
                    email_confirmado=True,
                ),
                "TesteForte!2026x",
                Perfil.PROFESSOR,
            ),
        ]

        for usuario, senha, perfil in usuarios:
            with self.subTest(perfil=perfil):
                resposta_csrf = self.client.get("/api/auth/csrf")
                token = resposta_csrf.data["csrfToken"]

                resposta_login = self.client.post(
                    "/api/auth/login",
                    {"email": usuario.email, "senha": senha},
                    format="json",
                    HTTP_X_CSRFTOKEN=token,
                )

                self.assertEqual(resposta_login.status_code, 200)
                self.assertEqual(resposta_login.data["perfil"], perfil)
                self.assertIn("_auth_user_id", self.client.session)

                resposta_me = self.client.get("/api/auth/me")
                self.assertEqual(resposta_me.status_code, 200)
                self.assertEqual(resposta_me.data["perfil"], perfil)

                resposta_csrf = self.client.get("/api/auth/csrf")
                token = resposta_csrf.data["csrfToken"]

                resposta_logout = self.client.post(
                    "/api/auth/logout",
                    {},
                    format="json",
                    HTTP_X_CSRFTOKEN=token,
                )

                self.assertEqual(resposta_logout.status_code, 204)
                self.assertNotIn("_auth_user_id", self.client.session)


    def test_login_sem_csrf_e_bloqueado(self):
        resposta = self.client.post(
        "/api/auth/login",
        {
            "email": "sessao@teste.com",
            "senha": "TesteForte!2026x",
        },
        format="json",
    )

        self.assertEqual(resposta.status_code, 403)
        self.assertNotIn("_auth_user_id", self.client.session)



    def test_me_sem_autenticacao(self):
        resposta = self.client.get("/api/auth/me")
        self.assertIn(resposta.status_code, [401, 403])

    def test_logout_sem_csrf_e_bloqueado(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            "/api/auth/logout",
            {},
            format="json",
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_com_csrf_valido(self):
        self.client.force_login(self.usuario)

        resposta_csrf = self.client.get("/api/auth/csrf")
        self.assertEqual(resposta_csrf.status_code, 200)

        token = resposta_csrf.data["csrfToken"]

        resposta = self.client.post(
            "/api/auth/logout",
            {},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(resposta.status_code, 204)
        self.assertNotIn("_auth_user_id", self.client.session)

        resposta_me = self.client.get("/api/auth/me")
        self.assertIn(resposta_me.status_code, [401, 403])

    def test_logout_com_csrf_invalido(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            "/api/auth/logout",
            {},
            format="json",
            HTTP_X_CSRFTOKEN="token-invalido",
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_sem_autenticacao(self):
        resposta = self.client.post("/api/auth/logout")
        self.assertIn(resposta.status_code, [401, 403])


    def test_sessao_tem_expiracao_de_30_minutos(self):
        self.client.force_login(self.usuario)

        sessao = self.client.session

        self.assertEqual(sessao.get_expiry_age(), 1800)



    def test_requisicao_renova_sessao(self):
        self.client.force_login(self.usuario)

        idade_antes = self.client.session.get_expiry_age()

        resposta = self.client.get("/api/auth/me")

        self.assertEqual(resposta.status_code, 200)

        idade_depois = self.client.session.get_expiry_age()

        self.assertEqual(idade_antes, 1800)
        self.assertEqual(idade_depois, 1800)


    def test_confirmacao_com_token_expirado(self):
        usuario = User.objects.create_user(
            email="expirado@aluno.unicatolica.edu.br",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            matricula="TESTE007",
            curso="Engenharia de Software",
            periodo=6,
            is_active=False,
            email_confirmado=False,
        )

        token = signing.dumps(
            {"user_id": usuario.pk},
            salt="confirmacao-email",
        )

        # Simula um token com mais de 24 horas.
        with patch("accounts.views.signing.loads") as mock_loads:
            mock_loads.side_effect = signing.SignatureExpired

            resposta = self.client.get(
                "/api/auth/confirm-email",
                {"token": token},
            )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.data["erro"],
            "O link de confirmação expirou.",
        )

        usuario.refresh_from_db()
        self.assertFalse(usuario.email_confirmado)
        self.assertFalse(usuario.is_active)

    def test_confirmacao_de_email_ja_confirmado(self):
        usuario = User.objects.create_user(
            email="confirmado@aluno.unicatolica.edu.br",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            matricula="TESTE008",
            curso="Engenharia de Software",
            periodo=6,
            is_active=True,
            email_confirmado=True,
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
        self.assertEqual(
            resposta.data["mensagem"],
            "E-mail já confirmado.",
        )
class PerfilPeloDominioTests(TestCase):

    def test_identifica_perfil_professor_pelo_dominio(self):
        DominioInstitucional.objects.create(
            nome="professor.unicatolica.edu.br",
            ativo=True,
            perfil=Perfil.PROFESSOR,
        )

        perfil = perfil_pelo_dominio(
            "docente@professor.unicatolica.edu.br"
        )

        self.assertEqual(perfil, Perfil.PROFESSOR)

        
    def test_rejeita_dominio_inexistente(self):
        from accounts.services import DominioInvalido

        with self.assertRaises(DominioInvalido):
            perfil_pelo_dominio("usuario@gmail.com")

    def test_rejeita_dominio_desativado(self):
        from accounts.services import DominioInvalido

        DominioInstitucional.objects.create(
            nome="professor.unicatolica.edu.br",
            ativo=False,
            perfil=Perfil.PROFESSOR,
        )

        with self.assertRaises(DominioInvalido):
            perfil_pelo_dominio(
                "docente@professor.unicatolica.edu.br"
            )

class RotaAdministrativaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.ADMIN,
            is_active=True,
            is_staff=True,
            is_superuser=True,
            email_confirmado=True,
        )
        self.academico = User.objects.create_user(
            email="aluno@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.ACADEMICO,
            is_active=True,
            email_confirmado=True,
        )
        self.professor = User.objects.create_user(
            email="professor@teste.com",
            password="TesteForte!2026x",
            perfil=Perfil.PROFESSOR,
            is_active=True,
            email_confirmado=True,
        )

    def test_admin_pode_acessar_rota(self):
        self.client.force_authenticate(user=self.admin)
        resposta = self.client.get("/api/admin/teste-acesso")
        self.assertEqual(resposta.status_code, 200)

    def test_academico_nao_pode_acessar_rota(self):
        self.client.force_authenticate(user=self.academico)
        resposta = self.client.get("/api/admin/teste-acesso")
        self.assertEqual(resposta.status_code, 403)

    def test_professor_nao_pode_acessar_rota(self):
        self.client.force_authenticate(user=self.professor)
        resposta = self.client.get("/api/admin/teste-acesso")
        self.assertEqual(resposta.status_code, 403)

    def test_usuario_nao_autenticado_nao_pode_acessar_rota(self):
        resposta = self.client.get("/api/admin/teste-acesso")
        self.assertIn(resposta.status_code, [401, 403])


