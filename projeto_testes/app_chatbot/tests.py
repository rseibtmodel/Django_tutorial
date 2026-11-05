"""Suíte de testes automatizados do aplicativo Chatbot.

Cobre autenticação, isolamento multi-tenant (IDOR), controle de acessos,
camada de seletores, serviços, RAG de documentos e criação/gestão de personas e perfis.
"""

from typing import Any
from unittest.mock import MagicMock, patch
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import StreamingHttpResponse
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .exceptions import (
    DocumentoInvalidoError,
    PerfilInvalidoError,
    PersonaInvalidaError,
    SessaoNaoEncontradaError,
    TituloInvalidoError,
)
from .models import DocumentoSessao, MensagemChat, PerfilUsuario, Persona, SessaoChat
from .selectors import (
    listar_documentos_sessao,
    listar_mensagens_sessao,
    listar_personas_disponiveis,
    listar_sessoes_usuario,
    obter_documento_por_id,
    obter_metricas_telemetria_usuario,
    obter_ou_criar_perfil_usuario,
    obter_perfil_usuario,
    obter_persona_padrao,
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
    compilar_system_prompt_persona,
    criar_persona_customizada,
    criar_sessao_para_usuario,
    deletar_persona_customizada,
    excluir_sessao_e_vetores,
    extrair_texto_de_arquivo,
    fatiar_texto_em_chunks,
    garantir_persona_padrao,
    gerar_markdown_conversa,
    processar_e_indexar_documento,
    renomear_sessao_usuario,
    sanitizar_e_validar_titulo,
    validar_arquivo_imagem,
)
from .tools import (
    avaliar_expressao_matematica_segura,
    executar_calculo_matematico,
    obter_data_e_hora_oficial,
    obter_ferramentas_para_sessao,
)

class ChatbotAuthESessoesTestCase(TestCase):
    """Testes de autenticação, controle de acesso e isolamento multi-tenant de sessões."""

    def setUp(self) -> None:
        self.client: Client = Client()

        # Cria dois usuários distintos para testar o isolamento de sessões
        self.usuario_a: User = User.objects.create_user(
            username="rodrigo",
            password="senha_segura_123",
            email="rodrigo@teste.com",
        )
        self.usuario_b: User = User.objects.create_user(
            username="lucas",
            password="outra_senha_456",
            email="lucas@teste.com",
        )

        self.persona_padrao: Persona = garantir_persona_padrao()

        # Sessão do Usuário A
        self.sessao_a: SessaoChat = SessaoChat.objects.create(
            usuario=self.usuario_a,
            titulo="Conversa do Rodrigo",
            persona=self.persona_padrao,
            acessado_em=timezone.now(),
        )
        # Sessão do Usuário B
        self.sessao_b: SessaoChat = SessaoChat.objects.create(
            usuario=self.usuario_b,
            titulo="Conversa Privada do Lucas",
            persona=self.persona_padrao,
            acessado_em=timezone.now(),
        )

    def test_acesso_anonimo_redireciona_para_login(self) -> None:
        """Garante que usuários não autenticados sejam redirecionados para o login."""
        url = reverse("app_chatbot:painel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        url_redirecionamento: str = getattr(response, "url", "")
        self.assertIn(reverse("app_chatbot:login"), url_redirecionamento)

    def test_login_com_sucesso(self) -> None:
        """Valida autenticação com credenciais corretas."""
        url = reverse("app_chatbot:login")
        response = self.client.post(url, {
            "username": "rodrigo",
            "password": "senha_segura_123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("app_chatbot:painel"))

    def test_login_com_credenciais_invalidas(self) -> None:
        """Garante exibição de erro ao errar a senha."""
        url = reverse("app_chatbot:login")
        response = self.client.post(url, {
            "username": "rodrigo",
            "password": "senha_errada",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Credenciais inválidas")

    def test_usuario_a_nao_enxerga_sessao_do_usuario_b(self) -> None:
        """Garante que o Usuário A só veja suas próprias conversas na lista lateral."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:painel")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conversa do Rodrigo")
        self.assertNotContains(response, "Conversa Privada do Lucas")

    def test_trava_idor_usuario_a_nao_pode_acessar_sessao_do_usuario_b(self) -> None:
        """Garante que tentar acessar diretamente o ID da sessão de outro usuário resulte em 404."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = f"{reverse('app_chatbot:painel')}?sessao_id={self.sessao_b.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_criar_nova_sessao_vincula_ao_usuario_logado(self) -> None:
        """Valida que o endpoint de criação de sessão amarra a nova conversa ao usuário logado."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:criar_sessao")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SessaoChat.objects.filter(usuario=self.usuario_a).count(), 2)

    def test_excluir_sessao_propria_via_post_com_sucesso(self) -> None:
        """Valida exclusão segura de conversa pelo próprio dono via requisição POST."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:deletar_sessao", kwargs={"sessao_id": self.sessao_a.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(SessaoChat.objects.filter(id=self.sessao_a.id).exists())

    def test_tentativa_de_deletar_sessao_via_get_retorna_405(self) -> None:
        """Garante que deleção via GET seja terminantemente proibida com HTTP 405 Method Not Allowed."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:deletar_sessao", kwargs={"sessao_id": self.sessao_a.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(SessaoChat.objects.filter(id=self.sessao_a.id).exists())

    def test_tentativa_de_excluir_sessao_alheia_retorna_404(self) -> None:
        """Garante que um usuário não possa excluir a conversa de outro via IDOR."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:deletar_sessao", kwargs={"sessao_id": self.sessao_b.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(SessaoChat.objects.filter(id=self.sessao_b.id).exists())

    def test_chat_stream_autenticado_processa_comando_status(self) -> None:
        """Valida streaming de mensagem com usuário autenticado e gravação no SQLite."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:chat_stream")
        payload = {
            "sessao_id": str(self.sessao_a.id),
            "mensagem": "/status",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)

        assert isinstance(response, StreamingHttpResponse)
        streaming_content: Any = getattr(response, "streaming_content")
        conteudo = b"".join(streaming_content).decode("utf-8")
        self.assertIn("Status do Sistema", conteudo)
        self.assertEqual(MensagemChat.objects.filter(sessao=self.sessao_a).count(), 2)

    def test_login_abre_ultima_sessao_acessada(self) -> None:
        """Garante que ao entrar no painel sem ID, a sessão com acesso mais recente seja aberta."""
        self.client.login(username="rodrigo", password="senha_segura_123")

        sessao_recente = SessaoChat.objects.create(
            usuario=self.usuario_a,
            titulo="Conversa Recente Acessada",
            persona=self.persona_padrao,
            acessado_em=timezone.now(),
        )

        url = reverse("app_chatbot:painel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        context = getattr(response, "context", {})
        self.assertIsNotNone(context)
        sessao_contexto = context["sessao"]
        self.assertEqual(sessao_contexto.id, sessao_recente.id)

    def test_renomear_sessao_com_sucesso(self) -> None:
        """Valida que o usuário pode alterar o nome da sessão via endpoint assíncrono."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:renomear_sessao", kwargs={"sessao_id": self.sessao_a.id})

        response = self.client.post(url, {"titulo": "Caso Clínico Dr. Carlos"})
        self.assertEqual(response.status_code, 200)
        dados = getattr(response, "json")()
        self.assertEqual(dados.get("status"), "sucesso")
        self.assertEqual(dados.get("titulo"), "Caso Clínico Dr. Carlos")

        self.sessao_a.refresh_from_db()
        self.assertEqual(self.sessao_a.titulo, "Caso Clínico Dr. Carlos")

    def test_rejeicao_codigo_malicioso_no_titulo(self) -> None:
        """Garante que tentativas de injeção XSS/HTML sejam barradas com erro 400."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:renomear_sessao", kwargs={"sessao_id": self.sessao_a.id})

        payloads_maliciosos = [
            "<script>alert('hack')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:void(0)",
            "<iframe src='evil.com'></iframe>",
            "onload=malicious()",
        ]

        for payload in payloads_maliciosos:
            response = self.client.post(url, {"titulo": payload})
            self.assertEqual(response.status_code, 400)
            dados = getattr(response, "json")()
            self.assertIn("código ou tags HTML", dados.get("erro", ""))

        self.sessao_a.refresh_from_db()
        self.assertEqual(self.sessao_a.titulo, "Conversa do Rodrigo")

    def test_rejeicao_titulo_excedendo_limite_de_caracteres(self) -> None:
        """Garante que títulos com mais de 80 caracteres sejam rejeitados."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:renomear_sessao", kwargs={"sessao_id": self.sessao_a.id})

        titulo_gigante = "A" * 85
        response = self.client.post(url, {"titulo": titulo_gigante})
        self.assertEqual(response.status_code, 400)
        dados = getattr(response, "json")()
        self.assertIn("não pode exceder 80 caracteres", dados.get("erro", ""))

    def test_tentativa_de_renomear_sessao_alheia_retorna_404(self) -> None:
        """Garante trava IDOR: usuário não pode renomear conversa de outro."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:renomear_sessao", kwargs={"sessao_id": self.sessao_b.id})

        response = self.client.post(url, {"titulo": "Hackeando Titulo"})
        self.assertEqual(response.status_code, 404)

    def test_camada_selectors(self) -> None:
        """Testa o isolamento e as funções da camada selectors.py."""
        sessoes = listar_sessoes_usuario(usuario=self.usuario_a)
        self.assertEqual(sessoes.count(), 1)
        primeira_sessao = sessoes.first()
        self.assertIsNotNone(primeira_sessao)
        assert primeira_sessao is not None
        self.assertEqual(primeira_sessao.id, self.sessao_a.id)

        sessao_encontrada = obter_sessao_por_id(sessao_id=self.sessao_a.id, usuario=self.usuario_a)
        self.assertIsNotNone(sessao_encontrada)

        sessao_outro = obter_sessao_por_id(sessao_id=self.sessao_a.id, usuario=self.usuario_b)
        self.assertIsNone(sessao_outro)

        ultima = obter_ultima_sessao_acessada(usuario=self.usuario_a)
        self.assertIsNotNone(ultima)
        assert ultima is not None
        self.assertEqual(ultima.id, self.sessao_a.id)

    def test_sanitizar_titulo_excecoes_de_dominio(self) -> None:
        """Testa se sanitizar_e_validar_titulo levanta TituloInvalidoError corretamente."""
        with self.assertRaises(TituloInvalidoError):
            sanitizar_e_validar_titulo("")

        with self.assertRaises(TituloInvalidoError):
            sanitizar_e_validar_titulo("<script>alert(1)</script>")

        with self.assertRaises(TituloInvalidoError):
            sanitizar_e_validar_titulo("A" * 85, max_chars=80)

        titulo_ok = sanitizar_e_validar_titulo("   Consulta Médica   ")
        self.assertEqual(titulo_ok, "Consulta Médica")

    def test_falha_na_inferencia_do_gemini_nao_grava_erro_como_modelo_no_banco(self) -> None:
        """Garante que se a API externa de IA falhar, o stack trace não seja gravado como mensagem do modelo."""
        service = ChatOrchestratorService(sessao=self.sessao_a)
        service.api_key = "dummy_key_para_forcar_fluxo"

        with patch.object(service, "_obter_cliente_genai") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content_stream.side_effect = RuntimeError("API Gemini Indisponível")
            mock_get_client.return_value = mock_client

            generator = service.executar_chat_stream(texto_usuario="Pergunta qualquer")
            chunks = list(generator)

            self.assertTrue(any("Erro temporário" in c for c in chunks))

            mensagens_model = MensagemChat.objects.filter(sessao=self.sessao_a, papel="model")
            self.assertEqual(mensagens_model.count(), 0)

            mensagens_user = MensagemChat.objects.filter(sessao=self.sessao_a, papel="user")
            self.assertEqual(mensagens_user.count(), 1)

    # ==========================================================================
    # TESTES DE RAG DE DOCUMENTOS
    # ==========================================================================

    @patch("google.genai.Client")
    def test_upload_documento_com_sucesso(self, mock_genai_client_class: MagicMock) -> None:
        """Valida envio e persistência de documento para RAG na sessão."""
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.embeddings = [MagicMock(values=[0.1] * 3072)]
        mock_client.models.embed_content.return_value = mock_resp
        mock_genai_client_class.return_value = mock_client

        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:upload_documento", kwargs={"sessao_id": self.sessao_a.id})

        arquivo_conteudo = b"Este e um documento de teste com instrucoes arquiteturais para o chatbot."
        arquivo_mock = SimpleUploadedFile("manual_arquitetura.txt", arquivo_conteudo, content_type="text/plain")

        response = self.client.post(url, {"documento": arquivo_mock})
        self.assertEqual(response.status_code, 302)

        docs = listar_documentos_sessao(sessao=self.sessao_a)
        self.assertEqual(docs.count(), 1)
        doc = docs.first()
        self.assertIsNotNone(doc)
        assert doc is not None
        self.assertEqual(doc.nome_original, "manual_arquitetura.txt")
        self.assertTrue(doc.total_chunks > 0)

    def test_deletar_documento_com_sucesso(self) -> None:
        """Valida remoção segura de documento da sessão."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        doc = DocumentoSessao.objects.create(
            sessao=self.sessao_a,
            nome_original="arquivo_para_deletar.txt",
            tamanho_bytes=100,
            total_chunks=1,
        )

        url = reverse(
            "app_chatbot:deletar_documento",
            kwargs={"sessao_id": self.sessao_a.id, "doc_id": doc.id}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertFalse(DocumentoSessao.objects.filter(id=doc.id).exists())

    def test_slash_command_docs_lista_documentos_da_sessao(self) -> None:
        """Garante que o comando /docs liste os arquivos anexados no chat."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        DocumentoSessao.objects.create(
            sessao=self.sessao_a,
            nome_original="especificacao_tecnica.md",
            tamanho_bytes=2048,
            total_chunks=3,
        )

        url = reverse("app_chatbot:chat_stream")
        payload = {
            "sessao_id": str(self.sessao_a.id),
            "mensagem": "/docs",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)

        assert isinstance(response, StreamingHttpResponse)
        streaming_content: Any = getattr(response, "streaming_content")
        conteudo = b"".join(streaming_content).decode("utf-8")
        self.assertIn("especificacao_tecnica.md", conteudo)

    def test_chunking_de_texto(self) -> None:
        """Testa o utilitário de fatiamento de texto com overlap."""
        texto_longo = "Parágrafo de teste sobre engenharia de software. " * 30
        chunks = fatiar_texto_em_chunks(texto_longo, tamanho_chunk=200, overlap=50)
        self.assertTrue(len(chunks) > 1)
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 200)

    # ==========================================================================
    # NOVOS TESTES: PERSONAS CUSTOMIZÁVEIS & PERFIL DO USUÁRIO
    # ==========================================================================

    def test_compilar_system_prompt_persona_completo(self) -> None:
        """Valida que o compilador de prompt agrega demografia, tom, história e perfil do usuário."""
        persona = Persona.objects.create(
            nome="Dra. Helena Rocha",
            slug="dra-helena",
            profissao_cargo="Pesquisadora em Bioética",
            tom_de_voz="academico",
            idade=45,
            sexo="feminino",
            escolaridade="doutorado",
            historia_background="Formada pela USP com 15 anos de atuação hospitalar.",
            diretrizes_comportamento="Sempre questione o viés estatístico dos algoritmos.",
        )
        perfil = PerfilUsuario.objects.create(
            usuario=self.usuario_a,
            nome_exibicao="Rodrigo Model",
            profissao="Engenheiro de Software",
        )

        prompt_compilado = compilar_system_prompt_persona(persona=persona, perfil_usuario=perfil)

        self.assertIn("Dra. Helena Rocha", prompt_compilado)
        self.assertIn("Pesquisadora em Bioética", prompt_compilado)
        self.assertIn("45 anos", prompt_compilado)
        self.assertIn("Doutorado", prompt_compilado)
        self.assertIn("Formada pela USP", prompt_compilado)
        self.assertIn("Rodrigo Model", prompt_compilado)
        self.assertIn("Engenheiro de Software", prompt_compilado)

    def test_criar_e_atualizar_persona_customizada(self) -> None:
        """Testa o ciclo de vida completo de uma persona customizada criada pelo usuário."""
        persona = criar_persona_customizada(
            usuario=self.usuario_a,
            nome="Mentor Hacker",
            descricao_curta="Especialista em segurança ofensiva.",
            tom_de_voz="tecnico_rigoroso",
            profissao_cargo="Pen Tester",
            diretrizes_comportamento="Aponte falhas de segurança sem rodeios.",
        )
        self.assertEqual(persona.nome, "Mentor Hacker")
        self.assertFalse(persona.is_sistema)
        self.assertEqual(persona.usuario, self.usuario_a)

        # Atualiza a persona
        persona_atualizada = atualizar_persona_customizada(
            persona=persona,
            usuario=self.usuario_a,
            nome="Mentor Hacker Sênior",
            tom_de_voz="descontraido",
        )
        self.assertEqual(persona_atualizada.nome, "Mentor Hacker Sênior")
        self.assertEqual(persona_atualizada.tom_de_voz, "descontraido")

    def test_tentativa_de_editar_persona_do_sistema_lanca_excecao(self) -> None:
        """Garante que personas protegidas do sistema não possam ser modificadas."""
        with self.assertRaises(PersonaInvalidaError):
            atualizar_persona_customizada(
                persona=self.persona_padrao,
                usuario=self.usuario_a,
                nome="Tentando Hackear Sistema",
            )

    def test_tentativa_de_editar_persona_alheia_lanca_excecao(self) -> None:
        """Garante trava IDOR na edição de personas entre usuários distintos."""
        persona_do_b = criar_persona_customizada(
            usuario=self.usuario_b,
            nome="Persona do Lucas",
        )
        with self.assertRaises(PersonaInvalidaError):
            atualizar_persona_customizada(
                persona=persona_do_b,
                usuario=self.usuario_a,
                nome="Invadindo Persona",
            )

    def test_atualizar_perfil_usuario(self) -> None:
        """Valida persistência e atualização dos dados cadastrais do perfil do operador."""
        perfil = atualizar_perfil_usuario(
            usuario=self.usuario_a,
            nome_exibicao="Rodrigo S. Model",
            profissao="Arquiteto de IA",
            bio="Pesquisador apaixonado por sistemas multiagentes e Django.",
        )
        self.assertEqual(perfil.nome_exibicao, "Rodrigo S. Model")
        self.assertEqual(perfil.profissao, "Arquiteto de IA")
        self.assertIn("multiagentes", perfil.bio)

    def test_gerenciar_personas_view_renderiza_com_sucesso(self) -> None:
        """Garante que a tela central /personas/ responda com HTTP 200 para usuário autenticado."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:gerenciar_personas")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GERENCIADOR DE PERSONAS")
        self.assertContains(response, "MINHAS PERSONAS")

    def test_salvar_persona_via_endpoint(self) -> None:
        """Valida criação de nova persona via POST no endpoint /personas/salvar/."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:salvar_persona")

        response = self.client.post(url, {
            "nome": "Professor Pardal",
            "descricao_curta": "Inventor maluco e criativo",
            "tom_de_voz": "descontraido",
            "idade": "60",
            "profissao_cargo": "Inventor Chefe",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Persona.objects.filter(nome="Professor Pardal", usuario=self.usuario_a).exists())

    def test_deletar_persona_customizada_via_endpoint(self) -> None:
        """Garante exclusão segura de persona customizada própria."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        persona = criar_persona_customizada(
            usuario=self.usuario_a,
            nome="Persona Temporaria",
        )
        url = reverse("app_chatbot:deletar_persona", kwargs={"persona_id": persona.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Persona.objects.filter(id=persona.id).exists())

    def test_alterar_persona_na_sessao_via_endpoint(self) -> None:
        """Testa alteração de persona da sessão via endpoint /sessao/<id>/persona/."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        coder_persona = Persona.objects.filter(slug="coder", is_sistema=True).first()
        self.assertIsNotNone(coder_persona)
        assert coder_persona is not None

        url = reverse("app_chatbot:alterar_persona", kwargs={"sessao_id": self.sessao_a.id})
        response = self.client.post(url, {"persona": str(coder_persona.id)})
        self.assertEqual(response.status_code, 200)

        dados = getattr(response, "json")()
        self.assertEqual(dados.get("status"), "sucesso")
        self.sessao_a.refresh_from_db()
        self.assertEqual(self.sessao_a.persona, coder_persona)

    def test_slash_command_persona_altera_para_persona_do_banco(self) -> None:
        """Valida que o comando /persona coder altera dinamicamente a sessão."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:chat_stream")
        payload = {
            "sessao_id": str(self.sessao_a.id),
            "mensagem": "/persona coder",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)

        assert isinstance(response, StreamingHttpResponse)
        streaming_content: Any = getattr(response, "streaming_content")
        conteudo = b"".join(streaming_content).decode("utf-8")
        self.assertIn("Persona alterada com sucesso", conteudo)

        self.sessao_a.refresh_from_db()
        persona_ativa = self.sessao_a.persona
        self.assertIsNotNone(persona_ativa)
        assert persona_ativa is not None
        self.assertEqual(persona_ativa.slug, "coder")

    def test_validar_arquivo_imagem_valida_e_invalida(self) -> None:
        """Testa validação defensiva de tamanho e extensão em upload de imagens."""
        # Arquivo válido PNG
        arquivo_valido = SimpleUploadedFile("avatar.png", b"fake_png_data", content_type="image/png")
        validar_arquivo_imagem(arquivo_valido)

        # Arquivo com extensão inválida
        arquivo_invalido_ext = SimpleUploadedFile("script.py", b"print('hack')", content_type="text/x-python")
        with self.assertRaises(PersonaInvalidaError):
            validar_arquivo_imagem(arquivo_invalido_ext)

        # Arquivo que excede 2MB
        conteudo_pesado = b"X" * (2 * 1024 * 1024 + 10)
        arquivo_pesado = SimpleUploadedFile("grande.jpg", conteudo_pesado, content_type="image/jpeg")
        with self.assertRaises(PersonaInvalidaError):
            validar_arquivo_imagem(arquivo_pesado)

    def test_slug_persona_protegido_contra_shadowing(self) -> None:
        """Garante que personas customizadas com nomes reservados recebam prefixo user-."""
        persona_coder = criar_persona_customizada(
            usuario=self.usuario_a,
            nome="Coder",
        )
        self.assertTrue(persona_coder.slug.startswith("user-coder-"))

        persona_padrao = criar_persona_customizada(
            usuario=self.usuario_a,
            nome="Padrao",
        )
        self.assertTrue(persona_padrao.slug.startswith("user-padrao-"))

    def test_atualizar_perfil_com_data_invalida_lanca_excecao(self) -> None:
        """Valida que parsing de data de nascimento lance PerfilInvalidoError em formato incorreto."""
        with self.assertRaises(PerfilInvalidoError):
            atualizar_perfil_usuario(
                usuario=self.usuario_a,
                data_nascimento="15/05/1990",
            )

        # Formato correto deve atualizar normalmente
        perfil = atualizar_perfil_usuario(
            usuario=self.usuario_a,
            data_nascimento="1990-05-15",
        )
        self.assertEqual(str(perfil.data_nascimento), "1990-05-15")

    def test_salvar_persona_view_com_erro_dispara_mensagem_error(self) -> None:
        """Garante que submissão inválida de persona no endpoint registre mensagem de erro."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:salvar_persona")

        response = self.client.post(url, {"nome": "A"}, follow=True)
        self.assertEqual(response.status_code, 200)

        wsgi_req = getattr(response, "wsgi_request", None)
        self.assertIsNotNone(wsgi_req)
        assert wsgi_req is not None
        mensagens = list(get_messages(wsgi_req))
        self.assertTrue(any("Erro ao salvar persona" in str(m) for m in mensagens))

    @patch("google.genai.Client")
    def test_processar_e_indexar_documento_rag_com_batching(self, mock_client_cls: MagicMock) -> None:
        """Valida processamento em lote (batching) com fallback defensivo para RAG."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_resp_batch = MagicMock()
        mock_resp_batch.embeddings = [
            MagicMock(values=[0.1] * 3072),
        ]
        mock_client.models.embed_content.return_value = mock_resp_batch

        documento = DocumentoSessao.objects.create(
            sessao=self.sessao_a,
            arquivo="docs_chat/teste.txt",
            nome_original="teste.txt",
            tamanho_bytes=500,
        )

        conteudo = b"Primeiro bloco de texto relevante para indexacao."
        total = processar_e_indexar_documento(
            documento=documento,
            conteudo_bytes=conteudo,
            api_key="fake-test-key",
        )

        self.assertGreater(total, 0)
        self.assertTrue(mock_client.models.embed_content.called)

    def test_gerar_markdown_conversa_e_protecao_idor(self) -> None:
        """Testa geração de markdown estruturado da sessão e bloqueio IDOR."""
        MensagemChat.objects.create(
            sessao=self.sessao_a,
            papel="user",
            conteudo="Qual é a capital da França?",
            tokens_utilizados=10,
        )
        MensagemChat.objects.create(
            sessao=self.sessao_a,
            papel="model",
            conteudo="A capital da França é Paris.",
            tokens_utilizados=25,
        )

        markdown_text = gerar_markdown_conversa(sessao=self.sessao_a, usuario=self.usuario_a)
        self.assertIn("# Transcrição de Conversa", markdown_text)
        self.assertIn("Qual é a capital da França?", markdown_text)
        self.assertIn("A capital da França é Paris.", markdown_text)
        self.assertIn("35 tokens", markdown_text)

        with self.assertRaises(SessaoNaoEncontradaError):
            gerar_markdown_conversa(sessao=self.sessao_a, usuario=self.usuario_b)

    def test_exportar_sessao_markdown_view_com_sucesso_e_idor(self) -> None:
        """Valida endpoint de download de Markdown com Content-Disposition e isolamento."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url_propria = reverse("app_chatbot:exportar_sessao_markdown", kwargs={"sessao_id": self.sessao_a.id})
        response = self.client.get(url_propria)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/markdown; charset=utf-8")
        self.assertIn("attachment; filename=", response["Content-Disposition"])

        url_alheia = reverse("app_chatbot:exportar_sessao_markdown", kwargs={"sessao_id": self.sessao_b.id})
        resp_alheia = self.client.get(url_alheia)
        self.assertEqual(resp_alheia.status_code, 404)

    def test_obter_metricas_telemetria_usuario(self) -> None:
        """Valida cálculo de agregações de tokens, custos e personas no seletor de telemetria."""
        MensagemChat.objects.create(
            sessao=self.sessao_a,
            papel="model",
            conteudo="Resposta de teste",
            tokens_utilizados=1000,
        )

        metricas = obter_metricas_telemetria_usuario(usuario=self.usuario_a)
        self.assertGreaterEqual(metricas["total_tokens"], 1000)
        self.assertGreaterEqual(metricas["total_mensagens"], 1)
        self.assertGreaterEqual(metricas["total_sessoes"], 1)
        self.assertGreater(metricas["custo_estimado_usd"], 0.0)
        self.assertIsInstance(metricas["consumo_por_persona"], list)
        self.assertIsInstance(metricas["ultimas_sessoes"], list)

    def test_dashboard_telemetria_view_autenticado_e_anonimo(self) -> None:
        """Testa acesso à página de telemetria para usuário logado e redirecionamento de anônimo."""
        url = reverse("app_chatbot:dashboard")

        resp_anonimo = self.client.get(url)
        self.assertEqual(resp_anonimo.status_code, 302)

        self.client.login(username="rodrigo", password="senha_segura_123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DASHBOARD DE TELEMETRIA")
        self.assertContains(response, "Tokens Registrados")

    @patch("app_chatbot.services.VectorStoreManager")
    def test_excluir_sessao_e_vetores_servico_e_idor(self, mock_vsm_cls: MagicMock) -> None:
        """Valida que o serviço exclui arquivos em disco, expurga vetores do ChromaDB e barra IDOR."""
        mock_vsm = MagicMock()
        mock_collection = MagicMock()
        mock_vsm.collection = mock_collection
        mock_vsm_cls.return_value = mock_vsm

        sessao_temp = SessaoChat.objects.create(
            usuario=self.usuario_a,
            titulo="Conversa para Exclusao",
            persona=self.persona_padrao,
        )
        doc_temp = DocumentoSessao.objects.create(
            sessao=sessao_temp,
            nome_original="arquivo.txt",
            tamanho_bytes=100,
        )

        # Usuário B não pode deletar sessão do Usuário A
        with self.assertRaises(SessaoNaoEncontradaError):
            excluir_sessao_e_vetores(sessao=sessao_temp, usuario=self.usuario_b)

        # Usuário A exclui com sucesso
        excluir_sessao_e_vetores(sessao=sessao_temp, usuario=self.usuario_a)
        self.assertFalse(SessaoChat.objects.filter(id=sessao_temp.id).exists())
        self.assertFalse(DocumentoSessao.objects.filter(id=doc_temp.id).exists())
        self.assertTrue(mock_collection.delete.called)

    @patch("google.genai.Client")
    def test_anexar_documento_sessao_servico_sucesso_e_validacoes(self, mock_client_cls: MagicMock) -> None:
        """Valida serviço de ingestão defensiva de documentos, limites e rollback duplo."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.embeddings = [MagicMock(values=[0.1] * 3072)]
        mock_client.models.embed_content.return_value = mock_resp

        # Arquivo > 5MB deve ser rejeitado
        arquivo_pesado = SimpleUploadedFile("pesado.pdf", b"X" * (5 * 1024 * 1024 + 100), content_type="application/pdf")
        with self.assertRaises(DocumentoInvalidoError):
            anexar_documento_sessao(sessao=self.sessao_a, arquivo_upload=arquivo_pesado, max_mb=5)

        # Extensão inválida deve ser rejeitada
        arquivo_invalido = SimpleUploadedFile("script.exe", b"binario", content_type="application/octet-stream")
        with self.assertRaises(DocumentoInvalidoError):
            anexar_documento_sessao(sessao=self.sessao_a, arquivo_upload=arquivo_invalido)

        # Arquivo válido deve persistir com sucesso
        arquivo_valido = SimpleUploadedFile("roteiro.txt", b"Texto relevante para a sessao", content_type="text/plain")
        doc_criado = anexar_documento_sessao(sessao=self.sessao_a, arquivo_upload=arquivo_valido, max_mb=5)
        self.assertEqual(doc_criado.nome_original, "roteiro.txt")
        self.assertTrue(doc_criado.total_chunks > 0)

    def test_deletar_persona_customizada_reatribui_sessao_para_padrao(self) -> None:
        """Garante que a exclusão da persona reatribua atômica e automaticamente as sessões para a persona padrão."""
        persona_custom = criar_persona_customizada(
            usuario=self.usuario_a,
            nome="Instrutor Rust",
        )
        self.sessao_a.persona = persona_custom
        self.sessao_a.save(update_fields=["persona"])

        # Tentar apagar persona do sistema deve falhar
        with self.assertRaises(PersonaInvalidaError):
            deletar_persona_customizada(persona=self.persona_padrao, usuario=self.usuario_a)

        # Deletar persona customizada própria
        nome_deletada = deletar_persona_customizada(persona=persona_custom, usuario=self.usuario_a)
        self.assertEqual(nome_deletada, "Instrutor Rust")
        self.assertFalse(Persona.objects.filter(id=persona_custom.id).exists())

        # Sessão deve ter sido reatribuída para a persona padrão do sistema
        self.sessao_a.refresh_from_db()
        self.assertEqual(self.sessao_a.persona, self.persona_padrao)

    def test_upload_documento_view_com_mensagens_sucesso_e_erro(self) -> None:
        """Valida que o endpoint de upload emita mensagens de sucesso e erro via messages framework."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:upload_documento", kwargs={"sessao_id": self.sessao_a.id})

        # Tentativa de envio com arquivo acima do limite
        arquivo_pesado = SimpleUploadedFile("grande.pdf", b"X" * (5 * 1024 * 1024 + 10), content_type="application/pdf")
        resp_erro = self.client.post(url, {"documento": arquivo_pesado}, follow=True)
        self.assertEqual(resp_erro.status_code, 200)

        wsgi_req = getattr(resp_erro, "wsgi_request", None)
        assert wsgi_req is not None
        msgs_erro = [str(m) for m in get_messages(wsgi_req)]
        self.assertTrue(any("Erro na ingestão do documento" in m for m in msgs_erro))

    # ==========================================================================
    # TESTES DE HARDENING DAS AÇÕES ACT-005 A ACT-009
    # ==========================================================================

    def test_seletor_persona_padrao_e_garantir_persona_servico_cqrs(self) -> None:
        """ACT-005: Valida que seletor é consulta pura (CQRS) e serviço centraliza criação."""
        Persona.objects.all().delete()
        # Seletor não cria se tabela estiver vazia
        self.assertIsNone(obter_persona_padrao())
        self.assertEqual(Persona.objects.count(), 0)

        # Serviço garante/cria defensivamente
        padrao = garantir_persona_padrao()
        self.assertIsNotNone(padrao)
        self.assertEqual(padrao.slug, "padrao")
        self.assertEqual(Persona.objects.count(), 1)

        # Seletor agora recupera sem mutação
        recuperada = obter_persona_padrao()
        self.assertIsNotNone(recuperada)
        assert recuperada is not None
        self.assertEqual(recuperada.id, padrao.id)

    def test_painel_chat_metodo_get_preserva_acessado_em(self) -> None:
        """ACT-006: Valida que requisição passiva GET no painel não altera acessado_em da sessão."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        timestamp_antigo = timezone.now() - timezone.timedelta(days=1)
        SessaoChat.objects.filter(id=self.sessao_a.id).update(acessado_em=timestamp_antigo)
        self.sessao_a.refresh_from_db()

        url = f"{reverse('app_chatbot:painel')}?sessao_id={self.sessao_a.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.sessao_a.refresh_from_db()
        self.assertEqual(self.sessao_a.acessado_em, timestamp_antigo)

    def test_indices_estruturais_sessao_e_mensagem(self) -> None:
        """ACT-007: Valida presença dos índices de performance em SessaoChat e MensagemChat."""
        campo_acessado = SessaoChat._meta.get_field("acessado_em")
        self.assertTrue(getattr(campo_acessado, "db_index", False))

        nomes_indices = [idx.name for idx in MensagemChat._meta.indexes]
        self.assertIn("idx_msg_sessao_criado", nomes_indices)

    def test_enforcement_decorators_http_405_em_views(self) -> None:
        """ACT-008: Valida bloqueio com 405 Method Not Allowed ao usar verbo HTTP incorreto."""
        self.client.login(username="rodrigo", password="senha_segura_123")

        # GET em endpoint que exige POST
        url_stream = reverse("app_chatbot:chat_stream")
        resp_get_stream = self.client.get(url_stream)
        self.assertEqual(resp_get_stream.status_code, 405)

        # POST em endpoints que exigem GET
        url_painel = reverse("app_chatbot:painel")
        resp_post_painel = self.client.post(url_painel)
        self.assertEqual(resp_post_painel.status_code, 405)

        url_msgs = reverse("app_chatbot:listar_mensagens", kwargs={"sessao_id": self.sessao_a.id})
        resp_post_msgs = self.client.post(url_msgs)
        self.assertEqual(resp_post_msgs.status_code, 405)

        url_telemetria = reverse("app_chatbot:dashboard")
        resp_post_telemetria = self.client.post(url_telemetria)
        self.assertEqual(resp_post_telemetria.status_code, 405)

    @patch("threading.Thread")
    def test_streaming_indexacao_memoria_despachada_em_background(self, mock_thread_class: MagicMock) -> None:
        """ACT-009: Valida que a indexação de memória seja despachada como thread daemon em background."""
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        service = ChatOrchestratorService(sessao=self.sessao_a)
        service.api_key = "dummy_key_mock"

        with patch.object(service, "_obter_cliente_genai") as mock_get_client:
            mock_client = MagicMock()
            mock_chunk = MagicMock()
            mock_chunk.text = "Resposta do modelo."
            mock_chunk.usage_metadata = MagicMock(total_token_count=15)
            mock_client.models.generate_content_stream.return_value = [mock_chunk]
            mock_get_client.return_value = mock_client

            with patch.object(service, "_recuperar_contexto_semantico", return_value=""):
                chunks = list(service.executar_chat_stream("Pergunta do teste"))

            self.assertEqual(chunks, ["Resposta do modelo."])
            mock_thread_class.assert_called_once()
            _, kwargs = mock_thread_class.call_args
            self.assertTrue(kwargs.get("daemon"))
            mock_thread_instance.start.assert_called_once()

    # ==========================================================================
    # TESTES DE AGENTES MULTI-STEP COM TOOL CALLING (FASE 4)
    # ==========================================================================

    def test_avaliar_expressao_matematica_segura_sucesso(self) -> None:
        """Valida avaliação precisa de operações aritméticas via AST segura."""
        self.assertEqual(avaliar_expressao_matematica_segura("2 + 2"), "4")
        self.assertEqual(avaliar_expressao_matematica_segura("(10 + 5) * 2"), "30")
        self.assertEqual(avaliar_expressao_matematica_segura("100 / 4"), "25")
        self.assertEqual(avaliar_expressao_matematica_segura("2 ** 3"), "8")
        self.assertEqual(avaliar_expressao_matematica_segura("17 % 5"), "2")
        self.assertEqual(avaliar_expressao_matematica_segura("15 // 2"), "7")
        self.assertEqual(avaliar_expressao_matematica_segura("-(5 * 4)"), "-20")

        # Divisão por zero deve retornar mensagem explicativa sem crash
        self.assertIn("Divisão por zero", avaliar_expressao_matematica_segura("10 / 0"))

    def test_avaliar_expressao_matematica_segura_bloqueio_ataques_rce(self) -> None:
        """Valida que tentativas de injeção de código ou chamadas a funções sejam bloqueadas."""
        # Tentativas de chamadas de função
        res_rce = avaliar_expressao_matematica_segura("__import__('os').system('ls')")
        self.assertIn("bloqueada por segurança", res_rce.lower())

        res_open = avaliar_expressao_matematica_segura("open('/etc/passwd')")
        self.assertIn("bloqueada por segurança", res_open.lower())

        # Tentativa de acesso a variáveis
        res_var = avaliar_expressao_matematica_segura("x + 1")
        self.assertIn("bloqueada por segurança", res_var.lower())

        # Expressão vazia
        self.assertIn("vazia", avaliar_expressao_matematica_segura("   "))

    def test_obter_data_e_hora_oficial(self) -> None:
        """Valida retorno estruturado da ferramenta de data e hora oficial."""
        resultado = obter_data_e_hora_oficial()
        self.assertIn("Data e hora oficial:", resultado)
        self.assertIn("America/Sao_Paulo", resultado)
        self.assertIn("ISO:", resultado)

    def test_ferramentas_sessao_catalogo_e_execucao(self) -> None:
        """Valida a geração do catálogo de ferramentas com escopo seguro da sessão."""
        # Anexa um documento de teste à sessão
        DocumentoSessao.objects.create(
            sessao=self.sessao_a,
            nome_original="politica_seguranca.pdf",
            tamanho_bytes=10240,
            total_chunks=5,
        )

        ferramentas = obter_ferramentas_para_sessao(sessao=self.sessao_a)
        self.assertEqual(len(ferramentas), 7)

        nomes_ferramentas = [f.__name__ for f in ferramentas]
        self.assertIn("obter_data_e_hora_oficial", nomes_ferramentas)
        self.assertIn("executar_calculo_matematico", nomes_ferramentas)
        self.assertIn("consultar_documentos_sessao", nomes_ferramentas)
        self.assertIn("obter_informacoes_sessao", nomes_ferramentas)
        self.assertIn("consultar_telemetria_operador", nomes_ferramentas)
        self.assertIn("registrar_transacao_financeira", nomes_ferramentas)
        self.assertIn("consultar_extrato_financeiro", nomes_ferramentas)

        # Executa ferramentas de sessão diretamente e valida retornos
        f_map = {f.__name__: f for f in ferramentas}

        res_docs = f_map["consultar_documentos_sessao"]()
        self.assertIn("politica_seguranca.pdf", res_docs)
        self.assertIn("5 chunks", res_docs)

        res_info = f_map["obter_informacoes_sessao"]()
        self.assertIn(str(self.sessao_a.id)[:8], res_info)
        self.assertIn(self.sessao_a.titulo, res_info)

        res_telem = f_map["consultar_telemetria_operador"]()
        self.assertIn(self.usuario_a.username, res_telem)

    def test_slash_command_tools_retorna_lista_formatada(self) -> None:
        """Valida que o comando /tools exiba a lista de ferramentas ativas de Function Calling."""
        self.client.login(username="rodrigo", password="senha_segura_123")
        url = reverse("app_chatbot:chat_stream")
        payload = {
            "sessao_id": str(self.sessao_a.id),
            "mensagem": "/tools",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)

        assert isinstance(response, StreamingHttpResponse)
        streaming_content: Any = getattr(response, "streaming_content")
        conteudo = b"".join(streaming_content).decode("utf-8")
        self.assertIn("Ferramentas Ativas no Sistema", conteudo)
        self.assertIn("executar_calculo_matematico", conteudo)
        self.assertIn("obter_data_e_hora_oficial", conteudo)
