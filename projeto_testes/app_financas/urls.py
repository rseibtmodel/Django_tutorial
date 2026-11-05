"""Roteamento de URLs para o aplicativo app_financas."""

from django.urls import path
from . import views

app_name = "app_financas"

urlpatterns = [
    path("", views.extrato_financeiro, name="extrato"),
    path("criar/", views.criar_lancamento_view, name="criar"),
    path("excluir/<int:lancamento_id>/", views.remover_lancamento_view, name="excluir"),
    path("exportar/", views.exportar_extrato_csv_view, name="exportar_csv"),
]

