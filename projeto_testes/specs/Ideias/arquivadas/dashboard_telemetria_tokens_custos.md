# 💡 Ideia: Dashboard de Telemetria de Tokens & Custos de IA

- **Autor(es):** Arquiteto de Software & Tech Lead
- **Data:** 02/11/2026
- **Status:** Aprovada para Roadmap (Fase 3)
- **Prioridade:** Média

---

## 1. 🎯 Declaração do Problema
O campo `MensagemChat.tokens_utilizados` já existe e vem sendo alimentado em cada resposta do Gemini. Porém, o operador e o administrador não têm visibilidade de quantos tokens estão sendo consumidos por sessão, por persona ou por dia, nem qual o custo estimado em dólares da fatura da Google GenAI.

---

## 2. 🏛️ Arquitetura Proposta
- **Camada `selectors.py`:**
  - `calcular_tokens_totais_usuario(*, usuario: User) -> int`
  - `obter_consumo_por_persona(*, usuario: User) -> list[dict]`
  - `obter_consumo_ultimos_dias(*, usuario: User, dias: int = 7) -> list[dict]`
- **Cálculo Financeiro:**
  Tabela de preços do Gemini 2.5 Flash:
  - Input: ~$0.075 por 1M tokens.
  - Output: ~$0.30 por 1M tokens.
- **Visualização:**
  Uma aba simples `/chat/dashboard/` com cards de métricas (Total de Mensagens, Total de Tokens, Custo Estimado em US$, Persona Mais Usada).

