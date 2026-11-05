"""Exceções de domínio customizadas para o módulo app_financas.

Centraliza erros de regras de negócio, sanitização monetária e permissões contábeis.
"""


class FinancasBaseError(Exception):
    """Exceção base para todas as falhas de domínio financeiro."""


class ValorInvalidoError(FinancasBaseError):
    """Disparada quando o valor monetário informado for inválido, nulo ou menor/igual a zero."""


class LancamentoNaoEncontradoError(FinancasBaseError):
    """Disparada quando um lançamento solicitado não existir ou pertencer a outro usuário."""


class TransacaoInvalidaError(FinancasBaseError):
    """Disparada quando os parâmetros de uma transação ferirem as regras contábeis."""


class DataCompetenciaInvalidaError(FinancasBaseError):
    """Disparada quando a data de competência fornecida for ilegível ou inválida."""

