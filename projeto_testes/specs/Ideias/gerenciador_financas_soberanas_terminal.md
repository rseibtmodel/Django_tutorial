# 💡 Console de Finanças Pessoais Soberanas & Telemetria Orçamentária Local

- **Autor(es):** Arquiteto de Software, Especialista em UX/UI, Hacker Pragmático, Advogado do Diabo, Estrategista de Impacto & O Alquimista
- **Data de Proposição:** 04/11/2026
- **Status da Ideia:** Aprovada para Roadmap (Fase 5)
- **Prioridade Estimada:** Alta (Score Alquimia: 9.3 / 10.0 - Ouro Puro)
- **ADR Relacionado:** [`specs/architeture/adr_006_app_financas_local_first_cqrs.md`](../architeture/adr_006_app_financas_local_first_cqrs.md)
- **Dossiê de Brainstorm:** [`projeto_testes/brainstorms/26110401_brainstorm_gerenciador_financas_terminal.md`](../../brainstorms/26110401_brainstorm_gerenciador_financas_terminal.md)
- **Síntese Canônica Alquímica:** [`alquimista_ideias/ouro/26110401_alquimia_93_terminal_financas_soberanas.json`](../../../alquimista_ideias/ouro/26110401_alquimia_93_terminal_financas_soberanas.json)

---

## 1. 🎯 Declaração do Problema & Hipótese de Valor

- **Qual a dor atual do operador ou desenvolvedor?**
  Os aplicativos comerciais de gestão financeira falham por excesso de atrito e invasão de privacidade: exigem formulários complexos com múltiplos campos, forçam sincronização de contas bancárias em nuvens públicas de terceiros (com risco de vazamento e venda de dados para birôs de crédito) e impõem interfaces poluídas com gráficos irrelevantes. Por outro lado, o uso de planilhas locais é estéril, não possui validação monetária automática e é desconectado do ecossistema de produtividade e IA do operador.

- **Qual a solução proposta?**
  A criação do módulo **`app_financas`**: um console de finanças pessoais soberano, integrado ao monólito Django e operado sob a estética **Terminal Dark & Verde Neon**. A ferramenta permite:
  1. **Lançamento Telegráfico Instantâneo:** Registro de despesas e receitas em menos de 2 segundos através de comandos de linha única (ex.: `/gasto 45.00 almoco [alimentacao]` ou `/receita 1200.00 freela`), utilizáveis tanto no console web quanto no chat conversacional com as personas de IA.
  2. **Extrato Analítico de Alta Densidade:** Tabela em estilo monospace com cores funcionais (`#00ff66` para receitas, `#ff5555` para despesas), navegação mensal ágil por hotkeys (`[F1/F2]`) e sticky header com saldo líquido e taxa de poupança calculados em tempo real.
  3. **Blindagem Determinística & Soft Delete:** Validação estrita de valores monetários em `Decimal(0.01)` (eliminando float binário), proibição de valores negativos e exclusão lógica contábil auditável via campo `ativo`.
  4. **Alavancagem de IA Sem Risco de Alucinação:** Exposição de ferramentas de Function Calling no Gemini (`TOOL-006` e `TOOL-007`) para que personas atuem como conselheiros financeiros consultando o SQLite local com as travas do backend.

- **Qual o ganho prático?**
  - Redução de 80% no tempo de registro de lançamentos diários comparado a apps convencionais.
  - 100% de privacidade e soberania (zero dados trafegando para servidores externos de terceiros).
  - Precisão contábil absoluta de centavos garantida pelo Django ORM.
  - Eliminação de Shadow IT através do cumprimento do *Teste da Planilha Implacável*.

---

## 2. 🏛️ Impacto Arquitetural Previsto (/architect)

> **Parecer do Arquiteto:**  
> A funcionalidade deve ser encapsulada em um novo aplicativo Django desacoplado (`app_financas`), mantendo o princípio de monólito modular e CQRS estrito formalizado no [ADR 006](../architeture/adr_006_app_financas_local_first_cqrs.md).
>
> **Diretrizes Arquiteturais:**
> 1. *Camada de Dados:* Model canônico único `LancamentoFinanceiro` com `DecimalField(max_digits=12, decimal_places=2)`, Soft Delete (`ativo=models.BooleanField`) e índice composto `['usuario', 'data_competencia', 'ativo']`.
> 2. *Camada `services.py`:* Funções atômicas `sanitizar_e_validar_valor()`, `criar_lancamento()` e `excluir_lancamento()` protegidas por `transaction.atomic()`.
> 3. *Camada `selectors.py`:* Consultas de leitura pura `obter_extrato_mensal()` e `calcular_balanco_periodo()` usando agregações SQL diretas (`aggregate(Sum(...))`).
> 4. *Camada de Views:* Function-Based Views (FBV) com decorators canônicos `@login_required` e `@require_http_methods`.
> 5. *Zero Dependências Externas:* Uso exclusivo da standard library Python (`decimal`, `re`) e ecossistema Django nativo.

- **Novos Modelos de Dados necessários:**
  - `LancamentoFinanceiro` (em `app_financas/models.py`).
- **Alterações em `services.py` e `selectors.py`:**
  - Criação de `app_financas/services.py` e `app_financas/selectors.py`.
  - Integração em `app_chatbot/tools.py` para registro e consulta via IA.
- **Dependências Externas requeridas:**
  Zero novas bibliotecas.

---

## 3. 🎨 Esboço de UX/UI & Ergonomia de Uso (/ux_designer)

> **Parecer do Especialista em UX/UI:**  
> A tela de finanças deve banir gráficos de pizza coloridos e focar em densidade analítica, tipografia monospace e navegação 100% orientada a teclado (Heurísticas de Nielsen #6 - Reconhecimento em vez de Recordação, e #7 - Eficiência de Uso).

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ [SYS_FIN_v1.0] :: FLUXO_DE_CAIXA_LOCAL             DATA: 2026-11-04        │
├────────────────────────────────────────────────────────────────────────────┤
│ SALDO DISPONÍVEL: R$ 4.850,00 [ESTÁVEL]   | RECEITAS: +R$ 6.200,00 [GREEN] │
│ DESPESAS DO MÊS:  R$ 1.350,00 [ALERTA_AMB]| TAXA POUPANÇA: 78.2%           │
│ NAVEGAÇÃO: [F1 / ←] Mês Anterior  |  [F2 / →] Próximo Mês  |  [F3] Filtros  │
├────────────────────────────────────────────────────────────────────────────┤
│ ID   | DATA       | TIPO    | VALOR (R$)   | CATEGORIA   | DESCRIÇÃO       │
│ 0042 | 2026-11-04 | [DEBIT] | -     45,00  | Alimentacao | Almoco executivo│
│ 0041 | 2026-11-03 | [CRED]  | +  1.200,00  | Projetos    | Consultoria PoC │
│ 0040 | 2026-11-02 | [DEBIT] | -    120,00  | Servidores  | VPS Localhost   │
├────────────────────────────────────────────────────────────────────────────┤
│ [CMD] > /gasto 85.00 livros [educacao] █                     [TAB] Autocomplete│
└────────────────────────────────────────────────────────────────────────────┘
```

- **Paleta de Cores e Estilo:**
  - Fundo escuro profundo (`#0d1117`), bordas sutis neon (`#1f242c`).
  - Receitas / Créditos: Verde neon `#00ff66`.
  - Despesas / Débitos: Vermelho / Âmbar `#ff5555`.
  - Valores alinhados à direita com colunas tabulares monoespaçadas.

---

## 4. 🧭 Critérios de Aceite para Entrega

- [ ] Criação do app `app_financas` registrado no `INSTALLED_APPS` do `settings.py`.
- [ ] Model `LancamentoFinanceiro` criado com `DecimalField`, Soft Delete (`ativo`) e migrations aplicadas no SQLite.
- [ ] Camada `services.py` com sanitizador determinístico aceitando tanto vírgula (`35,50`) quanto ponto (`35.50`) e rejeitando valores $\le 0$.
- [ ] Camada `selectors.py` com cálculo agregado de saldo líquido, total de despesas e receitas por competência mensal.
- [ ] Views funcionais criadas (`extrato_financeiro`, `adicionar_lancamento`, `remover_lancamento`) com decorators HTTP estritos.
- [ ] Interface web em Terminal Dark renderizada com tabela monospace e formulário telegráfico de linha única.
- [ ] Duas ferramentas cadastradas no `tools.py` (`TOOL-006` e `TOOL-007`) permitindo ao Gemini registrar e consultar transações.
- [ ] Cobertura de testes automatizados com `django.test.TestCase` para fluxos felizes, validações de erro e soft-delete contábil.

