# 💡 Ideia: Exportador de Conversas (Markdown & PDF)

- **Autor(es):** UX Designer & Arquiteto de Software
- **Data:** 02/11/2026
- **Status:** Aprovada para Roadmap (Fase 3)
- **Prioridade:** Média-Alta

---

## 1. 🎯 Declaração do Problema
O operador tem conversas ricas em insights, código e discussões técnicas no terminal, mas não possui um meio rápido de extrair o conteúdo para compartilhar com a equipe, salvar em documentações ou anexar em relatórios executivos.

---

## 2. 🏛️ Arquitetura Proposta
- **Formato Markdown (`.md`):**  
  Implementação pura em Python com geração de texto formatado:
  - Cabeçalho com título, persona utilizada, data e operador.
  - Turnos identificados com `### 👤 Operador:` e `### 🤖 Persona [Cargo]:`.
  - Blocos de código delimitados com crases triplas.
  - Resposta direta via `HttpResponse(conteudo, content_type="text/markdown")` com header `Content-Disposition: attachment; filename="conversa.md"`.
- **Formato PDF:**  
  Avaliar se vale introduzir dependência de renderização HTML-to-PDF ou manter foco no Markdown limpo para o MVP.

---

## 3. 🎨 UX/UI
Botão discreto no cabeçalho do terminal:
`[⬇ EXPORTAR .MD]` ao lado do título da sessão.

