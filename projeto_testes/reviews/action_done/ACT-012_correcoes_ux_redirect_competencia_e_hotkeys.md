---
id: ACT-012
titulo: Refinamento Ergonômico de Redirect, Validação CSV e Atalhos JS
modulo: app_financas
relacionado_review: REV-0004
data_criacao: 2026-11-04
status: concluido
data_conclusao: 2026-11-04
autores: [/review, /architect, /ux_designer, /doc_master, /coder]
---

# Proposta de Ação ACT-012: Refinamento Ergonômico de Redirect, Validação CSV e Hotkeys

## 1. Problema Identificado no Review
1. Em `views.py` ([`criar_lancamento_view`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/views.py#L131)), o redirect após criação usava os parâmetros ocultos `ano`/`mes` da tela atual. Se o operador cadastrasse uma despesa com data de outro mês (ex: retroativa), ele era redirecionado para o mês da tela e não via a despesa que acabara de criar.
2. Em `views.py` ([`exportar_extrato_csv_view`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/views.py#L227)), o filtro ativo `categoria` era ignorado e o parâmetro `mes` não possuía validação de faixa `1 <= mes <= 12`.
3. No template `extrato.html` ([atalhos JS](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/templates/app_financas/extrato.html#L320)), teclas como `'n'` e `'e'` não verificavam modificadores, sequestrando atalhos nativos do sistema operacional (ex: `Cmd+N`, `Cmd+E`).

---

## 2. Pareceres Especialistas

> **Parecer de UX/UI (/ux_designer):**  
> - Heurística de Nielsen #1 (Visibilidade do Estado do Sistema): Ao registrar uma transação retroativa, o operador deve ser levado à competência exata da transação para ter feedback imediato de que o dado foi incluído.
> - Heurística de Nielsen #7 (Flexibilidade e Eficiência de Uso): Atalhos globais de teclado devem respeitar teclas modificadoras (`event.ctrlKey`, `event.metaKey`, `event.altKey`) para não degradar a experiência de operadores em Mac/Linux/Windows.

---

## 3. Checklist de Implementação para o /coder:
- [x] Em `criar_lancamento_view`, redirecionar para o ano e mês da competência do lançamento recém-criado (`lancamento.data_competencia.year`, `lancamento.data_competencia.month`).
- [x] Em `exportar_extrato_csv_view`, capturar e aplicar o parâmetro `categoria` e validar `1 <= mes <= 12`.
- [x] Em `extrato.html`, adicionar a trava `const hasModifier = event.ctrlKey || event.metaKey || event.altKey;` antes de capturar `n` e `e`.
- [x] Atualizar testes em `tests.py` validando os fluxos.

