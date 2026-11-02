# Relatório de Auditoria: Revisão Completa de Arquitetura, Camadas e Fluxos

- **ID do Review:** REV-0002
- **Data da Auditoria:** 2026-11-02
- **Auditor:** Agente 1 (Tech Lead Sênior de Python & Django)
- **Módulo:** `app_chatbot`
- **Arquivos Auditados:**
  - [`views.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py)
  - [`services.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/services.py)
  - [`selectors.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/selectors.py)
  - [`models.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/models.py)
  - [`templates/app_chatbot/chat.html`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/templates/app_chatbot/chat.html)
- **Status:** `RESOLVIDO`

---

## 1. Parecer Técnico Geral do Tech Lead

> *"Olha só... o estagiário finalmente parou de brigar com a IDE e os testes estão passando. Maravilha. Mas código que passa em teste unitário ingênuo não significa código à prova de ambiente de produção real. Temos aqui vazamento de arquivos no sistema de arquivos, vetores fantasmas se proliferando eternamente no ChromaDB, views gordas fazendo trabalho sujo de deleção sem passar por services, e um streaming WSGI que sob concorrência vai derrubar o servidor com starvation de threads. Abaixo está o diagnóstico cirúrgico do que precisa ser corrigido antes de batermos o martelo de produção."*

---

## 2. Apontamentos Cirúrgicos & Vínculo com Propostas de Ação

### 1. `[CRÍTICO]` Exclusão de Sessão com Vazamento de Vetores Fantasmas no ChromaDB e Arquivos Órfãos
- **Código Original ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py#L254-L259)):**
```python
@login_required
@require_POST
def deletar_sessao(request: HttpRequest, sessao_id: uuid.UUID) -> HttpResponseRedirect:
    """Exclui com segurança uma sessão pertencente ao usuário autenticado via requisição POST."""
    sessao = get_object_or_404(SessaoChat, id=sessao_id, usuario=request.user)
    sessao.delete()
    return redirect("app_chatbot:painel")
```
- **Diagnóstico & Crítica:**
  Chamar `sessao.delete()` diretamente na View faz o SQLite deletar em cascata as mensagens e os documentos relacionais. Porém, o ChromaDB e o FileSystem são **completamente ignorados**. Os vetores de memória da conversa e os embeddings dos arquivos permanecem órfãos no ChromaDB ad infinitum, além de arquivos binários continuarem ocupando disco em `media/docs_chat/`.
- **Impacto:** Degradação contínua de memória e disco no banco vetorial; violação da LGPD/privacidade (usuário acredita que apagou a sessão, mas suas memórias vetoriais continuam no ChromaDB).
- **Ação Vinculada:** 🔗 [ACT-001: Expurgo de Vetores e Arquivos na Exclusão de Sessão](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-001_expurgo_vetores_e_arquivos_ao_deletar_sessao.md)

---

### 2. `[ALERTA]` Pipeline de Ingestão de Documentos: Acoplamento na View, Falha de Rollback de Binários e Ausência de Feedback Visual
- **Código Original ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py#L215-L232) e [chat.html](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/templates/app_chatbot/chat.html)):**
```python
    doc = DocumentoSessao.objects.create(
        sessao=sessao,
        arquivo=arquivo_enviado,
        nome_original=nome_arquivo,
        tamanho_bytes=tamanho_arquivo,
    )

    api_key = os.getenv("GEMINI_API_KEY", "").strip().strip("'\"")
    try:
        processar_e_indexar_documento(
            documento=doc,
            conteudo_bytes=conteudo_bytes,
            api_key=api_key,
        )
    except DocumentoInvalidoError:
        doc.delete()
```
- **Diagnóstico & Crítica (Visão Unificada Backend + Frontend):**
  O fluxo de upload de documentos para RAG foi implementado de forma fragmentada e desprotegida:
  1. *Backend:* A view acessa `os.getenv` e cria registros antes da validação. Ao falhar, `doc.delete()` **não apaga o arquivo binário salvo em disco**, gerando lixo órfão permanente em `media/docs_chat/`.
  2. *Frontend:* Ao ser rejeitado por extensão ou tamanho (> 5MB), o endpoint redireciona em silêncio absoluto. O template `chat.html` não renderiza `django.contrib.messages`, violando frontalmente as Heurísticas 1 e 9 de Nielsen (o operador não sabe se o arquivo foi indexado ou recusado).
- **Impacto:** Degradação de storage com arquivos corrompidos e péssima experiência de uso (sensação de travamento).
- **Ação Vinculada:** 🔗 [ACT-002: Ingestão Defensiva de Documentos RAG com Rollback de Storage e Feedback Visual no Terminal Dark](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-002_ingestao_documentos_rag_rollback_e_feedback_ux.md)

---

### 3. `[ALERTA]` Exclusão de Persona Direta na View e Risco de Sessões com Persona Nula
- **Código Original ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py#L400-L413)):**
```python
@login_required
@require_POST
def deletar_persona(request: HttpRequest, persona_id: uuid.UUID) -> HttpResponseRedirect:
    try:
        persona = get_object_or_404(Persona, id=persona_id, usuario=request.user, is_sistema=False)
        nome = persona.nome
        if persona.foto:
            persona.foto.delete(save=False)
        persona.delete()
        messages.success(request, f"Persona '{nome}' removida com sucesso.")
    except Exception as erro:
        messages.error(request, f"Erro ao excluir persona: {erro}")

    return redirect("app_chatbot:gerenciar_personas")
```
- **Diagnóstico & Crítica:**
  Ausência de função de domínio na camada de serviços. A deleção direta na view faz com que sessões ativas do usuário passem a ter `persona = None` silenciosamente devido ao `SET_NULL`, quebrando a integridade de contexto do assistente caso o usuário retorne à conversa.
- **Impacto:** Sessões ativas perdem comportamento e diretrizes sem que o usuário entenda o motivo; lógica de negócio orquestrada na camada HTTP.
- **Ação Vinculada:** 🔗 [ACT-003: Serviço de Exclusão de Personas e Tratamento de Sessões Órfãs](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-003_servico_delecao_personas_e_sessao_fallback.md)

---

### 4. `[ALERTA]` Risco de Starvation de Threads WSGI em Streaming Prolongado de LLM
- **Código Original ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py#L301-L306)):**
```python
    service = ChatOrchestratorService(sessao=sessao)

    response = StreamingHttpResponse(
        service.executar_chat_stream(texto_usuario=mensagem_usuario),
        content_type="text/plain; charset=utf-8",
    )
    response["X-Accel-Buffering"] = "no"
    return response
```
- **Diagnóstico & Crítica:**
  Em deployments síncronos WSGI (Gunicorn padrão), cada requisição de streaming de IA segura uma thread por 10 a 30 segundos. Com poucos usuários simultâneos, o pool de workers se esgota e toda a aplicação congela (inclusive telas estáticas de login e dashboard).
- **Impacto:** Gargalo severo de escalabilidade e risco de indisponibilidade em ambiente compartilhado.
- **Ação Vinculada:** 🔗 [ACT-004: Mitigação de Starvation de Threads WSGI em Streaming de IA](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-004_mitigacao_starvation_streaming_wsgi_asgi.md)

---

## 3. Checklist de Auditoria & Resolução

- [x] **Ação ACT-001:** Implementar serviço `excluir_sessao_e_vetores` com expurgo no ChromaDB e remoção de anexos em disco.
- [x] **Ação ACT-002:** Encapsular ingestão de documentos em `anexar_documento_sessao` com rollback rigoroso de storage físico E renderização de mensagens de alerta no `chat.html` com padrão Terminal Dark.
- [x] **Ação ACT-003:** Implementar `deletar_persona_customizada` reatribuindo sessões ativas para o preset padrão do sistema.
- [x] **Ação ACT-004:** Configurar timeouts defensivos no Gemini e documentar roadmap de transição para ASGI.
