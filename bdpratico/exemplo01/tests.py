from datetime import date
from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from .admin import PessoaCustomizado
from .models import pessoa


class PessoaCustomizadoAdminTest(TestCase):
    """Testes unitários para a customização PessoaCustomizado no Django Admin."""

    def setUp(self) -> None:
        """Inicializa instâncias necessárias para os testes."""
        self.site = AdminSite()
        self.admin = PessoaCustomizado(pessoa, self.site)

    def test_calcula_idade_sem_nascimento(self) -> None:
        """Verifica se retorna 'Não informado' quando nascimento for nulo."""
        obj: pessoa = pessoa.objects.create(
            nome="Fulano",
            email="fulano@teste.com",
            nascimento=None,
        )
        resultado = self.admin.calcula_idade(obj)
        self.assertEqual(resultado, "Não informado")

    def test_calcula_idade_com_nascimento(self) -> None:
        """Verifica o cálculo exato da idade em anos completos."""
        hoje: date = date.today()
        # Data de nascimento há exatamente 20 anos
        nascimento: date = date(hoje.year - 20, hoje.month, hoje.day)
        obj: pessoa = pessoa.objects.create(
            nome="Ciclano",
            email="ciclano@teste.com",
            nascimento=nascimento,
        )
        resultado = self.admin.calcula_idade(obj)
        self.assertEqual(resultado, 20)
