# 🏛️ ADR 002: Separação de Camadas (Services, Selectors, Exceptions & FBVs)

- **Status:** Aprovado & Implementado
- **Decisores:** Tech Lead, Arquiteto de Software, Estagiário Codificador
- **Data:** 01/11/2026

---

## 1. Contexto & Problema
O padrão Django tradicional frequentemente gera dois anti-padrões:
1. *"Fat Views"*: Views abarrotadas de queries de banco, validações manuais e chamadas de API externa.
2. *"Fat Models"*: Models com centenas de linhas de métodos utilitários, virando classes deusas.

---

## 2. Decisão Arquitetural
Adotar a convenção do *Two Scoops of Django* com arquitetura modular em camadas:
- **`selectors.py`:** Centraliza todas as queries de leitura, filtros e relacionamentos do ORM (`select_related`, `prefetch_related`). Views nunca realizam queries complexas diretamente.
- **`services.py`:** Centraliza regras de negócio, transações, mutações de dados e orquestração de IA.
- **`exceptions.py`:** Exceções tipadas do app em vez de retornar tuplas `(False, "erro")` ou strings mágicas.
- **Function-Based Views (FBVs):** Views magras e previsíveis decoradas com `@login_required` e `@require_POST`.

---

## 3. Consequências & Trade-offs
- **Positivas:**
  - Testabilidade unitária de 100% da lógica sem precisar instanciar requisições HTTP falsas.
  - Eliminação de queries N+1 no ORM.
  - Reutilização simples de lógica em tarefas assíncronas ou comandos de terminal.
- **Negativas:**
  - Maior quantidade inicial de arquivos por app.

