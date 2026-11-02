# ⚙️ Módulo Interno: Memória Híbrida & ChromaDB

Este documento detalha o subsistema de persistência de memória em dois níveis (curto e longo prazo) que confere continuidade e inteligência ao chatbot.

---

## 1. Visão Geral e Conceito
A maioria dos chatbots sofre de amnésia crônica ao reiniciar ou excede a janela de contexto de tokens do modelo gerador ao tentar passar 100 mensagens anteriores.  
Para resolver isso, implementamos uma **Memória Híbrida**:
1. **Memória de Curto Prazo (Episódica Relacional):** O SQLite armazena a ordem cronológica exata das mensagens (`MensagemChat`). Os últimos 6 turnos são sempre enviados no payload de contexto imediato do Gemini.
2. **Memória de Longo Prazo (Semântica Vetorial):** O ChromaDB armazena representações vetoriais de 3072 dimensões de todas as perguntas, respostas e fatos compartilhados pelo operador.

---

## 2. Componentes Internos

### 2.1 Gerenciador Singleton Thread-Safe (`VectorStoreManager`)
Localizado em `app_chatbot/vector_store.py`:
- Utiliza padrão Singleton com double-checked locking (`threading.Lock()`).
- Inicializa o `chromadb.PersistentClient` apontando para o diretório local `projeto_testes/chroma_data`.
- Cria ou recupera a coleção vetorial nomeada `"chat_memory_store"` configurada com espaço métrico de cosseno (`metadata={"hnsw:space": "cosine"}`).

### 2.2 Modelo de Embeddings
- **SDK:** `google-genai` (v2.0+).
- **Modelo:** `gemini-embedding-001`.
- **Dimensões:** 3.072 dimensões float.
- **Isolamento de Metadata:**
  Cada vetor gravado na coleção carrega metadados para garantir que consultas nunca vazem dados entre usuários ou sessões:
  ```json
  {
    "usuario_id": "1",
    "sessao_id": "86b94fb7-3c8a-45f1-8d5e-8af25a1a011f",
    "tipo": "memoria_conversa"
  }
  ```

---

## 3. Fluxo de Consulta e Recuperação
1. O usuário digita uma pergunta: *"Qual o meu cargo?"*.
2. O método `_recuperar_contexto_semantico(pergunta)` gera o embedding da pergunta.
3. Executa a query vetorial no ChromaDB com filtro:
   `where={"$and": [{"usuario_id": "..."}, {"sessao_id": "..."}]}`
4. Recupera os top 3 a 5 documentos mais próximos semanticamente.
5. Injeta no System Prompt:
   ```text
   [MEMÓRIA DE CONVERSAS ANTERIORES]
   Pergunta: Eu sou o Rodrigo e sou Arquiteto de Software.
   Resposta: Entendido, Rodrigo!
   ```
6. O modelo responde com naturalidade lembrando-se do fato sem precisar de todo o histórico.

