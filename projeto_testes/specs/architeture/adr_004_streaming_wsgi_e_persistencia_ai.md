# 🏛️ ADR 004: Streaming de Tokens via WSGI & Prevenção de Auto-Intoxicação de Prompt

- **Status:** Aprovado & Implementado
- **Decisores:** Arquiteto de Software, Tech Lead
- **Data:** 01/11/2026

---

## 1. Contexto & Problema
Modelos de linguagem modernos levam de 2 a 10 segundos para gerar respostas completas. Em conexões HTTP convencionais bloqueantes, o usuário aguarda todo esse tempo em tela congelada. Além disso, se a chamada de IA falhar e o erro for salvo no banco, esse erro contamina o contexto subsequente.

---

## 2. Decisão Arquitetural
1. **Streaming via `StreamingHttpResponse`:**
   Utilizar gerador Python em tempo real que lê os chunks do `client.models.generate_content_stream()` do Gemini e envia com header `X-Accel-Buffering: no` para desativar bufferings intermediários.
2. **Separação Rígida de Persistência:**
   - As mensagens enviadas pelo usuário são salvas imediatamente no SQLite (`papel='user'`).
   - A resposta do assistente (`papel='model'`) **só é persistida se a inferência for concluída com sucesso**.
   - Em caso de falha de API, a mensagem de erro é transmitida no stream para feedback do usuário, mas **nunca vira registro no banco**, evitando que traces técnicos virem contexto futuro.

---

## 3. Consequências & Trade-offs
- **Positivas:**
  - Percepção de latência quase nula: o primeiro token surge na tela em milissegundos.
  - O histórico de contexto da conversa permanece 100% puro e sem contaminação.
- **Negativas:**
  - Conexões síncronas de streaming seguram o worker WSGI durante o tempo da resposta. Para cenários com milhares de usuários simultâneos, a evolução para ASGI (Uvicorn / Daphne) será mandatória.

