"""Camada de visualização (Function-Based Views) para o console app_financas.

Implementa telas interativas no padrão Terminal Dark & Verde Neon,
com formulários telegráficos de linha única, atalhos de teclado e exportação CSV.
"""

import csv
from datetime import date
from decimal import Decimal
import io
import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .exceptions import FinancasBaseError
from .selectors import (
    calcular_balanco_periodo,
    listar_categorias_ativas,
    obter_extrato_mensal,
)
from .services import (
    criar_lancamento,
    excluir_lancamento,
    processar_comando_telegrafico,
)

logger = logging.getLogger(__name__)


def _calcular_meses_adjacentes(ano: int, mes: int) -> tuple[int, int, int, int]:
    """Calcula o mês anterior e próximo para navegação por hotkeys.

    Args:
        ano: Ano corrente.
        mes: Mês corrente.

    Returns:
        tuple[int, int, int, int]: (ano_anterior, mes_anterior, ano_proximo, mes_proximo).
    """
    if mes == 1:
        ano_ant, mes_ant = ano - 1, 12
    else:
        ano_ant, mes_ant = ano, mes - 1

    if mes == 12:
        ano_prox, mes_prox = ano + 1, 1
    else:
        ano_prox, mes_prox = ano, mes + 1

    return ano_ant, mes_ant, ano_prox, mes_prox


@login_required
@require_http_methods(["GET"])
def extrato_financeiro(request: HttpRequest) -> HttpResponse:
    """Renderiza o console de extrato financeiro no padrão Terminal Dark.

    Args:
        request: Requisição HTTP autenticada.

    Returns:
        HttpResponse: Página HTML com dados analíticos e atalhos.
    """
    agora = timezone.localdate()
    raw_ano = request.GET.get("ano")
    raw_mes = request.GET.get("mes")
    categoria_filtro = request.GET.get("categoria", "").strip()

    try:
        ano = int(raw_ano) if raw_ano else agora.year
        mes = int(raw_mes) if raw_mes else agora.month
        if not (1 <= mes <= 12):
            mes = agora.month
    except (ValueError, TypeError):
        ano = agora.year
        mes = agora.month

    ano_ant, mes_ant, ano_prox, mes_prox = _calcular_meses_adjacentes(ano, mes)

    lancamentos = obter_extrato_mensal(
        usuario=request.user,
        ano=ano,
        mes=mes,
        categoria=categoria_filtro if categoria_filtro else None,
    )

    balanco = calcular_balanco_periodo(
        usuario=request.user,
        ano=ano,
        mes=mes,
    )

    categorias_disponiveis = listar_categorias_ativas(usuario=request.user)

    contexto: dict[str, Any] = {
        "lancamentos": lancamentos,
        "balanco": balanco,
        "ano_atual": ano,
        "mes_atual": mes,
        "mes_nome": date(ano, mes, 1).strftime("%B").capitalize(),
        "ano_anterior": ano_ant,
        "mes_anterior": mes_ant,
        "ano_proximo": ano_prox,
        "mes_proximo": mes_prox,
        "categoria_filtro": categoria_filtro,
        "categorias_disponiveis": categorias_disponiveis,
        "hoje": agora,
    }

    return render(request, "app_financas/extrato.html", contexto)


@login_required
@require_http_methods(["POST"])
def criar_lancamento_view(request: HttpRequest) -> HttpResponse:
    """Processa a criação de um lançamento via comando telegráfico ou form tradicional.

    Args:
        request: Requisição POST com parâmetros do formulário.

    Returns:
        HttpResponse: Redirecionamento para o extrato da competência.
    """
    ano_dest = request.POST.get("ano") or request.GET.get("ano")
    mes_dest = request.POST.get("mes") or request.GET.get("mes")
    redirect_url = reverse("app_financas:extrato")
    if ano_dest and mes_dest:
        redirect_url += f"?ano={ano_dest}&mes={mes_dest}"

    comando = request.POST.get("comando_telegrafico", "").strip()

    try:
        if comando:
            lancamento = processar_comando_telegrafico(
                usuario=request.user,
                comando=comando,
            )
            sinal = "+" if lancamento.tipo == lancamento.TIPO_RECEITA else "-"
            messages.success(
                request,
                f"[OK] Lançamento registrado: {sinal}R$ {lancamento.valor:.2f} "
                f"({lancamento.categoria}) — {lancamento.descricao}",
            )
        else:
            tipo = request.POST.get("tipo", "").strip()
            valor = request.POST.get("valor", "").strip()
            descricao = request.POST.get("descricao", "").strip()
            categoria = request.POST.get("categoria", "").strip()
            data_comp = request.POST.get("data_competencia", "").strip()

            lancamento = criar_lancamento(
                usuario=request.user,
                tipo=tipo,
                valor=valor,
                descricao=descricao,
                categoria=categoria,
                data_competencia=data_comp if data_comp else None,
            )
            sinal = "+" if lancamento.tipo == lancamento.TIPO_RECEITA else "-"
            messages.success(
                request,
                f"[OK] Lançamento cadastrado com sucesso: {sinal}R$ {lancamento.valor:.2f} ({lancamento.descricao})",
            )
        # Redireciona com precisão para a competência real do lançamento criado
        redirect_url = (
            f"{reverse('app_financas:extrato')}?ano={lancamento.data_competencia.year}&mes={lancamento.data_competencia.month}"
        )
    except FinancasBaseError as err_fin:
        messages.error(request, f"[ERRO] {str(err_fin)}")
    except Exception as err_gen:
        logger.exception("Falha inesperada ao processar lançamento financeiro: %s", err_gen)
        messages.error(request, f"[ERRO FATAL] Ocorreu uma falha no processamento: {str(err_gen)}")

    return redirect(redirect_url)


@login_required
@require_http_methods(["POST"])
def remover_lancamento_view(request: HttpRequest, lancamento_id: int) -> HttpResponse:
    """Executa o Soft Delete contábil de um lançamento financeiro do usuário.

    Args:
        request: Requisição POST autenticada.
        lancamento_id: Identificador da transação.

    Returns:
        HttpResponse: Redirecionamento para a página de extrato.
    """
    ano_dest = request.POST.get("ano")
    mes_dest = request.POST.get("mes")
    redirect_url = reverse("app_financas:extrato")
    if ano_dest and mes_dest:
        redirect_url += f"?ano={ano_dest}&mes={mes_dest}"

    try:
        lancamento = excluir_lancamento(
            lancamento_id=lancamento_id,
            usuario=request.user,
        )
        messages.success(
            request,
            f"[CANCELADO] Lançamento #{lancamento.id} ({lancamento.descricao}) inativado com sucesso.",
        )
    except FinancasBaseError as err_fin:
        messages.error(request, f"[ERRO] {str(err_fin)}")
    except Exception as err_gen:
        logger.exception("Falha ao inativar lançamento #%s: %s", lancamento_id, err_gen)
        messages.error(request, f"[ERRO FATAL] Não foi possível inativar o lançamento: {str(err_gen)}")

    return redirect(redirect_url)


@login_required
@require_http_methods(["GET"])
def exportar_extrato_csv_view(request: HttpRequest) -> HttpResponse:
    """Gera um arquivo CSV estruturado do extrato mensal com compatibilidade UTF-8 BOM.

    Args:
        request: Requisição GET com parâmetros de ano e mês.

    Returns:
        HttpResponse: Arquivo CSV pronto para download.
    """
    agora = timezone.localdate()
    categoria_filtro = request.GET.get("categoria", "").strip()

    try:
        ano = int(request.GET.get("ano", agora.year))
        mes = int(request.GET.get("mes", agora.month))
        if not (1 <= mes <= 12):
            mes = agora.month
    except (ValueError, TypeError):
        ano = agora.year
        mes = agora.month

    lancamentos = obter_extrato_mensal(
        usuario=request.user,
        ano=ano,
        mes=mes,
        categoria=categoria_filtro if categoria_filtro else None,
    )

    buffer = io.StringIO()
    # Adiciona BOM UTF-8 (\ufeff) para correta abertura no Excel no Windows/Mac
    buffer.write("\ufeff")
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        "ID",
        "Data Competencia",
        "Tipo",
        "Valor (R$)",
        "Categoria",
        "Descricao",
        "Data Cadastro",
    ])

    for l in lancamentos:
        writer.writerow([
            l.id,
            l.data_competencia.strftime("%d/%m/%Y"),
            l.tipo,
            f"{l.valor:.2f}".replace(".", ","),
            l.categoria,
            l.descricao,
            l.criado_em.strftime("%d/%m/%Y %H:%M"),
        ])

    csv_data = buffer.getvalue()
    buffer.close()

    nome_arquivo = f"extrato_financas_{ano}_{mes:02d}_{request.user.username}.csv"
    response = HttpResponse(csv_data, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
    return response

