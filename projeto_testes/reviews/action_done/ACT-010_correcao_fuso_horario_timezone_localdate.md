---
id: ACT-010
titulo: Correção de Timezone nos Defaults de Data e Services Contábeis
modulo: app_financas
relacionado_review: REV-0004
data_criacao: 2026-11-04
status: concluido
data_conclusao: 2026-11-04
autores: [/review, /architect, /doc_master, /coder]
---

# Proposta de Ação ACT-010: Correção de Fuso Horário e Timezone Localdate

## 1. Problema Identificado no Review
Em `models.py` ([`LancamentoFinanceiro.data_competencia`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/models.py#L59)), o campo utilizava `default=timezone.now`. Em `services.py` ([`criar_lancamento`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/services.py#L219)), utilizava-se `timezone.now().date()`.
Como `USE_TZ = True`, `timezone.now()` opera em UTC. Lançamentos realizados após as 21h no fuso do Brasil (`America/Sao_Paulo`, UTC-3) recebiam a data contábil de **amanhã**, gerando inconsistência fiscal.

---

## 2. Parecer do Arquiteto de Software (/architect)
> **Diagnóstico Arquitetural:**
> Para campos `DateField` puros, o Django fornece a função canônica `timezone.localdate`. O callable `timezone.localdate` converte o instante atual para o timezone ativo antes de extrair a data, evitando desvios de fuso.
> 
> **Diretriz Técnica:**
> 1. Alterar o default do model para `default=timezone.localdate`.
> 2. Gerar migration formal para refletir o default correto no model.
> 3. Substituir `timezone.now().date()` por `timezone.localdate()` em `services.py`, `views.py` e `tools.py`.

---

## 3. Checklist de Implementação para o /coder:
- [x] Alterar `models.py` para `data_competencia = models.DateField(default=timezone.localdate, ...)`.
- [x] Rodar `makemigrations app_financas` e `migrate`.
- [x] Substituir `timezone.now().date()` por `timezone.localdate()` em `app_financas/services.py` e `app_financas/views.py`.
- [x] Atualizar testes em `tests.py` validando que transações criadas sem data assumem a data local.

