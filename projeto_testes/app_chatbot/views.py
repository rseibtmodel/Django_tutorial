"""Camada de visualizações (FBVs) do Chatbot.

Atua como thin-view orquestradora: processa parâmetros HTTP, valida autenticação,
invoca seletores de leitura e serviços de domínio, e renderiza templates ou JSON.
"""

import os
import uuid
from typing import Any, Optional
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_POST

from .exceptions import (
    DocumentoInvalidoError,
    PerfilInvalidoError,
    PersonaInvalidaError,
    SessaoNaoEncontradaError,
    TituloInvalidoError,
)
from .models import DocumentoSessao, Persona, SessaoChat
from .selectors import (
    listar_documentos_sessao,
    listar_mensagens_sessao,
    listar_personas_disponiveis,
    listar_sessoes_usuario,
    obter_documento_por_id,
    obter_metricas_telemetria_usuario,
    obter_persona_por_id_ou_slug,
    obter_sessao_por_id,
    obter_ultima_sessao_acessada,
)
from .services import (
    ChatOrchestratorService,
    alterar_persona_sessao,
    anexar_documento_sessao,
    atualizar_perfil_usuario,
    atualizar_persona_customizada,
    criar_persona_customizada,
    criar_sessao_para_usuario,
    deletar_persona_customizada,
    excluir_sessao_e_vetores,
    garantir_persona_padrao,
    gerar_markdown_conversa,
    obter_ou_criar_perfil_usuario,
    processar_e_indexar_documento,
    remover_documento_e_vetores,
    renomear_sessao_usuario,
)


def login_view(request: HttpRequest) -> HttpResponse:
    """Realiza a autenticação de usuários no terminal do chatbot."""
    if request.user.is_authenticated:
        return redirect("app_chatbot:painel")

    erro: str = ""
    proxima_url: str = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        usuario_input: str = request.POST.get("username", "").strip()
        senha_input: str = request.POST.get("password", "")

        user = authenticate(request, username=usuario_input, password=senha_input)
        if user is not None:
            login(request, user)
            if proxima_url:
                return redirect(proxima_url)
            return redirect("app_chatbot:painel")
        else:
            erro = "Credenciais inválidas. Verifique seu usuário e senha."

    return render(
        request,
        "app_chatbot/login.html",
        {"erro": erro, "next": proxima_url},
    )


def logout_view(request: HttpRequest) -> HttpResponseRedirect:
    """Encerra a sessão autenticada do usuário."""
    logout(request)
    return redirect("app_chatbot:login")


@login_required
@require_GET
def painel_chat(request: HttpRequest) -> HttpResponse:
    """Renderiza a interface do Chatbot abrindo automaticamente a última sessão acessada."""
    sessao_id = request.GET.get("sessao_id")
    sessao: Optional[SessaoChat] = None

    if sessao_id:
        sessao = obter_sessao_por_id(sessao_id=sessao_id, usuario=request.user)
        if not sessao:
            return HttpResponse("Sessão não encontrada ou não autorizada.", status=404)
    else:
        sessao = obter_ultima_sessao_acessada(usuario=request.user)

    if not sessao:
        sessao = criar_sessao_para_usuario(usuario=request.user)

    assert sessao is not None

    # Garante que a sessão tenha uma persona vinculada defensivamente
    if not sessao.persona:
        sessao.persona = garantir_persona_padrao()
        sessao.save(update_fields=["persona"])

    # Consulta a lista de sessões uma única vez após determinar a sessão ativa
    sessoes = listar_sessoes_usuario(usuario=request.user)

    documentos = listar_documentos_sessao(sessao=sessao)
    personas = listar_personas_disponiveis(usuario=request.user)
    perfil = obter_ou_criar_perfil_usuario(usuario=request.user)

    context: dict[str, Any] = {
        "sessao": sessao,
        "sessoes": sessoes,
        "mensagens": listar_mensagens_sessao(sessao=sessao),
        "documentos": documentos,
        "personas": personas,
        "perfil": perfil,
    }
    return render(request, "app_chatbot/chat.html", context)


@login_required
@require_GET
def criar_sessao(request: HttpRequest) -> HttpResponseRedirect:
    """Cria uma nova sessão de chat isolada para o usuário autenticado."""
    nova_sessao = criar_sessao_para_usuario(usuario=request.user)
    url_painel: str = reverse("app_chatbot:painel")
    return redirect(f"{url_painel}?sessao_id={nova_sessao.id}")


@login_required
@require_POST
def renomear_sessao(request: HttpRequest, sessao_id: uuid.UUID) -> JsonResponse:
    """Renomeia uma sessão do usuário com validação anti-XSS e limite de tamanho."""
    sessao = obter_sessao_por_id(sessao_id=sessao_id, usuario=request.user)
    if not sessao:
        return JsonResponse({"erro": "Sessão não encontrada."}, status=404)

    novo_titulo_raw: str = request.POST.get("titulo", "")

    try:
        titulo_salvo = renomear_sessao_usuario(sessao=sessao, novo_titulo_raw=novo_titulo_raw)
        return JsonResponse({
            "status": "sucesso",
            "sessao_id": str(sessao.id),
            "titulo": titulo_salvo,
        })
    except TituloInvalidoError as erro:
        return JsonResponse({"erro": str(erro)}, status=400)


@login_required
@require_POST
def alterar_persona(request: HttpRequest, sessao_id: uuid.UUID) -> JsonResponse:
    """Altera a persona comportamental ativa para a sessão informada."""
    sessao = obter_sessao_por_id(sessao_id=sessao_id, usuario=request.user)
    if not sessao:
        return JsonResponse({"erro": "Sessão não encontrada."}, status=404)

    identificador_persona: str = request.POST.get("persona", "")
    try:
        persona = alterar_persona_sessao(
            sessao=sessao,
            identificador_persona=identificador_persona,
        )
        foto_url = persona.foto.url if persona.foto else ""
        return JsonResponse({
            "status": "sucesso",
            "persona_id": str(persona.id),
            "persona_nome": persona.nome,
            "persona_foto": foto_url,
        })
    except PersonaInvalidaError as erro:
        return JsonResponse({"erro": str(erro)}, status=400)


@login_required
@require_POST
def upload_documento(request: HttpRequest, sessao_id: uuid.UUID) -> HttpResponseRedirect:
    """Recebe e processa arquivos enviados para o RAG na sessão ativa com rollback defensivo."""
    sessao = obter_sessao_por_id(sessao_id=sessao_id, usuario=request.user)
    url_painel = f"{reverse('app_chatbot:painel')}?sessao_id={sessao_id}"

    if not sessao:
        messages.error(request, "Sessão não encontrada ou não autorizada.")
        return redirect("app_chatbot:painel")

    arquivo_enviado = request.FILES.get("documento")
    if not arquivo_enviado:
        messages.error(request, "Nenhum arquivo selecionado para upload.")
        return redirect(url_painel)

    try:
        doc = anexar_documento_sessao(
            sessao=sessao,
            arquivo_upload=arquivo_enviado,
            max_mb=5,
        )
        messages.success(
            request,
            f"Documento '{doc.nome_original}' indexado com sucesso ({doc.total_chunks} chunks persistidos)."
        )
    except DocumentoInvalidoError as erro:
        messages.error(request, f"Erro na ingestão do documento: {erro}")
    except Exception as erro:
        messages.error(request, f"Erro inesperado no processamento do documento: {erro}")

    return redirect(url_painel)


@login_required
@require_POST
def deletar_documento(
    request: HttpRequest,
    sessao_id: uuid.UUID,
    doc_id: uuid.UUID
) -> HttpResponseRedirect:
    """Exclui com segurança um documento anexado e expurga seus vetores do ChromaDB."""
    doc = obter_documento_por_id(doc_id=doc_id, usuario=request.user)
    url_painel = f"{reverse('app_chatbot:painel')}?sessao_id={sessao_id}"

    if doc:
        nome_doc = doc.nome_original
        remover_documento_e_vetores(documento=doc)
        messages.success(request, f"Documento '{nome_doc}' e seus vetores foram removidos com sucesso.")

    return redirect(url_painel)


@login_required
@require_POST
def deletar_sessao(request: HttpRequest, sessao_id: uuid.UUID) -> HttpResponseRedirect:
    """Exclui com segurança uma sessão pertencente ao usuário autenticado, expurgando vetores e arquivos."""
    sessao = get_object_or_404(SessaoChat, id=sessao_id, usuario=request.user)
    titulo = sessao.titulo
    try:
        excluir_sessao_e_vetores(sessao=sessao, usuario=request.user)
        messages.success(request, f"Conversa '{titulo}' e sua memória vetorial foram excluídas com sucesso.")
    except Exception as erro:
        messages.error(request, f"Erro ao excluir conversa: {erro}")

    return redirect("app_chatbot:painel")


@login_required
@require_GET
def listar_mensagens(request: HttpRequest, sessao_id: uuid.UUID) -> JsonResponse:
    """Retorna o histórico cronológico de mensagens de uma sessão do usuário."""
    sessao = get_object_or_404(SessaoChat, id=sessao_id, usuario=request.user)
    mensagens = [
        {
            "id": msg.id,
            "papel": msg.papel,
            "conteudo": msg.conteudo,
            "criado_em": msg.criado_em.strftime("%H:%M:%S - %d/%m/%Y"),
        }
        for msg in listar_mensagens_sessao(sessao=sessao)
    ]
    return JsonResponse({"sessao_id": str(sessao.id), "mensagens": mensagens})


@login_required
@require_POST
def chat_stream(request: HttpRequest) -> StreamingHttpResponse:
    """Endpoint de streaming de mensagens com autorização IDOR e isolamento do assistente."""
    sessao_id = request.POST.get("sessao_id")
    mensagem_usuario = request.POST.get("mensagem", "").strip()

    if not mensagem_usuario:
        return StreamingHttpResponse("A mensagem não pode ser vazia.", status=400)

    if sessao_id:
        sessao = get_object_or_404(SessaoChat, id=sessao_id, usuario=request.user)
    else:
        sessao = criar_sessao_para_usuario(
            usuario=request.user,
            titulo_inicial=mensagem_usuario[:35]
        )

    SessaoChat.objects.filter(id=sessao.id).update(acessado_em=timezone.now())

    service = ChatOrchestratorService(sessao=sessao)

    response = StreamingHttpResponse(
        service.executar_chat_stream(texto_usuario=mensagem_usuario),
        content_type="text/plain; charset=utf-8",
    )
    response["X-Accel-Buffering"] = "no"
    return response


# ==============================================================================
# GESTÃO DE PERSONAS E PERFIL DO USUÁRIO
# ==============================================================================

@login_required
@require_GET
def gerenciar_personas(request: HttpRequest) -> HttpResponse:
    """Renderiza a central de gerenciamento de personas customizadas e perfil do operador."""
    personas = listar_personas_disponiveis(usuario=request.user)
    perfil = obter_ou_criar_perfil_usuario(usuario=request.user)

    persona_edit_id = request.GET.get("editar")
    persona_em_edicao = None
    if persona_edit_id:
        persona_em_edicao = obter_persona_por_id_ou_slug(
            identificador=persona_edit_id,
            usuario=request.user,
        )

    context: dict[str, Any] = {
        "personas": personas,
        "perfil": perfil,
        "persona_em_edicao": persona_em_edicao,
        "tom_de_voz_choices": Persona.TOM_DE_VOZ_CHOICES,
        "sexo_choices": Persona.SEXO_CHOICES,
        "escolaridade_choices": Persona.ESCOLARIDADE_CHOICES,
        "msg_sucesso": request.GET.get("msg", ""),
    }
    return render(request, "app_chatbot/personas.html", context)


@login_required
@require_POST
def salvar_persona(request: HttpRequest) -> HttpResponseRedirect:
    """Cria uma nova persona ou atualiza uma persona customizada existente."""
    persona_id = request.POST.get("persona_id")
    nome = request.POST.get("nome", "")
    descricao_curta = request.POST.get("descricao_curta", "")
    tom_de_voz = request.POST.get("tom_de_voz", "objetivo")
    idade_raw = request.POST.get("idade", "")
    sexo = request.POST.get("sexo", "nao_especificado")
    escolaridade = request.POST.get("escolaridade", "nao_especificado")
    profissao_cargo = request.POST.get("profissao_cargo", "")
    historia_background = request.POST.get("historia_background", "")
    diretrizes_comportamento = request.POST.get("diretrizes_comportamento", "")
    foto = request.FILES.get("foto")

    idade = int(idade_raw) if idade_raw.isdigit() else None

    try:
        if persona_id:
            persona = get_object_or_404(Persona, id=persona_id, usuario=request.user)
            atualizar_persona_customizada(
                persona=persona,
                usuario=request.user,
                nome=nome,
                descricao_curta=descricao_curta,
                tom_de_voz=tom_de_voz,
                idade=idade,
                sexo=sexo,
                escolaridade=escolaridade,
                profissao_cargo=profissao_cargo,
                historia_background=historia_background,
                diretrizes_comportamento=diretrizes_comportamento,
                foto_arquivo=foto,
            )
            messages.success(request, f"Persona '{persona.nome}' atualizada com sucesso.")
        else:
            nova_persona = criar_persona_customizada(
                usuario=request.user,
                nome=nome,
                descricao_curta=descricao_curta,
                tom_de_voz=tom_de_voz,
                idade=idade,
                sexo=sexo,
                escolaridade=escolaridade,
                profissao_cargo=profissao_cargo,
                historia_background=historia_background,
                diretrizes_comportamento=diretrizes_comportamento,
                foto_arquivo=foto,
            )
            messages.success(request, f"Persona '{nova_persona.nome}' criada com sucesso.")
    except PersonaInvalidaError as erro:
        messages.error(request, f"Erro ao salvar persona: {erro}")
    except Exception as erro:
        messages.error(request, f"Erro inesperado ao salvar persona: {erro}")

    return redirect("app_chatbot:gerenciar_personas")


@login_required
@require_POST
def deletar_persona(request: HttpRequest, persona_id: uuid.UUID) -> HttpResponseRedirect:
    """Exclui com segurança uma persona customizada pelo criador via camada de serviços."""
    try:
        persona = get_object_or_404(Persona, id=persona_id, usuario=request.user, is_sistema=False)
        nome = deletar_persona_customizada(persona=persona, usuario=request.user)
        messages.success(request, f"Persona '{nome}' removida com sucesso. Conversas ativas foram vinculadas ao assistente padrão.")
    except PersonaInvalidaError as erro:
        messages.error(request, f"Erro ao excluir persona: {erro}")
    except Exception as erro:
        messages.error(request, f"Erro inesperado ao excluir persona: {erro}")

    return redirect("app_chatbot:gerenciar_personas")


@login_required
@require_POST
def salvar_perfil_usuario(request: HttpRequest) -> HttpResponseRedirect:
    """Salva os dados cadastrais e foto de perfil do usuário operador."""
    nome_exibicao = request.POST.get("nome_exibicao", "")
    profissao = request.POST.get("profissao", "")
    data_nascimento = request.POST.get("data_nascimento") or None
    bio = request.POST.get("bio", "")
    foto = request.FILES.get("foto")

    try:
        atualizar_perfil_usuario(
            usuario=request.user,
            nome_exibicao=nome_exibicao,
            profissao=profissao,
            data_nascimento=data_nascimento,
            bio=bio,
            foto_arquivo=foto,
        )
        messages.success(request, "Perfil do operador atualizado com sucesso.")
    except PerfilInvalidoError as erro:
        messages.error(request, f"Erro ao atualizar perfil: {erro}")
    except Exception as erro:
        messages.error(request, f"Erro inesperado ao atualizar perfil: {erro}")

    return redirect("app_chatbot:gerenciar_personas")


# ==============================================================================
# EXPORTAÇÃO DE CONVERSAS & TELEMETRIA
# ==============================================================================

@login_required
@require_GET
def exportar_sessao_markdown(request: HttpRequest, sessao_id: uuid.UUID) -> HttpResponse:
    """Exporta a transcrição completa da sessão em arquivo Markdown estruturado para download.

    Args:
        request: Requisição HTTP do operador autenticado.
        sessao_id: UUID da sessão a exportar.

    Returns:
        HttpResponse: Arquivo com attachment para download direto ou 404/403.
    """
    sessao = obter_sessao_por_id(sessao_id=sessao_id, usuario=request.user)
    if not sessao:
        return HttpResponse("Sessão não encontrada ou não autorizada.", status=404)

    try:
        conteudo_md = gerar_markdown_conversa(sessao=sessao, usuario=request.user)
        slug_titulo = slugify(sessao.titulo)[:30] or "conversa"
        data_str = timezone.now().strftime("%Y%m%d_%H%M")
        nome_arquivo = f"conversa_{slug_titulo}_{data_str}.md"

        response = HttpResponse(conteudo_md, content_type="text/markdown; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
        return response
    except SessaoNaoEncontradaError:
        return HttpResponse("Acesso não autorizado para exportar esta conversa.", status=403)


@login_required
@require_GET
def dashboard_telemetria(request: HttpRequest) -> HttpResponse:
    """Renderiza o dashboard de telemetria de tokens, métricas e custos de IA do operador.

    Args:
        request: Requisição HTTP autenticada.

    Returns:
        HttpResponse: Página HTML com dados agregados de telemetria.
    """
    metricas = obter_metricas_telemetria_usuario(usuario=request.user)
    perfil = obter_ou_criar_perfil_usuario(usuario=request.user)

    context: dict[str, Any] = {
        "metricas": metricas,
        "perfil": perfil,
    }
    return render(request, "app_chatbot/dashboard.html", context)
