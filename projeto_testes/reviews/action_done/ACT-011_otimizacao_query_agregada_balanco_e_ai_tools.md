---
id: ACT-011
titulo: Agregação SQL Única no Balanço e Otimização de Consultas de IA
modulo: app_financas
relacionado_review: REV-0004
data_criacao: 2026-11-04
status: concluido
data_conclusao: 2026-11-04
autores: [/review, /architect, /doc_master, /coder]
---

# Proposta de Ação ACT-011: Agregação SQL Única e Otimização de Queries

## 1. Problema Identificado no Review
1. Em `selectors.py` ([`calcular_balanco_periodo`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/selectors.py#L80-L103)), a contagem `qs.count()` era chamada separadamente logo após `qs.aggregate()`, gerando 2 queries SQL por requisição.
2. Em `app_chatbot/tools.py` ([`consultar_extrato_financeiro`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/tools.py#L309)), havia uma chamada `if lancamentos.exists():` antes de fatiar `lancamentos[:15]`, gerando uma query `SELECT (1)` supérflua.

---

## 2. Parecer do Arquiteto de Software (/architect)
> **Diagnóstico Arquitetural:**
> O Django ORM permite embutir `Count("id")` dentro do mesmo dicionário de agregação de `Sum(...)`. Isso consolida toda a leitura analítica em uma única sentença `SELECT SUM(...), SUM(...), COUNT(...) FROM ...`.
> Na camada de tools de IA, converter o slice diretamente para lista `list(lancamentos[:15])` evita um round-trip de rede para verificar existência.

---

## 3. Checklist de Implementação para o /coder:
- [x] Em `selectors.py`, incluir `total_lancamentos=Count("id")` dentro de `qs.aggregate(...)` e remover a chamada `qs.count()`.
- [x] Em `app_chatbot/tools.py`, substituir a checagem `lancamentos.exists()` por avaliação da lista fatiada `list(lancamentos[:15])`.
- [x] Rodar suíte de testes garantindo 100% de sucesso.

