"""Camada de serviços e regras de negócio para o aplicativo app_financas.

Centraliza mutações de dados contábeis, sanitização estrita de valores monetários,
parsing de comandos telegráficos e Soft Delete auditável sob transações atômicas.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import logging
import re
from typing import Any, Optional, Union

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from .exceptions import (
    DataCompetenciaInvalidaError,
    LancamentoNaoEncontradoError,
    TransacaoInvalidaError,
    ValorInvalidoError,
)
from .models import LancamentoFinanceiro

logger = logging.getLogger(__name__)


def sanitizar_e_validar_valor(raw_val: Union[str, int, float, Decimal]) -> Decimal:
    """Normaliza e valida valores monetários convertendo-os para Decimal(0.01).

    Aceita strings com vírgula, ponto, separadores de milhar e símbolos de moeda,
    garantindo precisão contábil estrita e rejeitando valores nulos, negativos ou zerados.

    Args:
        raw_val: Valor monetário fornecido pelo operador ou IA.

    Returns:
        Decimal: Valor sanitizado e quantizado em duas casas decimais.

    Raises:
        ValorInvalidoError: Se o valor for não-numérico, vazio ou menor/igual a zero.
    """
    if raw_val is None:
        raise ValorInvalidoError("O valor monetário não pode ser nulo.")

    if isinstance(raw_val, Decimal):
        valor_dec = raw_val
    elif isinstance(raw_val, (int, float)):
        try:
            valor_dec = Decimal(str(raw_val))
        except (InvalidOperation, ValueError):
            raise ValorInvalidoError(f"Valor numérico inválido: {raw_val}")
    elif isinstance(raw_val, str):
        texto = raw_val.strip()
        if not texto:
            raise ValorInvalidoError("O valor monetário informado está em branco.")

        # Remove símbolos monetários comuns (R$, $, etc.) mantendo apenas números, pontos e vírgulas
        texto_limpo = re.sub(r"[^\d,\.-]", "", texto)

        # Detecta padrão brasileiro (1.250,50 ou 45,50) vs padrão internacional (1,250.50 ou 45.50)
        if "," in texto_limpo and "." in texto_limpo:
            if texto_limpo.rfind(",") > texto_limpo.rfind("."):
                # Padrão BR: ponto é milhar, vírgula é decimal -> "1.250,50" -> "1250.50"
                texto_limpo = texto_limpo.replace(".", "").replace(",", ".")
            else:
                # Padrão US: vírgula é milhar, ponto é decimal -> "1,250.50" -> "1250.50"
                texto_limpo = texto_limpo.replace(",", "")
        elif "," in texto_limpo:
            # Apenas vírgula -> substitui por ponto decimal -> "45,50" -> "45.50"
            texto_limpo = texto_limpo.replace(",", ".")

        try:
            valor_dec = Decimal(texto_limpo)
        except (InvalidOperation, ValueError):
            raise ValorInvalidoError(f"Formato numérico ilegível para moeda: '{raw_val}'.")
    else:
        raise ValorInvalidoError(f"Tipo de dado não suportado para valor monetário: {type(raw_val)}.")

    # Quantização contábil estrita para 2 casas decimais
    try:
        valor_dec = valor_dec.quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ValorInvalidoError(f"Falha ao quantizar o valor para duas casas decimais: '{raw_val}'.")

    if valor_dec <= Decimal("0.00"):
        raise ValorInvalidoError(f"O valor monetário deve ser estritamente positivo (> 0). Fornecido: {valor_dec}.")

    return valor_dec


def parse_comando_telegrafico(comando: str) -> dict[str, Any]:
    """Interpreta comandos rápidos de linha única (/gasto ou /receita).

    Suporta sintaxes rápidas como:
        /gasto 45.00 almoco [alimentacao]
        /receita 1200.00 consultoria backend [projetos]
        /gasto 12.50 cafe com pao

    Args:
        comando: Linha de texto digitada no prompt ou chat.

    Returns:
        dict[str, Any]: Dicionário contendo tipo, valor, descricao e categoria.

    Raises:
        TransacaoInvalidaError: Se a sintaxe for incompreensível ou faltar tipo/valor.
    """
    texto = comando.strip()
    if not texto:
        raise TransacaoInvalidaError("Comando telegráfico vazio.")

    # Remove barra inicial opcional (/gasto -> gasto)
    if texto.startswith("/"):
        texto = texto[1:]

    partes = texto.split()
    if len(partes) < 2:
        raise TransacaoInvalidaError(
            "Sintaxe insuficiente. Use: /gasto <valor> <descricao> [categoria] ou /receita <valor> <descricao> [categoria]."
        )

    verbo = partes[0].lower()
    if verbo in ("gasto", "despesa", "debito", "saida"):
        tipo = LancamentoFinanceiro.TIPO_DESPESA
    elif verbo in ("receita", "credito", "entrada", "ganho"):
        tipo = LancamentoFinanceiro.TIPO_RECEITA
    else:
        raise TransacaoInvalidaError(
            f"Tipo de transação '{verbo}' não reconhecido. Use '/gasto' ou '/receita'."
        )

    raw_valor = partes[1]
    valor = sanitizar_e_validar_valor(raw_valor)

    resto = " ".join(partes[2:]).strip()
    if not resto:
        # Se nenhuma descrição foi dada, assume default genérico
        descricao = f"Lançamento via comando ({verbo})"
        categoria = "outros"
    else:
        # Verifica se há categoria explicitada entre colchetes no final, ex: "almoco executivo [alimentacao]"
        match_cat = re.search(r"\[(.*?)\]$", resto)
        if match_cat:
            categoria_extraida = match_cat.group(1).strip()
            descricao = resto[: match_cat.start()].strip()
            categoria = categoria_extraida if categoria_extraida else "outros"
        else:
            descricao = resto
            categoria = "outros"

    if not descricao:
        descricao = f"Lançamento de {categoria}"

    return {
        "tipo": tipo,
        "valor": valor,
        "descricao": descricao[:255],
        "categoria": categoria.lower()[:50],
    }


@transaction.atomic
def criar_lancamento(
    *,
    usuario: User,
    tipo: str,
    valor: Union[str, int, float, Decimal],
    descricao: str,
    categoria: Optional[str] = None,
    data_competencia: Optional[Union[date, str]] = None,
) -> LancamentoFinanceiro:
    """Cria e persiste um novo lançamento financeiro com validação determinística.

    Args:
        usuario: Operador proprietário do lançamento.
        tipo: 'RECEITA' ou 'DESPESA'.
        valor: Montante monetário (> 0).
        descricao: Resumo da transação.
        categoria: Categoria opcional (normalizada em minúsculas).
        data_competencia: Data contábil (objeto date ou string 'YYYY-MM-DD').

    Returns:
        LancamentoFinanceiro: Instância salva no banco de dados.

    Raises:
        TransacaoInvalidaError: Se os dados forem inconsistentes.
        ValorInvalidoError: Se o valor for inválido ou negativo.
        DataCompetenciaInvalidaError: Se a data fornecida for inválida.
    """
    if not usuario or not usuario.is_authenticated:
        raise TransacaoInvalidaError("Usuário autenticado obrigatório para criar lançamentos.")

    tipo_normalizado = tipo.upper().strip() if isinstance(tipo, str) else ""
    if tipo_normalizado not in (
        LancamentoFinanceiro.TIPO_RECEITA,
        LancamentoFinanceiro.TIPO_DESPESA,
    ):
        raise TransacaoInvalidaError(
            f"Tipo '{tipo}' inválido. Escolha entre '{LancamentoFinanceiro.TIPO_RECEITA}' e '{LancamentoFinanceiro.TIPO_DESPESA}'."
        )

    valor_dec = sanitizar_e_validar_valor(valor)

    desc_limpa = descricao.strip() if isinstance(descricao, str) else ""
    if not desc_limpa:
        raise TransacaoInvalidaError("A descrição do lançamento não pode estar vazia.")

    # Normalização de categoria: letras, números, hífen e underline em minúsculas
    cat_normalizada = "outros"
    if categoria and isinstance(categoria, str):
        cat_filtrada = re.sub(r"[^a-zA-Z0-9_\-\s]", "", categoria.strip().lower())
        cat_filtrada = re.sub(r"\s+", "-", cat_filtrada)
        if cat_filtrada:
            cat_normalizada = cat_filtrada[:50]

    # Parsing da data de competência
    if data_competencia is None:
        data_final = timezone.localdate()
    elif isinstance(data_competencia, date):
        data_final = data_competencia
    elif isinstance(data_competencia, str):
        data_str = data_competencia.strip()
        formatos = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d")
        data_parsed = None
        for fmt in formatos:
            try:
                data_parsed = datetime.strptime(data_str, fmt).date()
                break
            except ValueError:
                continue
        if data_parsed is None:
            raise DataCompetenciaInvalidaError(
                f"Data de competência '{data_competencia}' não reconhecida. Use o formato AAAA-MM-DD ou DD/MM/AAAA."
            )
        data_final = data_parsed
    else:
        raise DataCompetenciaInvalidaError(f"Tipo de data inválido: {type(data_competencia)}.")

    lancamento = LancamentoFinanceiro.objects.create(
        usuario=usuario,
        tipo=tipo_normalizado,
        valor=valor_dec,
        categoria=cat_normalizada,
        descricao=desc_limpa[:255],
        data_competencia=data_final,
        ativo=True,
    )

    logger.info(
        "Lançamento financeiro #%d criado para o usuário %s: %s R$ %.2f (%s)",
        lancamento.id,
        usuario.username,
        lancamento.tipo,
        lancamento.valor,
        lancamento.categoria,
    )
    return lancamento


@transaction.atomic
def excluir_lancamento(*, lancamento_id: int, usuario: User) -> LancamentoFinanceiro:
    """Executa o Soft Delete contábil de um lançamento financeiro pertencente ao usuário.

    Preserva a trilha auditável alterando o campo 'ativo' para False.

    Args:
        lancamento_id: Chave primária do lançamento a ser inativado.
        usuario: Operador logado (trava anti-IDOR).

    Returns:
        LancamentoFinanceiro: Instância inativada.

    Raises:
        LancamentoNaoEncontradoError: Se o lançamento não for localizado ou pertencer a outro usuário.
    """
    try:
        lancamento = LancamentoFinanceiro.objects.get(
            id=lancamento_id,
            usuario=usuario,
            ativo=True,
        )
    except LancamentoFinanceiro.DoesNotExist:
        raise LancamentoNaoEncontradoError(
            f"Lançamento #{lancamento_id} não encontrado ou já cancelado."
        )

    lancamento.ativo = False
    lancamento.save(update_fields=["ativo", "atualizado_em"])

    logger.info(
        "Lançamento financeiro #%d inativado (soft delete) pelo usuário %s.",
        lancamento.id,
        usuario.username,
    )
    return lancamento


def processar_comando_telegrafico(
    *,
    usuario: User,
    comando: str,
    data_competencia: Optional[Union[date, str]] = None,
) -> LancamentoFinanceiro:
    """Orquestra o parsing de uma linha de comando telegráfico e a criação do lançamento.

    Args:
        usuario: Operador autenticado.
        comando: Comando em linha única (/gasto ... ou /receita ...).
        data_competencia: Data contábil opcional.

    Returns:
        LancamentoFinanceiro: Registro persistido com sucesso.
    """
    parsed = parse_comando_telegrafico(comando)
    return criar_lancamento(
        usuario=usuario,
        tipo=parsed["tipo"],
        valor=parsed["valor"],
        descricao=parsed["descricao"],
        categoria=parsed["categoria"],
        data_competencia=data_competencia,
    )

