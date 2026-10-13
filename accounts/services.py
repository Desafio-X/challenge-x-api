
from config_edicao.models import DominioInstitucional
from accounts.models import Perfil


class DominioInvalido(Exception):
    pass


def perfil_pelo_dominio(email: str) -> str:
    email = email.strip().lower()

    if "@" not in email:
        raise DominioInvalido("E-mail inválido.")

    dominio = email.rsplit("@", 1)[1]

    try:
        registro = DominioInstitucional.objects.get(
            nome__iexact=dominio,
            ativo=True,
        )
    except DominioInstitucional.DoesNotExist:
        raise DominioInvalido(
            "E-mail fora dos domínios autorizados."
        )

    if registro.perfil not in (
        Perfil.ACADEMICO,
        Perfil.PROFESSOR,
    ):
        raise DominioInvalido(
            "Este domínio não permite cadastro público."
        )

    return registro.perfil
