# 🏛️ ADR 001: Monólito Modular Django vs. Microsserviços de IA

- **Status:** Aprovado & Implementado
- **Decisores:** Arquiteto de Software, Tech Lead
- **Data:** 30/10/2026

---

## 1. Contexto & Problema
Ao projetar sistemas que integram pipelines de Inteligência Artificial e LLMs, é comum a tentação de criar serviços isolados em FastAPI ou Flask exclusivamente para a IA, mantendo o backend tradicional em outro serviço. Esse paradigma introduz sobrecarga operacional precoce (múltiplos deploys, autenticação JWT entre serviços, tracing distribuído e schemas duplicados).

---

## 2. Decisão Arquitetural
Adotar o padrão **Monólito Modular Django**:
- O Django gerencia autenticação, banco relacional (SQLite/PostgreSQL), ORM, painel administrativo e a orquestração do LLM.
- O isolamento entre módulos de IA e regras de negócio é feito através de camadas no próprio repositório (`services.py`, `selectors.py`), mantendo alta coesão e baixo acoplamento sem a complexidade de rede de microsserviços.

---

## 3. Consequências & Trade-offs
- **Positivas:**
  - Velocidade de iteração e validação de MVP em dias, não meses.
  - Reúso direto do sistema de usuários nativo do Django (`django.contrib.auth`).
  - Deploy simplificado em processo único.
- **Negativas / Limitações:**
  - O dimensionamento conjunto da camada web e dos pipelines de inferência exige cuidado com conexões síncronas sob alta carga.

