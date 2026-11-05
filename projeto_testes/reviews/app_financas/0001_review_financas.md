# Relatório de Auditoria: Validação Contábil, Resiliência CQRS e Usabilidade

- **ID do Review:** REV-0004
- **Data da Auditoria:** 2026-11-04
- **Auditor:** Agente 1 (Tech Lead Sênior de Python & Django)
- **Módulo:** `app_financas`
- **Arquivos Auditados:**
  - [`models.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/models.py)
  - [`services.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/services.py)
  - [`selectors.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/selectors.py)
  - [`views.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/views.py)
  - [`templates/app_financas/extrato.html`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/templates/app_financas/extrato.html)
  - [`app_chatbot/tools.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/tools.py)
- **Status:** `RESOLVIDO`

---

## 1. Parecer Técnico Geral do Tech Lead

> *"O Estagiário Codificador estruturou muito bem a base: Decimal(0.01) salvou o monólito de erros de ponto flutuante, o isolamento em app_financas foi respeitado e o CQRS com services e selectors está no padrão Two Scoops of Django. Porém, encontramos o clássico fantasma do Timezone Deslocado (timezone.now em DateField gravando transações no dia seguinte após as 21h em Brasília), redundância de queries com qs.count() após qs.aggregate(), desorientação de redirect pós-lançamento retroativo e sequestro de atalhos globais de SO no JavaScript. Abaixo está o relatório oficial catalogado com suas ações vinculadas."*

---

## 2. Resumo de Severidade das Ocorrências

| Severidade | Quantidade | Descrição Sintética |
| :--- | :---: | :--- |
| `[CRÍTICO]` | 1 | Timezone deslocado (`timezone.now` em `DateField` gerando datas adiantadas em UTC) |
| `[ALERTA]` | 3 | Query `qs.count()` redundante, redirect pós-criação cego e CSV sem filtro/validação |
| `[RECOMENDAÇÃO]` | 2 | Sequestro de teclas modificadoras no JS e `exists()` antes do slice no Tool Calling |

---

## 3. Apontamentos Cirúrgicos & Vínculo com Propostas de Ação

### 1. `[CRÍTICO]` Viagem no Tempo: `timezone.now` como default em `DateField`
- **Código Original ([models.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/models.py#L59-L63) e [services.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/services.py#L218-L220)):**
```python
# models.py
data_competencia = models.DateField(
    default=timezone.now,
    verbose_name="Data de Competência",
)

# services.py
if data_competencia is None:
    data_final = timezone.now().date()
```
- **Diagnóstico & Crítica:**  
  Com `USE_TZ = True`, `timezone.now()` retorna um datetime em UTC. Em transações realizadas após as 21h em São Paulo (UTC-3), já é 00h+ do dia seguinte em UTC. O truncamento do Django para `DateField` grava a data fiscal no dia posterior.
- **Impacto:** Lançamentos com data contábil adiantada em relação ao momento real da despesa.
- **Ação Vinculada:** 🔗 [ACT-010: Correção de Timezone nos Defaults de Data e Services Contábeis](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action/ACT-010_correcao_fuso_horario_timezone_localdate.md)

---

### 2. `[ALERTA]` Desperdício de I/O: Query `qs.count()` disparada após `qs.aggregate()`
- **Código Original ([selectors.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/selectors.py#L80-L103)):**
```python
    resultado = qs.aggregate(
        total_receitas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_RECEITA)),
        total_despesas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_DESPESA)),
    )
    ...
    return {
        ...
        "total_lancamentos": qs.count(),
    }
```
- **Diagnóstico & Crítica:**  
  `qs.aggregate(...)` já executa um `SELECT` agregado no SQLite. Invocar `qs.count()` na linha seguinte força uma segunda query `SELECT COUNT(*)` desnecessária.
- **Impacto:** Dois round-trips ao banco em cada requisição de extrato.
- **Ação Vinculada:** 🔗 [ACT-011: Agregação SQL Única no Balanço e Otimização de Consultas de IA](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action/ACT-011_otimizacao_query_agregada_balanco_e_ai_tools.md)

---

### 3. `[ALERTA]` Desorientação Espacial: Redirecionamento da View ignora a competência real do lançamento
- **Código Original ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/views.py#L131-L136)):**
```python
    ano_dest = request.POST.get("ano") or request.GET.get("ano")
    mes_dest = request.POST.get("mes") or request.GET.get("mes")
    redirect_url = reverse("app_financas:extrato")
    if ano_dest and mes_dest:
        redirect_url += f"?ano={ano_dest}&mes={mes_dest}"
```
- **Diagnóstico & Crítica:**  
  Se o operador cadastra uma despesa retroativa de outro mês (ex: mês 09) enquanto navega no mês 11, o redirect o devolve ao mês 11, dando a falsa impressão de que o lançamento se perdeu.
- **Impacto:** Atrito severo de visibilidade de estado (Nielsen #1) e risco de lançamentos duplicados por engano.
- **Ação Vinculada:** 🔗 [ACT-012: Refinamento Ergonômico de Redirect, Validação CSV e Atalhos JS](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action/ACT-012_correcoes_ux_redirect_competencia_e_hotkeys.md)

---

### 4. `[ALERTA]` Exportação CSV Amnésica e sem Validação de Range
- **Código Original ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/views.py#L227-L239)):**
- **Diagnóstico & Crítica:**  
  O download do CSV ignora o filtro ativo `categoria` e aceita qualquer número de mês sem checagem de intervalo `1 <= mes <= 12`.
- **Ação Vinculada:** 🔗 [ACT-012: Refinamento Ergonômico de Redirect, Validação CSV e Atalhos JS](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action/ACT-012_correcoes_ux_redirect_competencia_e_hotkeys.md)

---

### 5. `[RECOMENDAÇÃO]` Sequestro de Atalhos do Sistema Operacional no JavaScript
- **Código Original ([extrato.html](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_financas/templates/app_financas/extrato.html#L320-L330)):**
- **Diagnóstico & Crítica:**  
  Atalhos `'n'` e `'e'` disparam `event.preventDefault()` mesmo se `Cmd` ou `Ctrl` estiverem pressionados, interceptando atalhos nativos do navegador (`Cmd+N`, `Cmd+E`).
- **Ação Vinculada:** 🔗 [ACT-012: Refinamento Ergonômico de Redirect, Validação CSV e Atalhos JS](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action/ACT-012_correcoes_ux_redirect_competencia_e_hotkeys.md)

---

### 6. `[RECOMENDAÇÃO]` Consulta Dupla de `exists()` antes do Slice no Tool Calling
- **Código Original ([app_chatbot/tools.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/tools.py#L309-L315)):**
- **Diagnóstico & Crítica:**  
  `lancamentos.exists()` seguido de `for l in lancamentos[:15]` executa duas queries SQL em vez de fatiar diretamente a lista.
- **Ação Vinculada:** 🔗 [ACT-011: Agregação SQL Única no Balanço e Otimização de Consultas de IA](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/reviews/action/ACT-011_otimizacao_query_agregada_balanco_e_ai_tools.md)

---

## 4. Checklist Geral de Resolução do Módulo

- [x] **ACT-010:** Substituir `timezone.now` por `timezone.localdate` no model e camada de services.
- [x] **ACT-011:** Unificar cálculo de contagem e somas em `Count("id")` dentro de `qs.aggregate()` no `selectors.py`.
- [x] **ACT-011:** Otimizar `consultar_extrato_financeiro` em `tools.py` eliminando a chamada duplicada de `exists()`.
- [x] **ACT-012:** Ajustar redirect de `criar_lancamento_view` para direcionar à competência do lançamento recém-criado.
- [x] **ACT-012:** Propagar filtro de `categoria` e validação de mês `1 <= mes <= 12` em `exportar_extrato_csv_view`.
- [x] **ACT-012:** Adicionar trava `!event.ctrlKey && !event.metaKey && !event.altKey` nos atalhos de teclado de `extrato.html`.

