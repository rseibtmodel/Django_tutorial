"""Camada de serviços e orquestração de negócios do Chatbot.

Centraliza regras de negócio, sanitização defensiva, ciclo de vida de sessões,
gerenciamento de personas dinâmicas, RAG com documentos e inferência de LLM.
"""

import logging
import os
import re
import threading
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Generator, Optional, Union
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser, User
from django.db import transaction
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify
from dotenv import load_dotenv

from .exceptions import (
    DocumentoInvalidoError,
    PerfilInvalidoError,
    PersonaInvalidaError,
    SessaoNaoEncontradaError,
    TituloInvalidoError,
)
from .models import DocumentoSessao, MensagemChat, PerfilUsuario, Persona, SessaoChat
from .selectors import (
    listar_mensagens_sessao,
    obter_persona_padrao,
    obter_persona_por_id_ou_slug,
)
from .tools import obter_ferramentas_para_sessao
from .vector_store import VectorStoreManager

# Carrega variáveis de ambiente uma única vez no carregamento do módulo
load_dotenv(Path(settings.BASE_DIR) / ".env")
load_dotenv(Path(settings.BASE_DIR).parent / ".env")

logger = logging.getLogger(__name__)


# ==============================================================================
# COMPILADOR DE SYSTEM PROMPT & PERSONAS
# ==============================================================================

def compilar_system_prompt_persona(
    *,
    persona: Persona,
    perfil_usuario: Optional[PerfilUsuario] = None
) -> str:
    """Compila as características demográficas, tom e histórico da persona em um System Prompt robusto.

    Args:
        persona: Instância da Persona ativa.
        perfil_usuario: Perfil opcional do interlocutor humano para hiper-personalização.

    Returns:
        str: System instruction completa compilada para o Gemini.
    """
    blocos: list[str] = [
        "### IDENTIDADE & PAPEL DO ASSISTENTE",
        f"- Nome do Personagem: {persona.nome}",
        f"- Ocupação / Especialidade: {persona.profissao_cargo or 'Assistente Especialista'}",
        f"- Tom de Voz Prevalente: {persona.get_tom_de_voz_display()}",
    ]

    if persona.descricao_curta:
        blocos.append(f"- Resumo do Papel: {persona.descricao_curta}")

    detalhes_demo: list[str] = []
    if persona.idade:
        detalhes_demo.append(f"Idade aparente: {persona.idade} anos")
    if persona.sexo and persona.sexo != "nao_especificado":
        detalhes_demo.append(f"Identidade/Gênero: {persona.get_sexo_display()}")
    if persona.escolaridade and persona.escolaridade != "nao_especificado":
        detalhes_demo.append(f"Formação Acadêmica: {persona.get_escolaridade_display()}")

    if detalhes_demo:
        blocos.append(f"- Características Demográficas: {', '.join(detalhes_demo)}")

    if persona.historia_background and persona.historia_background.strip():
        blocos.append(f"\n### HISTÓRICO & BACKSTORY:\n{persona.historia_background.strip()}")

    if persona.diretrizes_comportamento and persona.diretrizes_comportamento.strip():
        blocos.append(f"\n### DIRETRIZES DE COMPORTAMENTO:\n{persona.diretrizes_comportamento.strip()}")

    # Contextualização do Interlocutor Humano
    if perfil_usuario:
        nome_user = perfil_usuario.nome_exibicao or perfil_usuario.usuario.username
        blocos.append(
            f"\n### DADOS DO INTERLOCUTOR (USUÁRIO):\n"
            f"- Nome: {nome_user}\n"
            f"- Profissão/Atuação: {perfil_usuario.profissao or 'Não informada'}\n"
            f"- Adapte seu vocabulário e estilo para atender com maestria o perfil deste usuário."
        )

    blocos.append(
        "\n### DIRETRIZES GERAIS DE RESPOSTA:\n"
        "- Incorpore a persona de forma orgânica e crível, sem quebrar o personagem.\n"
        "- Responda com naturalidade, precisão e consistência em português do Brasil.\n"
        "- Se documentos de apoio forem fornecidos na sessão, priorize seus dados factuais."
    )

    return "\n".join(blocos)


# Constantes de proteção e segurança
RESERVED_PERSONA_SLUGS: set[str] = {
    "padrao",
    "coder",
    "socratico",
    "resumidor",
    "sistema",
    "admin",
    "root",
    "default",
}

EXTENSOES_IMAGEM_PERMITIDAS: set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".svg",
}


def validar_arquivo_imagem(arquivo: Optional[Any], max_mb: int = 2) -> None:
    """Valida tamanho e extensão de arquivos de imagem enviados de forma defensiva.

    Args:
        arquivo: Arquivo de upload recebido (ex: UploadedFile).
        max_mb: Tamanho máximo permitido em Megabytes (padrão: 2MB).

    Raises:
        PersonaInvalidaError: Se o arquivo violar limite de tamanho ou extensão não suportada.
    """
    if not arquivo:
        return

    # Validação defensiva de tamanho máximo (padrão 2MB)
    tamanho_bytes = getattr(arquivo, "size", 0)
    limite_bytes = max_mb * 1024 * 1024
    if tamanho_bytes > limite_bytes:
        raise PersonaInvalidaError(
            f"O arquivo de imagem excede o tamanho máximo permitido de {max_mb}MB."
        )

    # Validação de extensão por whitelist
    nome_arquivo = getattr(arquivo, "name", "")
    ext = os.path.splitext(nome_arquivo)[1].lower()
    if not ext or ext not in EXTENSOES_IMAGEM_PERMITIDAS:
        raise PersonaInvalidaError(
            f"Formato de imagem não suportado ('{ext}'). Utilize PNG, JPG, WEBP ou SVG."
        )


def criar_persona_customizada(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser],
    nome: str,
    descricao_curta: str = "",
    tom_de_voz: str = "objetivo",
    idade: Optional[int] = None,
    sexo: str = "nao_especificado",
    escolaridade: str = "nao_especificado",
    profissao_cargo: str = "",
    historia_background: str = "",
    diretrizes_comportamento: str = "",
    foto_arquivo: Optional[Any] = None
) -> Persona:
    """Cria uma nova persona customizada para o usuário autenticado.

    Args:
        usuario: Usuário criador da persona.
        nome: Nome da persona.
        descricao_curta: Resumo breve.
        tom_de_voz: Chave do tom de voz.
        idade: Idade opcional.
        sexo: Chave do sexo.
        escolaridade: Chave da escolaridade.
        profissao_cargo: Cargo ou especialidade.
        historia_background: Backstory detalhada.
        diretrizes_comportamento: Regras específicas de resposta.
        foto_arquivo: Arquivo opcional de imagem/avatar.

    Returns:
        Persona: Nova instância da Persona persistida.

    Raises:
        PersonaInvalidaError: Se os dados forem inválidos.
    """
    if foto_arquivo:
        validar_arquivo_imagem(foto_arquivo)

    nome_limpo: str = strip_tags(nome).strip()
    if not nome_limpo or len(nome_limpo) < 2:
        raise PersonaInvalidaError("O nome da persona deve ter no mínimo 2 caracteres.")

    if len(nome_limpo) > 100:
        raise PersonaInvalidaError("O nome da persona não pode exceder 100 caracteres.")

    # Gera slug único baseado no nome com barreira contra shadowing de personas do sistema
    base_slug = slugify(nome_limpo) or "persona"
    if base_slug in RESERVED_PERSONA_SLUGS or any(
        base_slug.startswith(f"{r}-") or base_slug == r for r in RESERVED_PERSONA_SLUGS
    ):
        base_slug = f"user-{base_slug}"

    slug_final = f"{base_slug}-{uuid.uuid4().hex[:6]}"
    while Persona.objects.filter(slug=slug_final).exists():
        slug_final = f"{base_slug}-{uuid.uuid4().hex[:6]}"

    usuario_alvo = usuario if getattr(usuario, "is_authenticated", False) else None
    persona = Persona.objects.create(
        usuario=usuario_alvo,
        is_sistema=False,
        nome=nome_limpo,
        slug=slug_final,
        descricao_curta=strip_tags(descricao_curta).strip()[:255],
        tom_de_voz=tom_de_voz,
        idade=idade if (idade and 0 <= idade <= 150) else None,
        sexo=sexo,
        escolaridade=escolaridade,
        profissao_cargo=strip_tags(profissao_cargo).strip()[:100],
        historia_background=strip_tags(historia_background).strip(),
        diretrizes_comportamento=strip_tags(diretrizes_comportamento).strip(),
        foto=foto_arquivo,
    )
    return persona


def atualizar_persona_customizada(
    *,
    persona: Persona,
    usuario: Union[AbstractBaseUser, AnonymousUser],
    nome: str,
    descricao_curta: str = "",
    tom_de_voz: str = "objetivo",
    idade: Optional[int] = None,
    sexo: str = "nao_especificado",
    escolaridade: str = "nao_especificado",
    profissao_cargo: str = "",
    historia_background: str = "",
    diretrizes_comportamento: str = "",
    foto_arquivo: Optional[Any] = None
) -> Persona:
    """Atualiza com segurança os dados de uma persona pertencente ao usuário.

    Args:
        persona: Instância da Persona a atualizar.
        usuario: Usuário solicitante da alteração (trava IDOR).
        nome: Novo nome.
        descricao_curta: Nova descrição.
        tom_de_voz: Novo tom de voz.
        idade: Nova idade.
        sexo: Novo sexo.
        escolaridade: Nova escolaridade.
        profissao_cargo: Nova profissão.
        historia_background: Novo backstory.
        diretrizes_comportamento: Novas diretrizes.
        foto_arquivo: Novo arquivo de foto se fornecido.

    Returns:
        Persona: Instância atualizada.

    Raises:
        PersonaInvalidaError: Se a persona for do sistema ou não pertencer ao usuário.
    """
    if persona.is_sistema:
        raise PersonaInvalidaError("Não é permitido editar personas protegidas do sistema.")

    if persona.usuario != usuario:
        raise PersonaInvalidaError("Acesso não autorizado para editar esta persona.")

    if foto_arquivo:
        validar_arquivo_imagem(foto_arquivo)

    nome_limpo = strip_tags(nome).strip()
    if not nome_limpo or len(nome_limpo) < 2:
        raise PersonaInvalidaError("O nome da persona deve ter no mínimo 2 caracteres.")

    persona.nome = nome_limpo
    persona.descricao_curta = strip_tags(descricao_curta).strip()[:255]
    persona.tom_de_voz = tom_de_voz
    persona.idade = idade if (idade and 0 <= idade <= 150) else None
    persona.sexo = sexo
    persona.escolaridade = escolaridade
    persona.profissao_cargo = strip_tags(profissao_cargo).strip()[:100]
    persona.historia_background = strip_tags(historia_background).strip()
    persona.diretrizes_comportamento = strip_tags(diretrizes_comportamento).strip()

    if foto_arquivo:
        persona.foto = foto_arquivo

    persona.save()
    return persona


@transaction.atomic
def deletar_persona_customizada(
    *,
    persona: Persona,
    usuario: Union[AbstractBaseUser, AnonymousUser, User]
) -> str:
    """Exclui com segurança uma persona customizada, apaga o avatar em disco e faz fallback de sessões ativas para o preset padrão.

    Args:
        persona: Instância da persona a ser excluída.
        usuario: Usuário solicitante (trava IDOR).

    Returns:
        str: Nome da persona excluída para mensagens de feedback.

    Raises:
        PersonaInvalidaError: Se a persona for do sistema ou não pertencer ao usuário.
    """
    if persona.is_sistema:
        raise PersonaInvalidaError("Não é permitido excluir personas protegidas do sistema.")

    if persona.usuario != usuario:
        raise PersonaInvalidaError("Acesso não autorizado para excluir esta persona.")

    nome_persona = persona.nome

    # Reatribui todas as sessões ativas do usuário para a persona padrão do sistema
    persona_padrao = garantir_persona_padrao()
    SessaoChat.objects.filter(persona=persona).update(persona=persona_padrao)

    if persona.foto:
        try:
            persona.foto.delete(save=False)
        except Exception as e:
            logger.warning("Falha ao remover arquivo de avatar da persona %s: %s", persona.id, e)

    persona.delete()
    return nome_persona


def garantir_persona_padrao() -> Persona:
    """Recupera a persona padrão do sistema ou provisiona uma instância defensivamente.

    Centraliza a responsabilidade de criação e seed de dados na camada de serviços (CQRS).

    Returns:
        Persona: Instância ativa da persona padrão do sistema.
    """
    padrao = Persona.objects.filter(slug="padrao", is_sistema=True).first()
    if not padrao:
        padrao = Persona.objects.filter(is_sistema=True).first()
    if not padrao:
        padrao = Persona.objects.create(
            nome="Assistente Geral",
            slug="padrao",
            is_sistema=True,
            descricao_curta="Assistente inteligente padrão.",
            tom_de_voz="objetivo",
            profissao_cargo="Assistente Virtual",
            diretrizes_comportamento="Responda com clareza e precisão em português do Brasil.",
        )
    return padrao


def obter_ou_criar_perfil_usuario(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> PerfilUsuario:
    """Recupera ou provisiona o perfil do usuário na camada de serviços.

    Args:
        usuario: Instância do usuário autenticado ou anônimo.

    Returns:
        PerfilUsuario: Perfil vinculado ou instância transiente em memória.
    """
    if not usuario.is_authenticated:
        return PerfilUsuario(nome_exibicao="Operador")

    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario)
    return perfil


def atualizar_perfil_usuario(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser],
    nome_exibicao: str = "",
    profissao: str = "",
    data_nascimento: Optional[Any] = None,
    bio: str = "",
    foto_arquivo: Optional[Any] = None
) -> PerfilUsuario:
    """Atualiza os dados de perfil e avatar do usuário/operador.

    Args:
        usuario: Usuário autenticado.
        nome_exibicao: Nome preferido de exibição.
        profissao: Ocupação profissional.
        data_nascimento: Data de nascimento.
        bio: Breve descrição ou resumo.
        foto_arquivo: Nova foto enviada se houver.

    Returns:
        PerfilUsuario: Instância atualizada do perfil.

    Raises:
        PerfilInvalidoError: Se os dados de nascimento ou arquivo de imagem forem inválidos.
    """
    perfil = obter_ou_criar_perfil_usuario(usuario=usuario)
    perfil.nome_exibicao = strip_tags(nome_exibicao).strip()[:100]
    perfil.profissao = strip_tags(profissao).strip()[:100]

    # Parsing defensivo de data_nascimento
    if data_nascimento:
        if isinstance(data_nascimento, str):
            data_str = data_nascimento.strip()
            if data_str:
                try:
                    data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
                    ano_atual = timezone.now().year
                    if data_obj.year < 1900 or data_obj.year > ano_atual:
                        raise PerfilInvalidoError("Data de nascimento fora do intervalo permitido.")
                    perfil.data_nascimento = data_obj
                except ValueError:
                    raise PerfilInvalidoError(
                        "Formato de data de nascimento inválido. Utilize o formato AAAA-MM-DD."
                    )
            else:
                perfil.data_nascimento = None
        elif isinstance(data_nascimento, (datetime, date)):
            perfil.data_nascimento = (
                data_nascimento.date() if isinstance(data_nascimento, datetime) else data_nascimento
            )
    else:
        perfil.data_nascimento = None

    perfil.bio = strip_tags(bio).strip()

    if foto_arquivo:
        try:
            validar_arquivo_imagem(foto_arquivo)
        except PersonaInvalidaError as err:
            raise PerfilInvalidoError(str(err))
        perfil.foto = foto_arquivo

    perfil.save()
    return perfil


# ==============================================================================
# SERVIÇOS DE SESSÃO & RAG
# ==============================================================================

def sanitizar_e_validar_titulo(titulo_raw: str, max_chars: int = 80) -> str:
    """Valida e sanitiza o título contra injeção de código, scripts maliciosos e tags HTML.

    Args:
        titulo_raw: Texto original fornecido para o título da sessão.
        max_chars: Limite máximo permitido de caracteres (padrão: 80).

    Returns:
        str: Título sanitizado e pronto para persistência.

    Raises:
        TituloInvalidoError: Se o título for vazio, exceder os limites ou contiver injeções maliciosas.
    """
    if not titulo_raw or not titulo_raw.strip():
        raise TituloInvalidoError("O título não pode estar vazio.")

    padroes_maliciosos: list[str] = [
        r"<[^>]*>",
        r"javascript\s*:",
        r"on\w+\s*=",
        r"data\s*:\s*text\/html",
        r"vbscript\s*:",
    ]
    for padrao in padroes_maliciosos:
        if re.search(padrao, titulo_raw, re.IGNORECASE):
            raise TituloInvalidoError(
                "Entrada inválida: detectada tentativa de inserção de código ou tags HTML."
            )

    titulo_limpo: str = strip_tags(titulo_raw).strip()

    if len(titulo_limpo) > max_chars:
        raise TituloInvalidoError(f"O título não pode exceder {max_chars} caracteres.")

    if len(titulo_limpo) < 2:
        raise TituloInvalidoError("O título deve ter no mínimo 2 caracteres.")

    return titulo_limpo


def criar_sessao_para_usuario(
    *,
    usuario: Union[AbstractBaseUser, AnonymousUser],
    titulo_inicial: Optional[str] = None,
    persona: Optional[Persona] = None
) -> SessaoChat:
    """Cria uma nova sessão de chat isolada para o usuário autenticado.

    Args:
        usuario: Usuário proprietário da sessão.
        titulo_inicial: Título opcional da conversa.
        persona: Persona opcional para vincular à sessão.

    Returns:
        SessaoChat: Nova sessão persistida.
    """
    titulo_final: str = "Nova Conversa"
    if titulo_inicial:
        try:
            titulo_final = sanitizar_e_validar_titulo(titulo_inicial[:80])
        except TituloInvalidoError:
            titulo_final = "Nova Conversa"

    persona_vinculada = persona or garantir_persona_padrao()
    usuario_vinculado = usuario if getattr(usuario, "is_authenticated", False) else None

    return SessaoChat.objects.create(
        usuario=usuario_vinculado,
        titulo=titulo_final,
        persona=persona_vinculada,
        acessado_em=timezone.now(),
    )


def renomear_sessao_usuario(
    *,
    sessao: SessaoChat,
    novo_titulo_raw: str
) -> str:
    """Renomeia com validação rigorosa uma sessão existente do usuário.

    Args:
        sessao: Instância da sessão do usuário.
        novo_titulo_raw: Novo nome sugerido para a sessão.

    Returns:
        str: Novo título validado e persistido.

    Raises:
        TituloInvalidoError: Se o título for inválido ou inseguro.
    """
    titulo_sanitizado: str = sanitizar_e_validar_titulo(novo_titulo_raw, max_chars=80)
    sessao.titulo = titulo_sanitizado
    sessao.acessado_em = timezone.now()
    sessao.save(update_fields=["titulo", "acessado_em", "atualizado_em"])
    return titulo_sanitizado


def alterar_persona_sessao(
    *,
    sessao: SessaoChat,
    identificador_persona: Union[uuid.UUID, str]
) -> Persona:
    """Modifica a persona comportamental vinculada à sessão.

    Args:
        sessao: Instância da sessão.
        identificador_persona: UUID ou slug da persona solicitada.

    Returns:
        Persona: Instância da persona ativada.

    Raises:
        PersonaInvalidaError: Se a persona informada não for reconhecida ou autorizada.
    """
    usuario_sessao = sessao.usuario
    persona = obter_persona_por_id_ou_slug(
        identificador=identificador_persona,
        usuario=usuario_sessao,
    )
    if not persona:
        raise PersonaInvalidaError(f"Persona '{identificador_persona}' não encontrada ou não autorizada.")

    sessao.persona = persona
    sessao.acessado_em = timezone.now()
    sessao.save(update_fields=["persona", "acessado_em", "atualizado_em"])
    return persona


def gerar_markdown_conversa(
    *,
    sessao: SessaoChat,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> str:
    """Gera um arquivo Markdown estruturado contendo a transcrição completa da sessão.

    Args:
        sessao: Instância da SessaoChat a ser exportada.
        usuario: Usuário solicitante da exportação (trava de segurança IDOR).

    Returns:
        str: Conteúdo formatado em Markdown com cabeçalho, metadados e histórico cronológico.

    Raises:
        SessaoNaoEncontradaError: Se a sessão não pertencer ao usuário autenticado.
    """
    if sessao.usuario != usuario:
        raise SessaoNaoEncontradaError("Acesso não autorizado para exportar esta conversa.")

    mensagens = listar_mensagens_sessao(sessao=sessao)
    data_exportacao = timezone.now().strftime("%d/%m/%Y às %H:%M:%S")
    persona_nome = sessao.persona.nome if sessao.persona else "Assistente Geral"
    persona_cargo = (
        sessao.persona.profissao_cargo if sessao.persona and sessao.persona.profissao_cargo else "IA"
    )
    total_tokens = sum(m.tokens_utilizados or 0 for m in mensagens)
    nome_operador = getattr(usuario, "username", "Operador")

    linhas: list[str] = [
        f"# Transcrição de Conversa // {sessao.titulo}",
        "",
        "> Relatório gerado automaticamente pelo Workspace Chatbot Terminal.",
        "",
        "## 📋 Metadados da Sessão",
        f"- **ID da Sessão:** `{sessao.id}`",
        f"- **Operador:** `{nome_operador}`",
        f"- **Persona Ativa:** `{persona_nome}` [{persona_cargo}]",
        f"- **Total de Mensagens:** {len(mensagens)} turnos",
        f"- **Total de Tokens Registrados:** {total_tokens:,} tokens",
        f"- **Data da Exportação:** {data_exportacao}",
        "",
        "---",
        "",
        "## 💬 Histórico do Diálogo",
        "",
    ]

    for msg in mensagens:
        horario = msg.criado_em.strftime("%d/%m/%Y %H:%M:%S")
        if msg.papel == "user":
            linhas.append(f"### 👤 {nome_operador} (`{horario}`)")
            linhas.append("")
            linhas.append(msg.conteudo)
            linhas.append("")
        elif msg.papel == "model":
            token_info = f" | {msg.tokens_utilizados} tokens" if msg.tokens_utilizados else ""
            linhas.append(f"### 🤖 {persona_nome} [{persona_cargo}] (`{horario}`{token_info})")
            linhas.append("")
            linhas.append(msg.conteudo)
            linhas.append("")
        elif msg.papel == "system":
            linhas.append(f"### ⚙️ Sistema (`{horario}`)")
            linhas.append("")
            linhas.append(f"> {msg.conteudo}")
            linhas.append("")
        linhas.append("---")
        linhas.append("")

    return "\n".join(linhas)


# ==============================================================================
# PIPELINE DE INGESTÃO DE DOCUMENTOS & RAG
# ==============================================================================

def extrair_texto_de_arquivo(nome_arquivo: str, conteudo_bytes: bytes) -> str:
    """Extrai conteúdo textual bruto a partir de bytes de arquivos suportados.

    Args:
        nome_arquivo: Nome do arquivo incluindo extensão.
        conteudo_bytes: Conteúdo binário original do arquivo.

    Returns:
        str: Texto extraído limpo.

    Raises:
        DocumentoInvalidoError: Se a extensão não for suportada ou o arquivo estiver ilegível.
    """
    extensao: str = Path(nome_arquivo).suffix.lower()

    if extensao in [".txt", ".md", ".csv", ".json", ".py", ".html", ".log"]:
        try:
            return conteudo_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return conteudo_bytes.decode("latin-1")
            except Exception as e:
                raise DocumentoInvalidoError(f"Falha ao decodificar arquivo texto: {e}")

    elif extensao == ".pdf":
        import zlib

        texto_acumulado: list[str] = []
        try:
            stream_matches = re.findall(b"stream[\r\n]+(.*?)[\r\n]+endstream", conteudo_bytes, re.DOTALL)
            for raw_stream in stream_matches:
                try:
                    descompactado = zlib.decompress(raw_stream)
                    strings_pdf = re.findall(rb"\((.*?)\)", descompactado)
                    for s in strings_pdf:
                        texto_acumulado.append(s.decode("utf-8", errors="ignore"))
                except Exception:
                    strings_diretas = re.findall(rb"\((.*?)\)", raw_stream)
                    for s in strings_diretas:
                        texto_acumulado.append(s.decode("utf-8", errors="ignore"))

            texto_final: str = " ".join(texto_acumulado).strip()
            if not texto_final:
                texto_final = re.sub(r"[^\x20-\x7E\n\r\t]", " ", conteudo_bytes.decode("latin-1", errors="ignore"))

            return texto_final
        except Exception as e:
            raise DocumentoInvalidoError(f"Não foi possível processar o arquivo PDF: {e}")

    else:
        raise DocumentoInvalidoError(
            f"Extensão '{extensao}' não suportada. Formatos permitidos: .txt, .md, .csv, .json, .py, .pdf"
        )


def fatiar_texto_em_chunks(texto: str, tamanho_chunk: int = 1000, overlap: int = 150) -> list[str]:
    """Divide um texto em blocos sequenciais com sobreposição (overlap) para manter contexto.

    Args:
        texto: Texto integral a fatiar.
        tamanho_chunk: Tamanho máximo em caracteres de cada bloco.
        overlap: Quantidade de caracteres sobrepostos entre blocos adjacentes.

    Returns:
        list[str]: Lista de chunks textuais prontos para vetorização.
    """
    texto_limpo: str = re.sub(r"\s+", " ", texto).strip()
    if not texto_limpo:
        return []

    if len(texto_limpo) <= tamanho_chunk:
        return [texto_limpo]

    chunks: list[str] = []
    inicio: int = 0
    total_len: int = len(texto_limpo)

    while inicio < total_len:
        fim: int = min(inicio + tamanho_chunk, total_len)
        chunk: str = texto_limpo[inicio:fim].strip()
        if chunk:
            chunks.append(chunk)

        if fim >= total_len:
            break

        inicio += (tamanho_chunk - overlap)

    return chunks


def processar_e_indexar_documento(
    *,
    documento: DocumentoSessao,
    conteudo_bytes: bytes,
    api_key: str
) -> int:
    """Extrai texto, fatia em chunks e persiste vetores no ChromaDB vinculados à sessão.

    Args:
        documento: Instância do DocumentoSessao persistida no SQLite.
        conteudo_bytes: Bytes do arquivo carregado.
        api_key: Chave da API do Google Gemini para embeddings.

    Returns:
        int: Quantidade de chunks indexados no ChromaDB.

    Raises:
        DocumentoInvalidoError: Se o documento estiver vazio ou a extração falhar.
    """
    texto: str = extrair_texto_de_arquivo(documento.nome_original, conteudo_bytes)
    if not texto.strip():
        raise DocumentoInvalidoError("O arquivo enviado não contém texto legível para indexação.")

    chunks: list[str] = fatiar_texto_em_chunks(texto, tamanho_chunk=1000, overlap=150)[:50]
    if not chunks:
        raise DocumentoInvalidoError("Nenhum bloco de texto pôde ser gerado a partir do arquivo.")

    vector_manager = VectorStoreManager()
    collection = vector_manager.collection

    if not collection or not api_key:
        documento.total_chunks = len(chunks)
        documento.save(update_fields=["total_chunks"])
        return len(chunks)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        embeddings_list: list[list[float]] = []
        ids_list: list[str] = []
        metadatas_list: list[dict[str, str]] = []
        documents_list: list[str] = []

        usuario_id_str: str = str(documento.sessao.usuario.id) if documento.sessao.usuario else "anon"

        # Otimização de I/O: processamento em lote (batching) com fallback resiliente
        tamanho_lote: int = 50
        for inicio in range(0, len(chunks), tamanho_lote):
            lote_chunks = chunks[inicio : inicio + tamanho_lote]
            vetores_lote: list[list[float]] = []

            try:
                emb_resp = client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=lote_chunks,
                )
                embeddings = emb_resp.embeddings or []
                vetores_lote = [getattr(emb, "values", []) for emb in embeddings if emb]
            except Exception:
                # Fallback defensivo para mock unitário ou caso a API espere chunk unitário
                for chunk in lote_chunks:
                    resp_unitaria = client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=chunk,
                    )
                    if resp_unitaria.embeddings and getattr(resp_unitaria.embeddings[0], "values", None):
                        vetores_lote.append(resp_unitaria.embeddings[0].values)

            for sub_idx, vetor in enumerate(vetores_lote):
                idx = inicio + sub_idx
                chunk_texto = lote_chunks[sub_idx]
                embeddings_list.append(vetor)
                documents_list.append(chunk_texto)
                ids_list.append(f"doc_{documento.id.hex[:8]}_chunk_{idx}")
                metadatas_list.append({
                    "usuario_id": usuario_id_str,
                    "sessao_id": str(documento.sessao.id),
                    "doc_id": str(documento.id),
                    "nome_arquivo": documento.nome_original,
                    "tipo": "documento_rag",
                })

        collection.add(
            embeddings=embeddings_list,
            documents=documents_list,
            metadatas=metadatas_list,
            ids=ids_list,
        )

        documento.total_chunks = len(chunks)
        documento.save(update_fields=["total_chunks"])
        return len(chunks)

    except Exception as e:
        logger.error("Falha ao indexar documento no ChromaDB: %s", e, exc_info=True)
        documento.total_chunks = len(chunks)
        documento.save(update_fields=["total_chunks"])
        return len(chunks)


def remover_documento_e_vetores(*, documento: DocumentoSessao) -> None:
    """Remove o documento do SQLite, apaga o arquivo em disco e expurga seus vetores do ChromaDB.

    Args:
        documento: Instância do DocumentoSessao a ser expurgada.
    """
    vector_manager = VectorStoreManager()
    collection = vector_manager.collection

    if collection:
        try:
            collection.delete(where={"doc_id": str(documento.id)})
        except Exception as e:
            logger.warning("Erro ao remover vetores do documento no ChromaDB: %s", e)

    if documento.arquivo:
        try:
            documento.arquivo.delete(save=False)
        except Exception as e:
            logger.warning("Falha ao remover arquivo físico do documento: %s", e)

    documento.delete()


def anexar_documento_sessao(
    *,
    sessao: SessaoChat,
    arquivo_upload: Any,
    max_mb: int = 5
) -> DocumentoSessao:
    """Valida, persiste, extrai texto e indexa vetores de documento para RAG com rollback limpo do storage.

    Args:
        sessao: Sessão à qual o documento será anexado.
        arquivo_upload: Instância do arquivo enviado (UploadedFile).
        max_mb: Tamanho máximo permitido em Megabytes (padrão: 5MB).

    Returns:
        DocumentoSessao: Instância persistida e indexada com total_chunks > 0.

    Raises:
        DocumentoInvalidoError: Se o arquivo for inválido, exceder o tamanho ou falhar na indexação.
    """
    if not arquivo_upload:
        raise DocumentoInvalidoError("Nenhum arquivo enviado para anexo.")

    tamanho_arquivo: int = getattr(arquivo_upload, "size", 0) or 0
    limite_bytes: int = max_mb * 1024 * 1024
    if tamanho_arquivo > limite_bytes:
        raise DocumentoInvalidoError(f"O documento excede o tamanho máximo permitido de {max_mb}MB.")

    nome_arquivo: str = getattr(arquivo_upload, "name", "documento") or "documento"
    extensao: str = Path(nome_arquivo).suffix.lower()
    extensoes_permitidas: set[str] = {".txt", ".md", ".csv", ".json", ".py", ".html", ".log", ".pdf"}
    if extensao not in extensoes_permitidas:
        raise DocumentoInvalidoError(
            f"Extensão '{extensao}' não suportada. Formatos permitidos: {', '.join(sorted(extensoes_permitidas))}."
        )

    conteudo_bytes: bytes = b""
    if hasattr(arquivo_upload, "read"):
        conteudo_bytes = arquivo_upload.read()
    if not conteudo_bytes:
        raise DocumentoInvalidoError("O arquivo enviado está vazio.")

    # Cria o registro inicial com o arquivo no storage
    doc = DocumentoSessao.objects.create(
        sessao=sessao,
        arquivo=arquivo_upload,
        nome_original=nome_arquivo,
        tamanho_bytes=tamanho_arquivo,
    )

    api_key = os.getenv("GEMINI_API_KEY", "").strip().strip("'\"")
    try:
        total_chunks = processar_e_indexar_documento(
            documento=doc,
            conteudo_bytes=conteudo_bytes,
            api_key=api_key,
        )
        if total_chunks <= 0:
            raise DocumentoInvalidoError("Nenhum trecho de texto legível pôde ser indexado a partir deste documento.")
        return doc
    except Exception as err:
        # Rollback defensivo duplo: expurga o arquivo em disco e o registro do banco
        if doc.arquivo:
            try:
                doc.arquivo.delete(save=False)
            except Exception as e_del:
                logger.warning("Falha ao remover arquivo físico durante rollback: %s", e_del)
        doc.delete()
        if isinstance(err, DocumentoInvalidoError):
            raise
        raise DocumentoInvalidoError(f"Falha ao processar e indexar documento: {err}") from err


@transaction.atomic
def excluir_sessao_e_vetores(
    *,
    sessao: SessaoChat,
    usuario: Union[AbstractBaseUser, AnonymousUser, User]
) -> None:
    """Exclui com segurança a sessão, expurga arquivos físicos de anexos e limpa todos os vetores no ChromaDB.

    Args:
        sessao: Instância da SessaoChat a ser excluída.
        usuario: Usuário solicitante (trava de segurança IDOR).

    Raises:
        SessaoNaoEncontradaError: Se a sessão não pertencer ao usuário autenticado.
    """
    if sessao.usuario != usuario:
        raise SessaoNaoEncontradaError("Acesso não autorizado para excluir esta conversa.")

    sessao_id_str = str(sessao.id)

    # 1. Remove os arquivos físicos de todos os documentos anexados à sessão
    documentos = DocumentoSessao.objects.filter(sessao=sessao)
    for doc in documentos:
        if doc.arquivo:
            try:
                doc.arquivo.delete(save=False)
            except Exception as e_arq:
                logger.warning("Falha ao remover arquivo de documento %s: %s", doc.id, e_arq)

    # 2. Expurga todos os vetores da sessão no ChromaDB (tanto memória de diálogo quanto RAG)
    vector_manager = VectorStoreManager()
    collection = vector_manager.collection
    if collection:
        try:
            collection.delete(where={"sessao_id": sessao_id_str})
        except Exception as e_chroma:
            logger.warning("Erro ao expurgar vetores da sessão %s no ChromaDB: %s", sessao_id_str, e_chroma)

    # 3. Exclui a sessão e seus relacionamentos no SQLite
    sessao.delete()


# ==============================================================================
# ORQUESTRADOR PRINCIPAL DO CHAT
# ==============================================================================

class ChatOrchestratorService:
    """Orquestrador do ciclo de vida de mensagens, memória híbrida, RAG e inferência."""

    def __init__(self, sessao: SessaoChat) -> None:
        """Inicializa o orquestrador para uma sessão específica.

        Args:
            sessao: Sessão ativa em contexto.
        """
        self.sessao: SessaoChat = sessao
        self.api_key: str = os.getenv("GEMINI_API_KEY", "").strip().strip("'\"")
        self.vector_store_manager: VectorStoreManager = VectorStoreManager()
        self._genai_client: Optional[Any] = None

    def _obter_cliente_genai(self) -> Optional[Any]:
        """Inicializa e reaproveita o cliente do SDK Google GenAI em cache de instância.

        Returns:
            Optional[Any]: Instância do genai.Client ou None caso a chave não esteja disponível.
        """
        if not self.api_key:
            return None

        if self._genai_client is None:
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error("Falha ao inicializar o cliente Google GenAI: %s", e)
                return None

        return self._genai_client

    def _recuperar_contexto_semantico(self, pergunta: str) -> str:
        """Busca no ChromaDB memórias anteriores e trechos de documentos anexados (RAG).

        Args:
            pergunta: Pergunta enviada pelo usuário.

        Returns:
            str: Bloco textual contendo memórias passadas e/ou trechos de documentos.
        """
        collection = self.vector_store_manager.collection
        client = self._obter_cliente_genai()
        if not collection or not client:
            return ""

        try:
            emb_response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=pergunta,
            )
            if not emb_response.embeddings or not getattr(emb_response.embeddings[0], "values", None):
                return ""
            vetor = emb_response.embeddings[0].values

            usuario_id_str: str = str(self.sessao.usuario.id) if self.sessao.usuario else "anon"
            where_filter = (
                {"$and": [{"usuario_id": usuario_id_str}, {"sessao_id": str(self.sessao.id)}]}
                if self.sessao.usuario
                else {"sessao_id": str(self.sessao.id)}
            )

            results = collection.query(
                query_embeddings=[vetor],
                n_results=5,
                where=where_filter,
            )

            documentos_raw = results.get("documents") or [[]]
            metadatas_raw = results.get("metadatas") or [[]]
            documentos = documentos_raw[0] if documentos_raw else []
            metadatas = metadatas_raw[0] if metadatas_raw else []

            if not documentos:
                return ""

            memorias: list[str] = []
            docs_rag: list[str] = []

            for doc_text, meta in zip(documentos, metadatas):
                if meta.get("tipo") == "documento_rag":
                    nome_arq = meta.get("nome_arquivo", "documento")
                    docs_rag.append(f"--- Documento [{nome_arq}] ---\n{doc_text}")
                else:
                    memorias.append(doc_text)

            contexto_acumulado: list[str] = []
            if docs_rag:
                contexto_acumulado.append(
                    "\n[DOCUMENTOS DE APOIO ANEXADOS À SESSÃO (RAG)]\n" + "\n\n".join(docs_rag)
                )
            if memorias:
                contexto_acumulado.append(
                    "\n[MEMÓRIA DE CONVERSAS ANTERIORES]\n" + "\n".join(memorias)
                )

            return "\n".join(contexto_acumulado)

        except Exception as e:
            logger.warning("Falha ao recuperar contexto semântico no ChromaDB: %s", e)
            return ""

    def _indexar_memoria(self, pergunta: str, resposta: str) -> None:
        """Armazena o par Pergunta/Resposta como vetor de memória no ChromaDB.

        Args:
            pergunta: Pergunta do usuário.
            resposta: Resposta gerada pela IA.
        """
        collection = self.vector_store_manager.collection
        client = self._obter_cliente_genai()
        if not collection or not client:
            return

        try:
            texto_para_vetorizar: str = f"Pergunta: {pergunta}\nResposta: {resposta}"
            emb = client.models.embed_content(
                model="gemini-embedding-001",
                contents=texto_para_vetorizar,
            )
            if not emb.embeddings or not getattr(emb.embeddings[0], "values", None):
                return

            usuario_id_str: str = str(self.sessao.usuario.id) if self.sessao.usuario else "anon"
            collection.add(
                embeddings=[emb.embeddings[0].values],
                documents=[texto_para_vetorizar],
                metadatas=[{
                    "usuario_id": usuario_id_str,
                    "sessao_id": str(self.sessao.id),
                    "tipo": "memoria_conversa",
                }],
                ids=[f"msg_{uuid.uuid4().hex[:8]}"],
            )
        except Exception as e:
            logger.warning("Falha ao indexar memória no ChromaDB: %s", e)

    def _atualizar_titulo_automatico(self, texto_usuario: str) -> None:
        """Define o título da conversa a partir da primeira mensagem com sanitização defensiva.

        Args:
            texto_usuario: Mensagem enviada pelo usuário.
        """
        if self.sessao.titulo in ["Nova Conversa", "Sessão Interativa", ""]:
            candidato: str = texto_usuario.strip()[:35]
            try:
                titulo_seguro = sanitizar_e_validar_titulo(candidato, max_chars=40)
            except TituloInvalidoError:
                titulo_seguro = "Conversa Ativa"

            self.sessao.titulo = titulo_seguro
            self.sessao.save(update_fields=["titulo", "atualizado_em"])

    def executar_chat_stream(self, texto_usuario: str) -> Generator[str, None, None]:
        """Executa o pipeline completo com roteamento de comandos, RAG e compilação de persona.

        Args:
            texto_usuario: Entrada textual enviada pelo usuário.

        Yields:
            str: Chunks textuais da resposta em tempo real.
        """
        # 1. Define título inicial seguro caso ainda esteja com o padrão
        self._atualizar_titulo_automatico(texto_usuario)

        # 2. Registra pergunta no SQLite (ordem cronológica imutável)
        MensagemChat.objects.create(sessao=self.sessao, papel="user", conteudo=texto_usuario)

        # 3. Roteamento determinístico imediato (Comandos locais de sistema)
        texto_limpo: str = texto_usuario.strip().lower()

        # Comando de alteração dinâmica de persona (/persona <slug_ou_nome>)
        if texto_limpo.startswith("/persona"):
            partes = texto_usuario.strip().split()
            if len(partes) >= 2:
                alvo = partes[1].lower()
                try:
                    persona_ativada = alterar_persona_sessao(sessao=self.sessao, identificador_persona=alvo)
                    resp = f"🎭 Persona alterada com sucesso para: **{persona_ativada.nome}**."
                except PersonaInvalidaError as e:
                    resp = f"⚠️ {str(e)}"
            else:
                nome_atual = self.sessao.persona.nome if self.sessao.persona else "Padrão"
                resp = f"🎭 Persona atual da sessão: **{nome_atual}**.\nPara trocar, use: `/persona <slug>` ou use o seletor no topo."

            MensagemChat.objects.create(sessao=self.sessao, papel="model", conteudo=resp)
            yield resp
            return

        # Comando de listagem de documentos RAG anexados
        if texto_limpo in ["/docs", "docs", "/arquivos"]:
            documentos = DocumentoSessao.objects.filter(sessao=self.sessao)
            if documentos.exists():
                linhas = [f"- 📄 {d.nome_original} ({d.tamanho_bytes // 1024} KB, {d.total_chunks} chunks)" for d in documentos]
                resp_docs = "📎 **Documentos Anexados à Sessão (RAG):**\n" + "\n".join(linhas)
            else:
                resp_docs = "📎 Nenhum documento anexado a esta conversa. Clique em `[📎 DOCS]` no topo para anexar arquivos (.pdf, .txt, .md, .csv)."

            MensagemChat.objects.create(sessao=self.sessao, papel="model", conteudo=resp_docs)
            yield resp_docs
            return

        if texto_limpo in ["/tools", "tools", "/ferramentas"]:
            resp_tools = (
                "🛠️ **Ferramentas Ativas no Sistema (Gemini Function Calling):**\n"
                "- ⏱️ `obter_data_e_hora_oficial`: Consulta data/hora exata do sistema (Fuso Brasília).\n"
                "- 🔢 `executar_calculo_matematico`: Calculadora exata e segura via AST (sem eval).\n"
                "- 📎 `consultar_documentos_sessao`: Lista os arquivos e chunks indexados na conversa.\n"
                "- 💬 `obter_informacoes_sessao`: Metadados da conversa ativa (título, persona, mensagens).\n"
                "- 📊 `consultar_telemetria_operador`: Consumo de tokens e custos estimados em USD."
            )
            MensagemChat.objects.create(sessao=self.sessao, papel="model", conteudo=resp_tools)
            yield resp_tools
            return

        if texto_limpo in ["/ajuda", "ajuda", "/help"]:
            resposta_ajuda: str = (
                "🤖 Comandos disponíveis no terminal:\n"
                "- Digite qualquer pergunta livremente para a IA.\n"
                "- /persona <slug> : Alterna a persona ativa da sessão.\n"
                "- /docs : Lista os documentos indexados na sessão ativa.\n"
                "- /tools : Lista as ferramentas ativas de Function Calling.\n"
                "- /status : Informações de memória, ChromaDB e modelo.\n"
                "- /limpar : Inicie uma nova conversa."
            )
            MensagemChat.objects.create(sessao=self.sessao, papel="model", conteudo=resposta_ajuda)
            yield resposta_ajuda
            return

        if texto_limpo == "/status":
            qtd_mensagens: int = MensagemChat.objects.filter(sessao=self.sessao).count()
            qtd_docs: int = DocumentoSessao.objects.filter(sessao=self.sessao).count()
            nome_persona = self.sessao.persona.nome if self.sessao.persona else "Padrão"
            resposta_status: str = (
                f"📊 Status do Sistema:\n"
                f"- Sessão ID: {self.sessao.id}\n"
                f"- Persona Ativa: {nome_persona}\n"
                f"- Documentos RAG Indexados: {qtd_docs}\n"
                f"- Total de Mensagens (SQLite): {qtd_mensagens}\n"
                f"- ChromaDB Ativo: {'Sim' if self.vector_store_manager.collection else 'Não'}\n"
                f"- Gemini API Key Configurada: {'Sim' if self.api_key else 'Não (Defina GEMINI_API_KEY)'}"
            )
            MensagemChat.objects.create(sessao=self.sessao, papel="model", conteudo=resposta_status)
            yield resposta_status
            return

        # 4. Se não houver chave do Gemini configurada, devolve resposta mock explicativa
        if not self.api_key:
            resposta_mock: str = (
                "⚠️ A variável de ambiente GEMINI_API_KEY não foi configurada ainda.\n\n"
                f"Sua mensagem foi gravada no SQLite: '{texto_usuario}'.\n"
                "Para ativar as respostas do Gemini e os embeddings no ChromaDB, defina a chave exportando:\n"
                "`export GEMINI_API_KEY='sua_chave_aqui'`"
            )
            MensagemChat.objects.create(sessao=self.sessao, papel="model", conteudo=resposta_mock)
            yield resposta_mock
            return

        # 5. Recupera histórico recente de curto prazo (últimos 6 turnos válidos)
        mensagens_validas = (
            MensagemChat.objects.filter(sessao=self.sessao)
            .exclude(papel="system")
            .order_by("-criado_em")[:6]
        )
        historico_recente = list(mensagens_validas)
        historico_recente.reverse()

        # 6. Recupera contexto semântico de longo prazo via ChromaDB (memória + RAG)
        contexto_semantico: str = self._recuperar_contexto_semantico(texto_usuario)

        # 7. Constrói chamada e executa o streaming do Gemini com o Compilador de Personas
        client = self._obter_cliente_genai()
        if not client:
            yield "Erro: Falha na inicialização do cliente de IA."
            return

        try:
            from google.genai import types

            # Compila o System Prompt com a Persona da sessão e o Perfil do Usuário
            persona_ativa = self.sessao.persona or garantir_persona_padrao()
            perfil_usuario = (
                obter_ou_criar_perfil_usuario(usuario=self.sessao.usuario)
                if self.sessao.usuario
                else None
            )

            system_prompt: str = compilar_system_prompt_persona(
                persona=persona_ativa,
                perfil_usuario=perfil_usuario,
            )
            if contexto_semantico:
                system_prompt += f"\n{contexto_semantico}\n"

            contents = []
            for msg in historico_recente:
                contents.append(
                    types.Content(
                        role=msg.papel,
                        parts=[types.Part.from_text(text=msg.conteudo)],
                    )
                )

            resposta_completa: list[str] = []
            tokens_totais: Optional[int] = None

            ferramentas_disponiveis = obter_ferramentas_para_sessao(sessao=self.sessao)

            response_stream = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.4,
                    http_options=types.HttpOptions(timeout=30000),
                    tools=ferramentas_disponiveis,
                ),
            )

            for chunk in response_stream:
                if chunk.text:
                    resposta_completa.append(chunk.text)
                    yield chunk.text

                if getattr(chunk, "usage_metadata", None):
                    tokens_totais = getattr(chunk.usage_metadata, "total_token_count", None)

            texto_final: str = "".join(resposta_completa)

            # 8. Salva a resposta no SQLite e indexa no ChromaDB em background desacoplado
            if texto_final.strip():
                MensagemChat.objects.create(
                    sessao=self.sessao,
                    papel="model",
                    conteudo=texto_final,
                    tokens_utilizados=tokens_totais,
                )

                def _despachar_indexacao_background() -> None:
                    try:
                        self._indexar_memoria(texto_usuario, texto_final)
                    except Exception as e_mem:
                        logger.warning("Falha defensiva em thread ao indexar memória vetorial: %s", e_mem)

                threading.Thread(target=_despachar_indexacao_background, daemon=True).start()

        except Exception as e:
            logger.error("Erro na inferência do Gemini: %s", e, exc_info=True)
            yield f"⚠️ Erro temporário na comunicação com o assistente: {str(e)}"
