"""Modelos de dados do aplicativo de Chatbot."""

import uuid
from typing import TYPE_CHECKING, Any, Optional
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class PerfilUsuario(models.Model):
    """Perfil estendido do usuário/operador para personalização de interações."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="Usuário",
    )
    nome_exibicao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nome de Exibição",
    )
    profissao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Profissão / Ocupação",
    )
    data_nascimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Nascimento",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="Bio / Resumo",
    )
    foto = models.FileField(
        upload_to="perfis/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Foto de Perfil",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"

    def __str__(self) -> str:
        return self.nome_exibicao or getattr(self.usuario, "username", "")


class Persona(models.Model):
    """Entidade que modela o comportamento, história, demografia e tom do assistente."""

    TOM_DE_VOZ_CHOICES = [
        ('objetivo', 'Objetivo & Direto'),
        ('tecnico_rigoroso', 'Técnico Rigoroso (Clean Code)'),
        ('socratico', 'Socrático & Thought Partner'),
        ('academico', 'Acadêmico & Científico'),
        ('descontraido', 'Descontraído & Informal'),
        ('empatico', 'Empático & Acolhedor'),
        ('resumidor', 'Executivo Conciso'),
    ]

    SEXO_CHOICES = [
        ('nao_especificado', 'Não especificado'),
        ('feminino', 'Feminino'),
        ('masculino', 'Masculino'),
        ('nao_binario', 'Não-binário'),
        ('outro', 'Outro'),
    ]

    ESCOLARIDADE_CHOICES = [
        ('nao_especificado', 'Não informada'),
        ('autodidata', 'Autodidata / Prático'),
        ('fundamental', 'Ensino Fundamental'),
        ('medio', 'Ensino Médio'),
        ('superior', 'Graduação Superior'),
        ('pos_graduacao', 'Pós-Graduação / Especialização'),
        ('mestrado', 'Mestrado'),
        ('doutorado', 'Doutorado / Pós-Doc'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="personas_customizadas",
        null=True,
        blank=True,
        verbose_name="Criador (null para preset do sistema)",
    )
    is_sistema = models.BooleanField(
        default=False,
        verbose_name="Preset Global do Sistema",
    )
    nome = models.CharField(max_length=100, verbose_name="Nome da Persona")
    slug = models.SlugField(max_length=100, verbose_name="Slug")
    descricao_curta = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descrição Curta",
    )
    foto = models.FileField(
        upload_to="personas/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Foto / Avatar",
    )
    tom_de_voz = models.CharField(
        max_length=50,
        default="objetivo",
        choices=TOM_DE_VOZ_CHOICES,
        verbose_name="Tom de Voz",
    )
    idade = models.IntegerField(null=True, blank=True, verbose_name="Idade")
    sexo = models.CharField(
        max_length=20,
        default="nao_especificado",
        choices=SEXO_CHOICES,
        verbose_name="Gênero / Identidade",
    )
    escolaridade = models.CharField(
        max_length=50,
        default="nao_especificado",
        choices=ESCOLARIDADE_CHOICES,
        verbose_name="Nível de Escolaridade",
    )
    profissao_cargo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Profissão / Especialidade",
    )
    historia_background = models.TextField(
        blank=True,
        verbose_name="Histórico & Backstory",
    )
    diretrizes_comportamento = models.TextField(
        blank=True,
        verbose_name="Diretrizes Comportamentais (System Prompt)",
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['nome']
        verbose_name = "Persona"
        verbose_name_plural = "Personas"

    def get_tom_de_voz_display(self) -> str:
        """Retorna a descrição textual legível do tom de voz configurado."""
        return dict(self.TOM_DE_VOZ_CHOICES).get(self.tom_de_voz, self.tom_de_voz)

    def get_sexo_display(self) -> str:
        """Retorna a descrição textual legível do sexo/gênero configurado."""
        return dict(self.SEXO_CHOICES).get(self.sexo, self.sexo)

    def get_escolaridade_display(self) -> str:
        """Retorna a descrição textual legível da escolaridade configurada."""
        return dict(self.ESCOLARIDADE_CHOICES).get(self.escolaridade, self.escolaridade)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        tag = "[Sistema]" if self.is_sistema else "[Custom]"
        return f"{self.nome} {tag}"


class SessaoChat(models.Model):
    """Representa uma sessão de conversa contínua com o chatbot."""

    if TYPE_CHECKING:
        mensagens: Any
        documentos: Any

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessoes_chat",
        null=True,
        blank=True,
        verbose_name="Usuário",
    )
    titulo = models.CharField(max_length=120, default="Nova Conversa", verbose_name="Título")
    persona = models.ForeignKey(
        Persona,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessoes",
        verbose_name="Persona Ativa",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    acessado_em = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Último Acesso")

    class Meta:
        ordering = ['-acessado_em']
        verbose_name = "Sessão de Chat"
        verbose_name_plural = "Sessões de Chat"

    def __str__(self) -> str:
        nome_persona = self.persona.nome if self.persona else "Padrão"
        return f"{self.titulo} [{nome_persona}] ({str(self.id)[:8]})"


class MensagemChat(models.Model):
    """Representa um turno de mensagem (pergunta ou resposta) na sessão."""

    PAPEL_CHOICES = [
        ('user', 'Usuário'),
        ('model', 'Assistente (Gemini)'),
        ('system', 'Sistema'),
    ]

    sessao = models.ForeignKey(
        SessaoChat,
        on_delete=models.CASCADE,
        related_name="mensagens",
        verbose_name="Sessão",
    )
    papel = models.CharField(max_length=10, choices=PAPEL_CHOICES, verbose_name="Papel")
    conteudo = models.TextField(verbose_name="Conteúdo da Mensagem")
    tokens_utilizados = models.IntegerField(null=True, blank=True, verbose_name="Tokens")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        ordering = ['criado_em']
        verbose_name = "Mensagem de Chat"
        verbose_name_plural = "Mensagens de Chat"
        indexes = [
            models.Index(fields=['sessao', 'criado_em'], name='idx_msg_sessao_criado'),
        ]

    def __str__(self) -> str:
        return f"[{self.papel}] {self.conteudo[:40]}..."


class DocumentoSessao(models.Model):
    """Armazena arquivos anexados à sessão para consulta RAG no ChromaDB."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sessao = models.ForeignKey(
        SessaoChat,
        on_delete=models.CASCADE,
        related_name="documentos",
        verbose_name="Sessão",
    )
    arquivo = models.FileField(upload_to="docs_chat/%Y/%m/", verbose_name="Arquivo")
    nome_original = models.CharField(max_length=255, verbose_name="Nome Original")
    tamanho_bytes = models.IntegerField(verbose_name="Tamanho (bytes)")
    total_chunks = models.IntegerField(default=0, verbose_name="Total de Chunks")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        ordering = ['-criado_em']
        verbose_name = "Documento de Sessão"
        verbose_name_plural = "Documentos de Sessão"

    def __str__(self) -> str:
        return f"{self.nome_original} ({self.total_chunks} chunks)"
