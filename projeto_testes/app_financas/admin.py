"""Configuração do Django Admin para app_financas."""

from django.contrib import admin
from .models import LancamentoFinanceiro


@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    """Admin customizado para auditoria de lançamentos financeiros."""

    list_display = (
        "id",
        "usuario",
        "data_competencia",
        "tipo",
        "valor",
        "categoria",
        "descricao",
        "ativo",
    )
    list_filter = ("tipo", "ativo", "data_competencia", "categoria")
    search_fields = ("descricao", "categoria", "usuario__username")
    ordering = ("-data_competencia", "-criado_em")
    readonly_fields = ("criado_em", "atualizado_em")

