"""Modelos de dados para o módulo de finanças pessoais soberanas.

Implementa o model canônico único LancamentoFinanceiro com precisão Decimal,
índice composto de alta frequência e Soft Delete contábil.
"""

from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class LancamentoFinanceiro(models.Model):
    """Entidade contábil central para despesas e receitas do operador.

    Garante precisão monetária estrita através de DecimalField, sem arredondamentos de float,
    e preserva rastreabilidade através de soft delete pelo campo 'ativo'.
    """

    TIPO_RECEITA = "RECEITA"
    TIPO_DESPESA = "DESPESA"

    TIPOS_CHOICES = (
        (TIPO_RECEITA, "Receita (Crédito)"),
        (TIPO_DESPESA, "Despesa (Débito)"),
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lancamentos_financeiros",
        verbose_name="Operador",
        help_text="Usuário proprietário da transação financeira.",
    )
    tipo = models.CharField(
        max_length=7,
        choices=TIPOS_CHOICES,
        verbose_name="Tipo de Lançamento",
        help_text="Indica se é um crédito (RECEITA) ou débito (DESPESA).",
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Monetário (R$)",
        help_text="Valor monetário estritamente positivo em formato Decimal.",
    )
    categoria = models.CharField(
        max_length=50,
        db_index=True,
        default="outros",
        verbose_name="Categoria",
        help_text="Categoria normalizada em minúsculas (ex: alimentacao, projetos, servidores).",
    )
    descricao = models.CharField(
        max_length=255,
        verbose_name="Descrição do Lançamento",
        help_text="Resumo ou justificativa do lançamento.",
    )
    data_competencia = models.DateField(
        default=timezone.localdate,
        verbose_name="Data de Competência",
        help_text="Data fiscal em que a transação ocorreu ou foi faturada.",
    )
    ativo = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Ativo",
        help_text="Indica se o lançamento é válido (Soft Delete auditável).",
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação",
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização",
    )

    class Meta:
        verbose_name = "Lançamento Financeiro"
        verbose_name_plural = "Lançamentos Financeiros"
        ordering = ["-data_competencia", "-criado_em"]
        indexes = [
            models.Index(
                fields=["usuario", "data_competencia", "ativo"],
                name="idx_fin_usr_data_ativo",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(valor__gt=Decimal("0.00")),
                name="chk_fin_valor_positivo",
            ),
        ]

    def __str__(self) -> str:
        sinal = "+" if self.tipo == self.TIPO_RECEITA else "-"
        return f"[{self.data_competencia}] {sinal}R$ {self.valor:.2f} ({self.categoria}): {self.descricao}"
