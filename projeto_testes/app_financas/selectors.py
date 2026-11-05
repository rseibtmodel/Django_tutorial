"""Camada de seletores e consultas de leitura pura (CQRS) para app_financas.

Centraliza filtros de alta performance, agregações diretas via SQL (Sum, Count)
e aniquila o problema N+1 mantendo isolamento estrito por usuário.
"""

from decimal import Decimal
import logging
from typing import Any, Optional

from django.contrib.auth.models import User
from django.db.models import Count, Q, QuerySet, Sum

from .models import LancamentoFinanceiro

logger = logging.getLogger(__name__)


def obter_extrato_mensal(
    *,
    usuario: User,
    ano: int,
    mes: int,
    categoria: Optional[str] = None,
) -> QuerySet[LancamentoFinanceiro]:
    """Retorna o QuerySet dos lançamentos ativos de uma competência mensal específica.

    Utiliza o índice composto ('usuario', 'data_competencia', 'ativo') para garantir
    tempo de resposta sub-milissegundo no SQLite local.

    Args:
        usuario: Operador proprietário das transações.
        ano: Ano de competência (ex: 2026).
        mes: Mês de competência (1 a 12).
        categoria: Filtro opcional por slug de categoria.

    Returns:
        QuerySet[LancamentoFinanceiro]: Lista ordenada por data e criação decrescente.
    """
    qs = LancamentoFinanceiro.objects.filter(
        usuario=usuario,
        ativo=True,
        data_competencia__year=ano,
        data_competencia__month=mes,
    )

    if categoria:
        cat_limpa = categoria.strip().lower()
        if cat_limpa:
            qs = qs.filter(categoria=cat_limpa)

    return qs.order_by("-data_competencia", "-criado_em")


def calcular_balanco_periodo(
    *,
    usuario: User,
    ano: int,
    mes: int,
) -> dict[str, Any]:
    """Calcula o balanço orçamentário agregado do operador no mês em uma única query SQL.

    Retorna receitas, despesas, saldo líquido e a taxa de poupança percentual.

    Args:
        usuario: Operador autenticado.
        ano: Ano de competência.
        mes: Mês de competência.

    Returns:
        dict[str, Any]: Métricas orçamentárias quantizadas e prontas para exibição.
    """
    qs = LancamentoFinanceiro.objects.filter(
        usuario=usuario,
        ativo=True,
        data_competencia__year=ano,
        data_competencia__month=mes,
    )

    resultado = qs.aggregate(
        total_receitas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_RECEITA)),
        total_despesas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_DESPESA)),
        total_lancamentos=Count("id"),
    )

    receitas: Decimal = resultado["total_receitas"] or Decimal("0.00")
    despesas: Decimal = resultado["total_despesas"] or Decimal("0.00")
    saldo_liquido: Decimal = receitas - despesas

    taxa_poupanca: float = 0.0
    if receitas > Decimal("0.00"):
        # Taxa de poupança = (Saldo Líquido / Total Receitas) * 100
        poupanca_dec = (saldo_liquido / receitas) * Decimal("100.0")
        taxa_poupanca = round(float(poupanca_dec), 1)

    return {
        "ano": ano,
        "mes": mes,
        "total_receitas": receitas.quantize(Decimal("0.01")),
        "total_despesas": despesas.quantize(Decimal("0.01")),
        "saldo_liquido": saldo_liquido.quantize(Decimal("0.01")),
        "taxa_poupanca": taxa_poupanca,
        "total_lancamentos": resultado["total_lancamentos"] or 0,
    }


def listar_categorias_ativas(*, usuario: User) -> list[str]:
    """Retorna a relação de categorias distintas ativas já utilizadas pelo usuário.

    Args:
        usuario: Operador autenticado.

    Returns:
        list[str]: Lista de nomes de categoria em ordem alfabética.
    """
    categorias = (
        LancamentoFinanceiro.objects.filter(usuario=usuario, ativo=True)
        .values_list("categoria", flat=True)
        .distinct()
        .order_by("categoria")
    )
    return list(categorias)


def obter_lancamento_por_id(*, lancamento_id: int, usuario: User) -> Optional[LancamentoFinanceiro]:
    """Recupera um lançamento ativo pontual com verificação de posse (anti-IDOR).

    Args:
        lancamento_id: Chave primária.
        usuario: Operador logado.

    Returns:
        Optional[LancamentoFinanceiro]: Instância encontrada ou None.
    """
    return LancamentoFinanceiro.objects.filter(
        id=lancamento_id,
        usuario=usuario,
        ativo=True,
    ).first()

