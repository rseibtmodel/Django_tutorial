from django.test import Client, TestCase
from django.urls import reverse


class AppTestesHealthCheckTestCase(TestCase):
    """Testes automatizados da view inicial do app_testes."""

    def setUp(self) -> None:
        self.client: Client = Client()

    def test_index_status_code_e_conteudo(self) -> None:
        """Valida se a rota index responde com status 200 e JSON esperado."""
        url: str = reverse('app_testes:index')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(dados.get('status'), 'online')
        self.assertEqual(dados.get('app'), 'app_testes')
