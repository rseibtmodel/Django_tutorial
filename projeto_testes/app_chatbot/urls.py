from django.urls import path
from . import views

app_name = "app_chatbot"

urlpatterns = [
    path("", views.painel_chat, name="painel"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("stream/", views.chat_stream, name="chat_stream"),
    path("sessao/nova/", views.criar_sessao, name="criar_sessao"),
    path("sessao/<uuid:sessao_id>/renomear/", views.renomear_sessao, name="renomear_sessao"),
    path("sessao/<uuid:sessao_id>/deletar/", views.deletar_sessao, name="deletar_sessao"),
    path("sessao/<uuid:sessao_id>/persona/", views.alterar_persona, name="alterar_persona"),
    path("sessao/<uuid:sessao_id>/upload-doc/", views.upload_documento, name="upload_documento"),
    path("sessao/<uuid:sessao_id>/doc/<uuid:doc_id>/deletar/", views.deletar_documento, name="deletar_documento"),
    path("sessao/<uuid:sessao_id>/mensagens/", views.listar_mensagens, name="listar_mensagens"),
    path("personas/", views.gerenciar_personas, name="gerenciar_personas"),
    path("personas/salvar/", views.salvar_persona, name="salvar_persona"),
    path("personas/<uuid:persona_id>/deletar/", views.deletar_persona, name="deletar_persona"),
    path("perfil/salvar/", views.salvar_perfil_usuario, name="salvar_perfil_usuario"),
    path("sessao/<uuid:sessao_id>/exportar/markdown/", views.exportar_sessao_markdown, name="exportar_sessao_markdown"),
    path("dashboard/", views.dashboard_telemetria, name="dashboard"),
]
