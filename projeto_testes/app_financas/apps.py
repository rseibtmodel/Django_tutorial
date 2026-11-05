"""Configurações da aplicação de Gestão de Finanças Pessoais Soberanas."""

from django.apps import AppConfig


class AppFinancasConfig(AppConfig):
    """Configuração do aplicativo modular app_financas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "app_financas"
    verbose_name = "Gestão de Finanças Pessoais Soberanas"

