# Relatório de Auditoria: Otimizações de Performance, Integridade CQRS e Boas Práticas

- **ID do Review:** REV-0003
- **Data da Auditoria:** 2026-11-02
- **Auditor:** Agente 1 (Tech Lead Sênior de Python & Django)
- **Módulo:** `app_chatbot`
- **Arquivos Auditados:**
  - [`selectors.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/selectors.py)
  - [`views.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py)
  - [`models.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/models.py)
  - [`services.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/services.py)
- **Status:** `RESOLVIDO`

---

## 1. Parecer Técnico Geral do Tech Lead

> *"Depois que limpamos os vazamentos de vetores e o lixo de storage, o sistema começou a se comportar como gente grande. Mas se queremos nos orgulhar de seguir o Clean Code e o Two Scoops of Django, ainda temos manchas que não passam pelo crivo de um Tech Lead. Encontrei mutação de banco de dados disfarçada dentro de seletor de leitura pura (violando CQRS), requisições GET disparando UPDATE silencioso a cada F5 no painel, queries sem índices compostos que vão ranger quando o histórico crescer, views aceitando qualquer verbo HTTP por falta de decorators nativos e embedding síncrono mantendo o socket HTTP aberto desnecessariamente. Abaixo está o relatório cirúrgico. Cada ponto foi encaminhado ao Guardião da Documentação para estruturar as propostas de ação com o Arquiteto e o UX Designer."*

---

## 2. Apontamentos Cirúrgicos & Vínculo com Propostas de Ação

### 1. `[ALERTA]` Violação de CQRS com Efeitos Colaterais em Camada de Leitura (`selectors.py`)
- **Código Original ([selectors.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/selectors.py#L181-L200)):**
```python
def obter_persona_padrao() -> Persona:
    padrao = Persona.objects.filter(slug="padrao", is_sistema=True).first()
    if not padrao:
        padrao = Persona.objects.filter(is_sistema=True).first()
    if not padrao:
        # Fallback de emergência se a tabela estiver vazia
        padrao = Persona.objects.create(
            nome="Assistente Geral",
            slug="padrao",
            is_sistema=True,
            descricao_curta="Assistente inteligente padrão.",
            diretrizes_comportamento="Responda com clareza e precisão em português do Brasil.",
        )
    return padrao
```
- **Diagnóstico & Crítica:**
  A camada `selectors.py` possui uma única responsabilidade inegociável: consultas de leitura (`QuerySets` e leituras puras). Inserir `Persona.objects.create()` dentro de um seletor viola frontalmente o princípio de CQRS (Command Query Responsibility Segregation). Seletor não é seed de banco nem serviço de criação. Além disso, `obter_ou_criar_perfil_usuario` também executa mutação silenciosa na mesma camada.
- **Impacto:** Consultas de leitura deixam de ser idempotentes, geram efeitos colaterais ocultos em testes e mascaram a ausência de migrations formais de dados.
- **Ação Vinculada:** 🔗 [ACT-005: Expurgo de Mutações na Camada de Seletores e Migração de Dados de Personas](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-005_expurgo_mutacao_seletor_persona_padrao.md)

---

### 2. `[ALERTA]` Operações de Escrita em Requisições GET e Queries Redundantes no Painel (`views.py`)
- **Código Original ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py#L101-L124)):**
```python
    sessoes = listar_sessoes_usuario(usuario=request.user)
    ...
    if not sessao:
        sessao = criar_sessao_para_usuario(usuario=request.user)
        sessoes = listar_sessoes_usuario(usuario=request.user)
    ...
    # Atualiza o timestamp de último acesso
    SessaoChat.objects.filter(id=sessao.id).update(acessado_em=timezone.now())
```
- **Diagnóstico & Crítica:**
  A view principal do chat executa `listar_sessoes_usuario` no início, depois chama `update(acessado_em=timezone.now())` logo em seguida durante um simples método `GET`. Além de transformar um `GET` idempotente em um comando de escrita no banco a cada refresh do operador, a lista de sessões passada para o template pode carregar dados desatualizados em relação ao timestamp recém-alterado.
- **Impacto:** I/O desnecessário de escrita no SQLite a cada navegação passiva; quebra de convenções HTTP sobre métodos seguros (`GET` não deve mutar estado do recurso).
- **Ação Vinculada:** 🔗 [ACT-006: Otimização do Painel de Chat e Eliminação de Escritas Desnecessárias em GET](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-006_otimizacao_painel_reaproveitamento_sessoes.md)

---

### 3. `[RECOMENDAÇÃO]` Ausência de Índices Estruturais para Ordenações e Filtros de Alta Frequência (`models.py`)
- **Código Original ([models.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/models.py#L205-L241)):**
```python
class SessaoChat(models.Model):
    ...
    acessado_em = models.DateTimeField(default=timezone.now, verbose_name="Último Acesso")
    class Meta:
        ordering = ['-acessado_em']

class MensagemChat(models.Model):
    sessao = models.ForeignKey(SessaoChat, on_delete=models.CASCADE, related_name="mensagens")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    class Meta:
        ordering = ['criado_em']
```
- **Diagnóstico & Crítica:**
  `SessaoChat.acessado_em` é o critério primário de ordenação da aplicação (`-acessado_em`), mas não possui `db_index=True`. Da mesma forma, `MensagemChat` é filtrada por `sessao` e ordenada por `criado_em` em absolutamente todas as trocas de mensagens e renders de tela. Conforme a tabela atinge dezenas de milhares de turnos de diálogo, a ausência de um índice composto `(sessao, criado_em)` forçará *full table scans* e *file-sorts* desnecessários.
- **Impacto:** Degradação de latência conforme o volume de mensagens e sessões aumenta.
- **Ação Vinculada:** 🔗 [ACT-007: Criação de Índices Estruturais e Compostos para Sessões e Mensagens](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-007_indices_banco_dados_alta_frequencia.md)

---

### 4. `[RECOMENDAÇÃO]` Falta de Decorators Estritos de Método HTTP nas Views (`views.py`)
- **Código Original ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py)):**
```python
@login_required
def listar_mensagens(request: HttpRequest, sessao_id: uuid.UUID) -> JsonResponse:
    ...

@login_required
def chat_stream(request: HttpRequest) -> StreamingHttpResponse:
    if request.method != "POST":
        return StreamingHttpResponse("Método não permitido. Use POST.", status=405)
```
- **Diagnóstico & Crítica:**
  Em `views.py`, views de consulta como `painel_chat`, `listar_mensagens`, `gerenciar_personas`, `exportar_sessao_markdown` e `dashboard_telemetria` não possuem `@require_GET`. Na view `chat_stream`, a restrição de método foi implementada manualmente via `if request.method != "POST":` com retorno de `StreamingHttpResponse` em vez de utilizar o decorator nativo padrão do Django `@require_POST` que responde com `HttpResponseNotAllowed (405)`.
- **Impacto:** Código não idiomático, endpoints aceitando verbos indesejados (ex: POST em endpoint de leitura pura) e ausência de headers HTTP `Allow` padronizados.
- **Ação Vinculada:** 🔗 [ACT-008: Padronização de Decorators Nativos de Verbos HTTP nas Views](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-008_padronizacao_decorators_http_views.md)

---

### 5. `[RECOMENDAÇÃO]` Bloqueio Síncrono de Indexação Vetorial no Encerramento do Streaming (`services.py`)
- **Código Original ([services.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/services.py#L1266-L1277)):**
```python
    texto_final: str = "".join(resposta_completa)
    if texto_final.strip():
        MensagemChat.objects.create(...)
        try:
            self._indexar_memoria(texto_usuario, texto_final)
        except Exception as e_mem:
            logger.warning("Falha defensiva ao indexar memória vetorial: %s", e_mem)
```
- **Diagnóstico & Crítica:**
  A indexação de memória vetorial (`_indexar_memoria`) envolve gerar embeddings via chamada de rede com o Gemini e inserir vetores no ChromaDB. Essa operação roda no final do loop do gerador `executar_chat_stream`, **antes** do gerador ser finalizado. Como consequência, o cliente HTTP permanece com o socket aberto aguardando a finalização do stream, mesmo já tendo recebido todo o texto na interface.
- **Impacto:** O tempo de conexão percebido pelo cliente se estende por mais 500ms a 1500ms desnecessariamente; a thread WSGI fica retida até a indexação de background terminar.
- **Ação Vinculada:** 🔗 [ACT-009: Desacoplamento da Indexação Vetorial Pós-Streaming](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action_done/ACT-009_embedding_assincrono_pos_streaming.md)

---

## 3. Checklist de Auditoria & Resolução

- [x] **Ação ACT-005:** Purgar mutações em `selectors.py` e garantir seed via data migration ou service específico.
- [x] **Ação ACT-006:** Otimizar `painel_chat` eliminando atualização de timestamp e re-queries em requisições GET passivas.
- [x] **Ação ACT-007:** Adicionar `db_index=True` em `SessaoChat.acessado_em` e índice composto `Index(fields=['sessao', 'criado_em'])` em `MensagemChat`.
- [x] **Ação ACT-008:** Aplicar decorators `@require_GET` e `@require_POST` canônicos em todas as views de `views.py`.
- [x] **Ação ACT-009:** Isolar o pós-processamento de memória vetorial para não bloquear a finalização do streaming HTTP.

