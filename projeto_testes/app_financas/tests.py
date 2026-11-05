"""Suíte de testes automatizados para o módulo app_financas.

Testa sanitização monetária, parser telegráfico, mutações atômicas, soft delete contábil,
CQRS de leitura, isolamento anti-IDOR, views em Terminal Dark e tools do chatbot.
"""

from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .exceptions import (
    DataCompetenciaInvalidaError,
    LancamentoNaoEncontradoError,
    TransacaoInvalidaError,
    ValorInvalidoError,
)
from .models import LancamentoFinanceiro
from .selectors import (
    calcular_balanco_periodo,
    listar_categorias_ativas,
    obter_extrato_mensal,
    obter_lancamento_por_id,
)
from .services import (
    criar_lancamento,
    excluir_lancamento,
    parse_comando_telegrafico,
    processar_comando_telegrafico,
    sanitizar_e_validar_valor,
)


class SanitizadorMonetarioTestCase(TestCase):
    """Testa a robustez da conversão determinística para Decimal(0.01)."""

    def test_valores_validos_padrao_br_e_us(self) -> None:
        """Verifica se vírgula, ponto e separadores de milhar são convertidos com exatidão."""
        self.assertEqual(sanitizar_e_validar_valor("45.50"), Decimal("45.50"))
        self.assertEqual(sanitizar_e_validar_valor("45,50"), Decimal("45.50"))
        self.assertEqual(sanitizar_e_validar_valor("1.250,50"), Decimal("1250.50"))
        self.assertEqual(sanitizar_e_validar_valor("1,250.50"), Decimal("1250.50"))
        self.assertEqual(sanitizar_e_validar_valor("R$ 80,00"), Decimal("80.00"))
        self.assertEqual(sanitizar_e_validar_valor("$ 100.25"), Decimal("100.25"))
        self.assertEqual(sanitizar_e_validar_valor(150), Decimal("150.00"))
        self.assertEqual(sanitizar_e_validar_valor(99.9), Decimal("99.90"))
        self.assertEqual(sanitizar_e_validar_valor(Decimal("250.75")), Decimal("250.75"))

    def test_rejeicao_valores_negativos_ou_zerados(self) -> None:
        """Garante que montantes <= 0 sejam barrados com ValorInvalidoError."""
        with self.assertRaises(ValorInvalidoError):
            sanitizar_e_validar_valor("0.00")
        with self.assertRaises(ValorInvalidoError):
            sanitizar_e_validar_valor("-45.50")
        with self.assertRaises(ValorInvalidoError):
            sanitizar_e_validar_valor(0)
        with self.assertRaises(ValorInvalidoError):
            sanitizar_e_validar_valor(Decimal("-10.00"))

    def test_rejeicao_entradas_invalidas_ou_nulas(self) -> None:
        """Garante que entradas vazias ou não-numéricas disparem exceção."""
        with self.assertRaises(ValorInvalidoError):
            sanitizar_e_validar_valor(None)  # type: ignore
        with self.assertRaises(ValorInvalidoError):
            sanitizar_e_validar_valor("")
        with self.assertRaises(ValorInvalidoError):
            sanitizar_e_validar_valor("invalido")


class ParserTelegraficoTestCase(TestCase):
    """Testa a extração de comandos telegráficos em linha única."""

    def test_comando_gasto_completo_com_categoria(self) -> None:
        """Testa parsing de '/gasto 45.00 almoco executivo [alimentacao]'."""
        cmd = "/gasto 45.00 almoco executivo [alimentacao]"
        res = parse_comando_telegrafico(cmd)
        self.assertEqual(res["tipo"], LancamentoFinanceiro.TIPO_DESPESA)
        self.assertEqual(res["valor"], Decimal("45.00"))
        self.assertEqual(res["descricao"], "almoco executivo")
        self.assertEqual(res["categoria"], "alimentacao")

    def test_comando_receita_sem_categoria_explicita(self) -> None:
        """Testa parsing de '/receita 1500.00 consultoria django'."""
        cmd = "/receita 1500.00 consultoria django"
        res = parse_comando_telegrafico(cmd)
        self.assertEqual(res["tipo"], LancamentoFinanceiro.TIPO_RECEITA)
        self.assertEqual(res["valor"], Decimal("1500.00"))
        self.assertEqual(res["descricao"], "consultoria django")
        self.assertEqual(res["categoria"], "outros")

    def test_comando_sem_barra_e_com_virgula(self) -> None:
        """Testa comando informal 'gasto 12,50 cafe'."""
        cmd = "gasto 12,50 cafe com pao"
        res = parse_comando_telegrafico(cmd)
        self.assertEqual(res["tipo"], LancamentoFinanceiro.TIPO_DESPESA)
        self.assertEqual(res["valor"], Decimal("12.50"))
        self.assertEqual(res["descricao"], "cafe com pao")

    def test_comando_invalido_dispara_excecao(self) -> None:
        """Testa comandos vazios ou malformados."""
        with self.assertRaises(TransacaoInvalidaError):
            parse_comando_telegrafico("")
        with self.assertRaises(TransacaoInvalidaError):
            parse_comando_telegrafico("/banana 50 almoço")
        with self.assertRaises(TransacaoInvalidaError):
            parse_comando_telegrafico("/gasto")


class FinancasServicesTestCase(TestCase):
    """Testa criação, processamento de comando e soft-delete de lançamentos."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user(username="operador_alfa", password="senha_segura_123")
        self.outro_usuario = User.objects.create_user(username="operador_beta", password="senha_segura_123")

    def test_criar_lancamento_sucesso(self) -> None:
        """Criação válida de despesa e receita."""
        l1 = criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="120,00",
            descricao="Hospedagem Servidor",
            categoria="infraestrutura",
            data_competencia="2026-11-04",
        )
        self.assertEqual(l1.valor, Decimal("120.00"))
        self.assertEqual(l1.tipo, LancamentoFinanceiro.TIPO_DESPESA)
        self.assertEqual(l1.categoria, "infraestrutura")
        self.assertTrue(l1.ativo)

    def test_default_data_competencia_usa_localdate(self) -> None:
        """Valida que lançamento sem data informada adota o timezone.localdate() atual."""
        l = criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_RECEITA,
            valor="100.00",
            descricao="Entrada Teste",
        )
        self.assertEqual(l.data_competencia, timezone.localdate())

    def test_processar_comando_telegrafico_cria_no_banco(self) -> None:
        """Executa comando telegráfico ponta a ponta persistindo no banco."""
        lanc = processar_comando_telegrafico(
            usuario=self.usuario,
            comando="/receita 3500.00 Salario Mensal [renda]",
        )
        self.assertEqual(lanc.tipo, LancamentoFinanceiro.TIPO_RECEITA)
        self.assertEqual(lanc.valor, Decimal("3500.00"))
        self.assertEqual(lanc.categoria, "renda")
        self.assertTrue(LancamentoFinanceiro.objects.filter(id=lanc.id).exists())

    def test_excluir_lancamento_soft_delete(self) -> None:
        """Garante que a exclusão inativa 'ativo=False' sem apagar a linha contábil."""
        lanc = criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="35.00",
            descricao="Almoco",
        )
        inativado = excluir_lancamento(lancamento_id=lanc.id, usuario=self.usuario)
        self.assertFalse(inativado.ativo)

        # Registro ainda existe no banco
        db_lanc = LancamentoFinanceiro.objects.get(id=lanc.id)
        self.assertFalse(db_lanc.ativo)

    def test_exclusao_anti_idor_bloqueada(self) -> None:
        """Impede que Usuário B inative lançamento do Usuário A."""
        lanc = criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="50.00",
            descricao="Secreto",
        )
        with self.assertRaises(LancamentoNaoEncontradoError):
            excluir_lancamento(lancamento_id=lanc.id, usuario=self.outro_usuario)


class FinancasSelectorsTestCase(TestCase):
    """Testa leitura analítica, balanço mensal e agregações CQRS."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user(username="operador_fin", password="senha_segura_123")
        # Cria 2 receitas e 2 despesas no mês 11/2026
        criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_RECEITA,
            valor="5000.00",
            descricao="Salario",
            categoria="renda",
            data_competencia="2026-11-01",
        )
        criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_RECEITA,
            valor="1200.00",
            descricao="Freela",
            categoria="projetos",
            data_competencia="2026-11-03",
        )
        criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="1500.00",
            descricao="Aluguel",
            categoria="moradia",
            data_competencia="2026-11-02",
        )
        criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="700.00",
            descricao="Mercado",
            categoria="alimentacao",
            data_competencia="2026-11-04",
        )

    def test_calcular_balanco_periodo_agregacoes_exatas(self) -> None:
        """Verifica se soma de receitas, despesas e saldo líquido são exatas."""
        balanco = calcular_balanco_periodo(usuario=self.usuario, ano=2026, mes=11)
        # Receitas: 5000 + 1200 = 6200.00
        # Despesas: 1500 + 700 = 2200.00
        # Saldo: 4000.00
        # Taxa poupança: (4000 / 6200) * 100 = 64.5%
        self.assertEqual(balanco["total_receitas"], Decimal("6200.00"))
        self.assertEqual(balanco["total_despesas"], Decimal("2200.00"))
        self.assertEqual(balanco["saldo_liquido"], Decimal("4000.00"))
        self.assertEqual(balanco["taxa_poupanca"], 64.5)
        self.assertEqual(balanco["total_lancamentos"], 4)

    def test_lancamento_inativo_ignorado_no_balanco(self) -> None:
        """Lançamentos com ativo=False não devem ser somados no balanço."""
        lanc = criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="1000.00",
            descricao="Compra Cancelada",
            data_competencia="2026-11-05",
        )
        excluir_lancamento(lancamento_id=lanc.id, usuario=self.usuario)

        balanco = calcular_balanco_periodo(usuario=self.usuario, ano=2026, mes=11)
        self.assertEqual(balanco["total_despesas"], Decimal("2200.00"))

    def test_obter_extrato_mensal_filtro_categoria(self) -> None:
        """Verifica filtro por categoria no extrato."""
        qs = obter_extrato_mensal(usuario=self.usuario, ano=2026, mes=11, categoria="moradia")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().descricao, "Aluguel")


class FinancasViewsTestCase(TestCase):
    """Testa endpoints HTTP e renderização no padrão Terminal Dark."""

    def setUp(self) -> None:
        self.client = Client()
        self.usuario = User.objects.create_user(username="operador_web", password="senha_segura_123")
        self.client.force_login(self.usuario)

    def test_extrato_requer_login(self) -> None:
        """Garante redirecionamento para login de usuários anônimos."""
        self.client.logout()
        res = self.client.get(reverse("app_financas:extrato"))
        self.assertEqual(res.status_code, 302)

    def test_extrato_get_200_terminal_dark(self) -> None:
        """Renderiza console de extrato com sucesso."""
        res = self.client.get(reverse("app_financas:extrato"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "FLUXO_DE_CAIXA_LOCAL")
        self.assertContains(res, "SALDO DISPONÍVEL")

    def test_criar_lancamento_via_comando_post(self) -> None:
        """Dispara criação via input de comando telegráfico."""
        res = self.client.post(
            reverse("app_financas:criar"),
            {"comando_telegrafico": "/gasto 65.00 combustivel [transporte]"},
            follow=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(LancamentoFinanceiro.objects.filter(descricao="combustivel").exists())

    def test_excluir_lancamento_post(self) -> None:
        """Inativa lançamento via POST."""
        lanc = criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="25.00",
            descricao="Cafe",
        )
        res = self.client.post(
            reverse("app_financas:excluir", kwargs={"lancamento_id": lanc.id}),
            follow=True,
        )
        self.assertEqual(res.status_code, 200)
        lanc.refresh_from_db()
        self.assertFalse(lanc.ativo)

    def test_exportar_extrato_csv(self) -> None:
        """Exporta CSV com header e BOM UTF-8."""
        criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_RECEITA,
            valor="2000.00",
            descricao="Honorarios",
            data_competencia="2026-11-04",
        )
        res = self.client.get(reverse("app_financas:exportar_csv") + "?ano=2026&mes=11")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Honorarios", res.content.decode("utf-8"))

    def test_criar_lancamento_retroativo_redireciona_para_mes_do_lancamento(self) -> None:
        """Garante que lançamento retroativo redireciona para a competência real da transação."""
        res = self.client.post(
            reverse("app_financas:criar"),
            {
                "tipo": "DESPESA",
                "valor": "300.00",
                "descricao": "Seguro Anual",
                "categoria": "veiculo",
                "data_competencia": "2026-05-15",
                "ano": "2026",
                "mes": "11",
            },
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse("app_financas:extrato") + "?ano=2026&mes=5")

    def test_exportar_extrato_csv_com_filtro_categoria_e_mes_invalido(self) -> None:
        """Exporta CSV respeitando filtro de categoria e tratando mês fora de faixa."""
        criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="50.00",
            descricao="Farmacia",
            categoria="saude",
        )
        criar_lancamento(
            usuario=self.usuario,
            tipo=LancamentoFinanceiro.TIPO_DESPESA,
            valor="40.00",
            descricao="Lanche",
            categoria="alimentacao",
        )
        # Requisita com mês inválido (99) e filtro categoria saude
        res = self.client.get(reverse("app_financas:exportar_csv") + "?ano=2026&mes=99&categoria=saude")
        self.assertEqual(res.status_code, 200)
        conteudo = res.content.decode("utf-8")
        self.assertIn("Farmacia", conteudo)
        self.assertNotIn("Lanche", conteudo)


class FinancasAIToolsTestCase(TestCase):
    """Testa a integração das Function Callings do Gemini no app_chatbot/tools.py."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user(username="operador_ai", password="senha_segura_123")
        # Cria uma sessão de chat associada ao usuário
        from app_chatbot.models import SessaoChat
        self.sessao = SessaoChat.objects.create(usuario=self.usuario, titulo="Sessao Finanças")

    def test_tool_registrar_e_consultar_financas(self) -> None:
        """Garante que as tools registrar_transacao_financeira e consultar_extrato_financeiro operam perfeitamente."""
        from app_chatbot.tools import obter_ferramentas_para_sessao

        ferramentas = {f.__name__: f for f in obter_ferramentas_para_sessao(self.sessao)}
        self.assertIn("registrar_transacao_financeira", ferramentas)
        self.assertIn("consultar_extrato_financeiro", ferramentas)

        # 1. Executa tool de registro
        func_registrar = ferramentas["registrar_transacao_financeira"]
        res_reg = func_registrar(
            tipo="DESPESA",
            valor="85.50",
            descricao="Jantar com a equipe",
            categoria="alimentacao",
        )
        self.assertIn("Transação contábil registrada com sucesso", res_reg)
        self.assertIn("R$ 85.50", res_reg)

        # 2. Executa tool de consulta
        func_consultar = ferramentas["consultar_extrato_financeiro"]
        res_cons = func_consultar()
        self.assertIn("BALANÇO FINANCEIRO LOCAL", res_cons)
        self.assertIn("Jantar com a equipe", res_cons)
        self.assertIn("R$ 85.50", res_cons)

