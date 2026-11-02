"""Camada de seletores (queries de leitura) do aplicativo de Chatbot.

Encapsula todas as consultas de leitura ao banco de dados com ordenações,
filtros de autorização e otimizações contra o problema N+1.
"""

import uuid
from typing import Any, Optional, Union
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser, User
from django.db.models import Count, Q, QuerySet, Sum
from .models import DocumentoSessao, MensagemChat, PerfilUsuario, Persona, SessaoChat


def listar_sessoes_usuario(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> QuerySet[SessaoChat]:
    """Retorna todas as sessões pertencentes a um usuário ordenadas por último acesso.

    Args:
        usuario: Instância do usuário autenticado.

    Returns:
        QuerySet[SessaoChat]: Queryset com as sessões ordenadas por `-acessado_em`.
    """
    if not usuario.is_authenticated:
        return SessaoChat.objects.none()

    return (
        SessaoChat.objects.filter(usuario=usuario)
        .select_related("persona")
        .order_by("-acessado_em")
    )


def obter_sessao_por_id(
    *,
    sessao_id: Union[uuid.UUID, str],
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> Optional[SessaoChat]:
    """Recupera uma sessão específica garantindo o isolamento IDOR do usuário.

    Args:
        sessao_id: UUID ou string identificadora da sessão.
        usuario: Usuário proprietário da sessão.

    Returns:
        Optional[SessaoChat]: Instância da sessão caso exista e pertença ao usuário, ou None.
    """
    if not usuario.is_authenticated:
        return None

    try:
        return (
            SessaoChat.objects.filter(id=sessao_id, usuario=usuario)
            .select_related("persona")
            .first()
        )
    except (ValueError, TypeError):
        return None


def obter_ultima_sessao_acessada(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> Optional[SessaoChat]:
    """Recupera a sessão mais recentemente acessada pelo usuário para restauração imediata.

    Args:
        usuario: Usuário autenticado.

    Returns:
        Optional[SessaoChat]: Sessão mais recente ou None se o usuário não possuir conversas.
    """
    return listar_sessoes_usuario(usuario=usuario).first()


def listar_mensagens_sessao(*, sessao: SessaoChat) -> QuerySet[MensagemChat]:
    """Retorna as mensagens de uma sessão em ordem cronológica de envio.

    Args:
        sessao: Instância da sessão do chat.

    Returns:
        QuerySet[MensagemChat]: Mensagens ordenadas cronologicamente por `criado_em`.
    """
    return MensagemChat.objects.filter(sessao=sessao).order_by("criado_em")


def listar_documentos_sessao(*, sessao: SessaoChat) -> QuerySet[DocumentoSessao]:
    """Retorna os documentos anexados a uma sessão específica ordenados por criação.

    Args:
        sessao: Instância da sessão do chat.

    Returns:
        QuerySet[DocumentoSessao]: Documentos anexados à sessão.
    """
    return DocumentoSessao.objects.filter(sessao=sessao).order_by("-criado_em")


def obter_documento_por_id(
    *,
    doc_id: Union[uuid.UUID, str],
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> Optional[DocumentoSessao]:
    """Recupera um documento garantindo a trava IDOR de propriedade do usuário.

    Args:
        doc_id: Identificador UUID do documento.
        usuario: Usuário proprietário da sessão pai.

    Returns:
        Optional[DocumentoSessao]: Instância do documento ou None.
    """
    if not usuario.is_authenticated:
        return None

    try:
        return DocumentoSessao.objects.filter(id=doc_id, sessao__usuario=usuario).first()
    except (ValueError, TypeError):
        return None


# ==============================================================================
# SELETORES DE PERSONAS E PERFIL DO USUÁRIO
# ==============================================================================

def listar_personas_disponiveis(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> QuerySet[Persona]:
    """Retorna as personas que o usuário pode utilizar (presets do sistema + customizadas).

    Args:
        usuario: Usuário em contexto.

    Returns:
        QuerySet[Persona]: Personas ativas acessíveis pelo usuário.
    """
    if not usuario.is_authenticated:
        return Persona.objects.filter(is_sistema=True, ativo=True).order_by("-is_sistema", "nome")

    return Persona.objects.filter(
        Q(is_sistema=True) | Q(usuario=usuario),
        ativo=True,
    ).order_by("-is_sistema", "nome")


def obter_persona_por_id_ou_slug(
    *,
    identificador: Union[uuid.UUID, str],
    usuario: Optional[Union[AbstractBaseUser, AnonymousUser]] = None
) -> Optional[Persona]:
    """Busca uma persona por UUID ou por Slug respeitando regras de autorização.

    Args:
        identificador: UUID ou slug da persona.
        usuario: Usuário opcional para checagem de autorização em personas customizadas.

    Returns:
        Optional[Persona]: Instância da persona ou None.
    """
    filtro_acesso = Q(is_sistema=True)
    if usuario and getattr(usuario, "is_authenticated", False):
        filtro_acesso = filtro_acesso | Q(usuario=usuario)

    # Tenta por UUID se parecer um UUID
    try:
        uuid_val = uuid.UUID(str(identificador))
        persona = Persona.objects.filter(id=uuid_val).filter(filtro_acesso).first()
        if persona:
            return persona
    except (ValueError, TypeError):
        pass

    # Tenta por slug
    return Persona.objects.filter(slug=str(identificador)).filter(filtro_acesso).first()


def obter_persona_padrao() -> Optional[Persona]:
    """Retorna a persona padrão do sistema (slug='padrao') ou a primeira ativa.

    Função estritamente de consulta (leitura pura / CQRS) sem criar registros colaterais.

    Returns:
        Optional[Persona]: Persona padrão do sistema caso exista, ou None.
    """
    padrao = Persona.objects.filter(slug="padrao", is_sistema=True).first()
    if not padrao:
        padrao = Persona.objects.filter(is_sistema=True).first()
    return padrao


def obter_perfil_usuario(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> Optional[PerfilUsuario]:
    """Recupera o perfil cadastrado do usuário caso exista.

    Função estritamente de consulta (leitura pura / CQRS) sem mutação no banco.

    Args:
        usuario: Instância do usuário autenticado ou anônimo.

    Returns:
        Optional[PerfilUsuario]: Perfil cadastrado ou None se não existir.
    """
    if not usuario.is_authenticated:
        return None
    return PerfilUsuario.objects.filter(usuario=usuario).first()


def obter_ou_criar_perfil_usuario(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> PerfilUsuario:
    """Função de conveniência delegada para a camada de serviços.

    Args:
        usuario: Instância do usuário autenticado ou anônimo.

    Returns:
        PerfilUsuario: Perfil vinculado ao usuário.
    """
    from .services import obter_ou_criar_perfil_usuario as _svc_obter_ou_criar
    return _svc_obter_ou_criar(usuario=usuario)


def obter_metricas_telemetria_usuario(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> dict[str, Any]:
    """Calcula e consolida as métricas de uso, contagem de tokens e estimativas de custo do operador.

    Args:
        usuario: Instância do usuário autenticado.

    Returns:
        dict[str, Any]: Dicionário contendo total_tokens, total_mensagens, total_sessoes,
            custo_estimado_usd, persona_mais_usada, consumo_por_persona e ultimas_sessoes.
    """
    if not usuario.is_authenticated:
        return {
            "total_tokens": 0,
            "total_mensagens": 0,
            "total_sessoes": 0,
            "custo_estimado_usd": 0.0,
            "persona_mais_usada": "Nenhuma",
            "consumo_por_persona": [],
            "ultimas_sessoes": [],
        }

    mensagens_qs = MensagemChat.objects.filter(sessao__usuario=usuario)
    total_mensagens = mensagens_qs.count()
    agregado_tokens = mensagens_qs.aggregate(total=Sum("tokens_utilizados"))
    total_tokens = agregado_tokens["total"] or 0
    total_sessoes = SessaoChat.objects.filter(usuario=usuario).count()

    # Preço do Gemini 2.5 Flash: média ponderada ~$0.30 por 1 milhão de tokens
    custo_estimado_usd = round((total_tokens / 1_000_000.0) * 0.30, 4)

    # Agregação por persona
    personas_consumo = (
        SessaoChat.objects.filter(usuario=usuario, persona__isnull=False)
        .values("persona__id", "persona__nome", "persona__profissao_cargo")
        .annotate(
            total_sessoes=Count("id", distinct=True),
            total_mensagens=Count("mensagens__id", distinct=True),
            total_tokens=Sum("mensagens__tokens_utilizados"),
        )
        .order_by("-total_tokens")
    )

    lista_personas: list[dict[str, Any]] = []
    persona_mais_usada = "Nenhuma"
    for item in personas_consumo:
        tokens_item = item["total_tokens"] or 0
        lista_personas.append({
            "id": str(item["persona__id"]),
            "nome": item["persona__nome"],
            "cargo": item["persona__profissao_cargo"] or "Geral",
            "sessoes": item["total_sessoes"],
            "mensagens": item["total_mensagens"],
            "tokens": tokens_item,
            "custo_usd": round((tokens_item / 1_000_000.0) * 0.30, 4),
        })
        if persona_mais_usada == "Nenhuma" and item["persona__nome"]:
            persona_mais_usada = item["persona__nome"]

    # Detalhamento das 10 últimas sessões
    ultimas_sessoes_qs = (
        SessaoChat.objects.filter(usuario=usuario)
        .select_related("persona")
        .annotate(
            msg_count=Count("mensagens__id"),
            token_count=Sum("mensagens__tokens_utilizados"),
        )
        .order_by("-acessado_em")[:10]
    )

    lista_sessoes: list[dict[str, Any]] = []
    for s in ultimas_sessoes_qs:
        s_tokens = getattr(s, "token_count", 0) or 0
        lista_sessoes.append({
            "id": str(s.id),
            "titulo": s.titulo,
            "persona_nome": s.persona.nome if s.persona else "Padrão",
            "mensagens": getattr(s, "msg_count", 0) or 0,
            "tokens": s_tokens,
            "custo_usd": round((s_tokens / 1_000_000.0) * 0.30, 4),
            "acessado_em": s.acessado_em,
        })

    return {
        "total_tokens": total_tokens,
        "total_mensagens": total_mensagens,
        "total_sessoes": total_sessoes,
        "custo_estimado_usd": custo_estimado_usd,
        "persona_mais_usada": persona_mais_usada,
        "consumo_por_persona": lista_personas,
        "ultimas_sessoes": lista_sessoes,
    }
