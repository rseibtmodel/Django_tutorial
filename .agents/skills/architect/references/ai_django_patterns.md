# Padrões de Arquitetura: Django Moderno & Inteligência Artificial

Este guia fornece os fundamentos de design e trade-offs técnicos comuns em aplicações que unem Django, fluxos assíncronos e pipelines de LLM.

---

## 1. Django como Hub de Orquestração de IA

### 1.1 O Mito do Microsserviço Obrigatório
- **O Dilema:** Todo mundo quer criar um serviço isolado em FastAPI para IA achando que o Django é "pesado".
- **A Realidade:** Para MVPs, o Django já entrega autenticação, ORM robusto, migrações seguras, painel administrativo pronto e filas maduras (Celery / Django-Q). Criar microsserviços precoces exige gerenciar autenticação entre serviços, múltiplos deploys, tracing distribuído e schemas duplicados.
- **Padrão Recomendado para MVP:** **Monólito Modular Django**. Mantenha a API e o admin no Django, e execute os pipelines de inferência pesada através de workers assíncronos (Celery) ou views assíncronas dedicadas (`async def`).

### 1.2 Vector Stores: Postgres + pgvector vs. Dedicated Vector DBs
- **Pinecone / Qdrant / Weaviate:**
  - *Prós:* Otimizados para bilhões de vetores, busca aproximada (HNSW) veloz, features de filtragem híbrida nativas.
  - *Contras:* Mais um serviço no cluster, risco de sincronização inconsistente de dados entre o banco relacional e o vector DB, custos elevados.
- **Postgres com `pgvector`:**
  - *Prós:* Tudo dentro do mesmo PostgreSQL onde o Django reside! Transações ACID perfeitas (se deletar o registro no Django, o vetor é deletado via chave estrangeira no mesmo commit). Custo zero de infraestrutura adicional no MVP.
  - *Contras:* Requer atenção aos índices (HNSW / IVFFlat) quando a tabela ultrapassa centenas de milhares de vetores.
  - *Veredito MVP:* Comece com **PostgreSQL + pgvector**. Só migre para vector DB dedicado quando os benchmarks de busca forem o real gargalo do produto.

---

## 2. Padrões de Pipelines de LLM e Agentes

### 2.1 Streaming e Latência
- Modelos generativos levam de 2 a 15 segundos para gerar respostas completas. Nunca bloqueie o request HTTP síncrono do Django (`WSGI`).
- **Opções:**
  1. **ASGI + Django StreamingHttpResponse:** Excelente para respostas de chat síncronas com streaming token a token via SSE (Server-Sent Events).
  2. **Celery + WebSockets (Django Channels):** Ideal para pipelines multiagente em que várias etapas e ferramentas são disparadas ao longo do tempo.
  3. **Polling via Redis:** Simples, robusto e sem dor de cabeça de WebSocket para o MVP. O cliente recebe um `task_id` e faz polling a cada 1 segundo no endpoint `/api/tasks/<id>/status/`.

### 2.2 Frameworks de Orquestração (LangChain vs. LlamaIndex vs. Pure Python)
- **LangChain:** Oferece muitas ferramentas prontas, mas possui excesso de abstração, quebra compatibilidade frequentemente e esconde o que realmente está sendo enviado no prompt.
- **Pure Python + LiteLLM / Pydantic:** Na maioria dos MVPs, chamar o provider diretamente usando `pydantic` para structured outputs (`response_format={"type": "json_schema"}`) e `LiteLLM` para abstrair provedores é muito mais rápido, previsível e fácil de debugar.
- **LangGraph / CrewAI:** Úteis para pipelines com ciclos e tomada de decisão multi-estágio. Só introduza se a lógica demandar backtracking e cooperação complexa entre múltiplos agentes.

### 2.3 Resiliência de Tokens & Vendor Lock-in
- Utilize camadas de proxy/abstração (ex.: `LiteLLM` ou classes de cliente customizadas) para alternar entre OpenAI, Claude, Gemini ou modelos locais (Ollama / vLLM) sem reescrever o código de domínio.
- Estabeleça limites rígidos de max_tokens e retries inteligentes com backoff exponencial.
