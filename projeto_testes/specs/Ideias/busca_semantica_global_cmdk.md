# 💡 Ideia: Busca Semântica Global no Histórico (`Cmd+K`)

- **Autor(es):** UX Designer & Arquiteto de Software
- **Data:** 02/11/2026
- **Status:** Proposta (Fase 4)
- **Prioridade:** Alta (após hardening)

---

## 1. 🎯 Declaração do Problema
Hoje a busca do ChromaDB só recupera memórias da **sessão ativa**. Se o usuário conversou há 3 semanas na "Sessão A" sobre uma regra de negócio específica e agora está na "Sessão B", ele não consegue recuperar essa informação a menos que lembre qual era a sessão antiga.

---

## 2. 🏛️ Arquitetura Proposta
- **Query Vetorial Global:**
  Executar consulta no ChromaDB filtrando apenas por `usuario_id` (sem amarrar `sessao_id`):
  `collection.query(query_embeddings=[vetor], where={"usuario_id": str(user.id)}, n_results=10)`.
- **Interface Modal `Cmd+K`:**
  Pressionar `Cmd+K` ou `Ctrl+K` abre uma janela modal flutuante estilo Spotlight / Raycast.
  Ao digitar uma pergunta ou termo, o sistema exibe os turnos e documentos mais relevantes de qualquer conversa do passado com link direto para pular para aquela sessão.

