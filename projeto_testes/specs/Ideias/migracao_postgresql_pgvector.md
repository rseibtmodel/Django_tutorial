---
id: IDEA-005
titulo: Migração de ChromaDB Local para PostgreSQL com Extensão pgvector
modulo: Ideias
versao: 1.0.0
status: rascunho
ultima_atualizacao: 2026-11-02
autores: [/architect, /doc]
---

# 💡 Migração de ChromaDB Local para PostgreSQL com Extensão pgvector

- **Autor(es):** Arquiteto de Software & Guardião da Documentação
- **Data de Proposição:** 02/11/2026
- **Status da Ideia:** Aprovada para Roadmap (Fase 4)
- **Prioridade Estimada:** Alta (Escala e Transacionalidade)

---

## 1. 🎯 Declaração do Problema & Hipótese de Valor

- **Qual a dor atual do operador ou desenvolvedor?**
  Atualmente, o sistema utiliza uma persistência híbrida: banco relacional SQLite para modelos (`User`, `Persona`, `SessaoChat`, `DocumentoSessao`) e banco vetorial ChromaDB local armazenado em pasta (`chroma_data/`). Essa arquitetura introduz risco de dessincronização em deploys distribuídos, falta de transações ACID atômicas entre metadados relacionais e embeddings vetoriais, e limitações de concorrência de leitura/escrita em ambiente multi-worker (ex.: Gunicorn/Uvicorn).

- **Qual a solução proposta?**
  Migrar a persistência do monólito modular para **PostgreSQL 16+** com a extensão oficial **`pgvector`**. Os embeddings vetoriais (3072 dimensões do Gemini) passarão a ser armazenados como colunas do tipo `vector(3072)` diretamente nas tabelas `DocumentoChunk` e `MemoriaSessao` dentro do schema relacional do PostgreSQL.

- **Qual o ganho prático?**
  - Transações ACID atômicas (se o documento falhar na persistência, os vetores sofrem rollback imediato).
  - Consultas vetoriais nativas no Django via `django-pgvector` ou SQL raw com índices `HNSW` e `IVFFlat`.
  - Eliminação total da pasta local `chroma_data/` e simplificação radical de backups e réplicas de leitura.

---

## 2. 🏛️ Impacto Arquitetural Previsto

- **Novos Modelos de Dados necessários:**
  - `MemoriaSemantica` e `DocumentoChunkVetorial` com coluna `embedding = VectorField(dimensions=3072)`.
  - Índice HNSW com métrica de distância cosseno: `HnswIndex(fields=['embedding'], opclasses=['vector_cosine_ops'])`.
- **Alterações em `services.py` e `selectors.py`:**
  - Substituição da classe `VectorStoreManager` do ChromaDB por queries diretas no ORM do Django utilizando `.annotate(distancia=CosineDistance('embedding', query_vector)).order_by('distancia')[:5]`.
- **Dependências Externas requeridas:**
  - `psycopg` (versão 3) e `pgvector-python`.
- **Riscos Técnicos & Pontos Cegos (Ataque à Jugular):**
  - Memória RAM para índices HNSW em vetores de 3072 dimensões (requer dimensionamento cuidadoso de `work_mem` e `shared_buffers`).

---

## 3. 🎨 Esboço de UX/UI & Ergonomia de Uso

- **Como o operador acessa essa funcionalidade?**
  A migração é transparente para o operador final. No entanto, o comando `/status` no terminal do chat passará a exibir o status do cluster PostgreSQL e do índice `pgvector` ativo.

---

## 4. 🧭 Critérios de Aceite para Entrega

- [ ] Docker Compose configurado com imagem `pgvector/pgvector:pg16`.
- [ ] Modelos de chunks e memória convertidos para `VectorField(dimensions=3072)` com índice HNSW.
- [ ] Script de migração de dados de `chroma_data/` para o PostgreSQL sem perda de dados históricos.
- [ ] 100% da suíte de testes de RAG e Chatbot validada e verde contra o banco PostgreSQL.
- [ ] Atualização do ADR correspondente em `specs/architeture/`.

