# 💡 Console de Faturas de Cartão, Agendamento Futuro & Saldo Espectral

- **Autor(es):** Arquiteto de Software, Especialista em UX/UI, Hacker Pragmático, Advogado do Diabo, Estrategista de Impacto & O Alquimista
- **Data de Proposição:** 04/11/2026
- **Status da Ideia:** Aprovada para Roadmap (Fase 6 / Expansão Finanças)
- **Prioridade Estimada:** Alta (Score Alquimia: 9.3 / 10.0 - Ouro Puro)
- **ADR Relacionado:** [`specs/architeture/adr_007_faturas_cartao_agendamento_e_saldo_projetado.md`](../architeture/adr_007_faturas_cartao_agendamento_e_saldo_projetado.md)
- **Dossiê de Brainstorm:** [`projeto_testes/brainstorms/26110402_brainstorm_faturas_cartao_agendamento_multimes.md`](../../brainstorms/26110402_brainstorm_faturas_cartao_agendamento_multimes.md)
- **Síntese Canônica Alquímica:** [`alquimista_ideias/ouro/26110402_alquimia_93_faturas_cartao_fluxo_multimes.json`](../../../alquimista_ideias/ouro/26110402_alquimia_93_faturas_cartao_fluxo_multimes.json)

---

## 1. 🎯 Declaração do Problema & Hipótese de Valor

- **Qual a dor atual do operador ou desenvolvedor?**
  O módulo de finanças atual gerencia com perfeição as transações diretas e pontuais do mês corrente, mas carece de controle sobre o maior vetor de despesas dos profissionais de tecnologia: **o cartão de crédito**. Hoje, registrar compras de cartão gera dois extremos nocivos:
  1. Ou o usuário lança cada cafezinho e compra online poluindo o extrato com dezenas de linhas que competem com o saldo da conta corrente (gerando dupla contagem quando o boleto da fatura também é pago).
  2. Ou o usuário lança apenas o valor consolidado da fatura no vencimento, perdendo totalmente a visibilidade e o histórico analítico de onde o dinheiro do cartão foi gasto.
  Além disso, o operador não consegue projetar despesas agendadas futuras para antecipar o impacto na liquidez do final do mês.

- **Qual a solução proposta?**
  A implementação da **Arquitetura Bipartida de Cartão** e **Saldo Espectral** no `app_financas`:
  1. **Gaveta Modal de Fatura (`[F4]`):** Ingestão local de PDFs de fatura bancária (sem conexão de Open Finance nem tráfego de dados para nuvens externas). Os itens detalhados da fatura são armazenados isoladamente em `ItemFaturaCartao` e consultáveis sob demanda.
  2. **Agendamento no Vencimento:** A confirmação da fatura agenda automaticamente uma **única despesa consolidada** no extrato geral na data exata do vencimento, com `status='PREVISTO'` e categoria `cartao_credito`.
  3. **Saldo Espectral (Real vs Projetado):** O dashboard exibe lado a lado o *Saldo Efetivado* (dinheiro real no bolso hoje) e o *Saldo Projetado* (o caixa que restará após a fatura e provisões agendadas debitarem).
  4. **Causalidade Multimês:** Navegação e criação de transações retroativas ou futuras em qualquer mês ou ano sem atrito.

- **Qual o ganho prático?**
  - Zero dupla contagem contábil de compras de cartão.
  - Redução de 90% no tempo de conciliação de faturas via upload local de PDF.
  - Visibilidade antecipada de solvência para os próximos 30 a 60 dias (Runway pessoal).
  - 100% de soberania e privacidade de dados financeiros mantidos em SQLite local.

---

## 2. 🏛️ Impacto Arquitetural Previsto (/architect)

> **Parecer do Arquiteto:**  
> A solução é formalizada no [ADR 007](../architeture/adr_007_faturas_cartao_agendamento_e_saldo_projetado.md). Adotamos a segregação estrita entre compras de cartão e movimentações de conta corrente, preservando o princípio CQRS.
>
> **Diretrizes Técnicas:**
> 1. *Extensão de Dados:* Adição de `status` (`EFETIVADO` / `PREVISTO`) em `LancamentoFinanceiro`.
> 2. *Novas Entidades:* `FaturaCartao` (com `UniqueConstraint` para evitar duplo agendamento de fatura) e `ItemFaturaCartao` (detalhe das compras).
> 3. *Parser Local:* Extração de texto de PDF no backend via streams locais e regex, populando a conferência no modal.
> 4. *Selectors Analíticos:* `calcular_balanco_periodo` atualizado para computar `saldo_efetivado` e `saldo_projetado` em consulta SQL otimizada.

- **Novos Modelos de Dados necessários:**
  - `FaturaCartao` e `ItemFaturaCartao` em `app_financas/models.py`.
- **Alterações em `services.py` e `selectors.py`:**
  - Funções de parsing de PDF, criação atômica de fatura e agendamento contábil em `services.py`.
  - Agregações de saldo efetivado e projetado em `selectors.py`.
- **Dependências Externas requeridas:**
  Zero dependências externas obrigatórias (uso de streams nativos e standard library).

---

## 3. 🎨 Esboço de UX/UI & Ergonomia de Uso (/ux_designer)

> **Parecer do Especialista em UX/UI:**  
> A interface utiliza a estética Terminal Dark com atalhos de teclado dedicados:
> - `[F4]`: Abre o Modal HUD de Fatura para upload e conferência de compras.
> - Badge Neon `[PREV]` (Ciano `#58a6ff`) destacando provisões e faturas agendadas no extrato.
> - Link rápido `[VER_FATURA]` sobre a despesa consolidada para reabrir a discriminação dos itens.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ [SYS_FIN_v2.0] :: FLUXO_DE_CAIXA_LOCAL & CARTÕES       COMPETÊNCIA: 2026-11│
├────────────────────────────────────────────────────────────────────────────┤
│ SALDO DISPONÍVEL: R$ 4.850,00 [GREEN]   | FATURA ABERTA (NOV): R$ 1.840,00 │
│ PROVISÕES FUTURAS: R$ 2.400,00 [AMBER]  | SALDO PROJETADO FINAL: R$ 610,00 │
├────────────────────────────────────────────────────────────────────────────┤
│ NAVEGAÇÃO: [F1] Mês Ant. | [F2] Próx. Mês | [F4] Faturas | [F5] Filtros    │
├────────────────────────────────────────────────────────────────────────────┤
│ >> JANELA DUAL-PANE (INSPEÇÃO DE FATURA CARTÃO [F4])                       │
│ ┌─ [FATURA NUBANK - VENC: 2026-11-25] ───────────────────────────────────┐ │
│ │ 04/11 | Uber *Trip 1042                     | transporte   |   R$  28,50 │
│ │ 03/11 | Mercado Livre *Teclado Mecânico     | equipamento  |   R$ 340,00 │
│ │ 28/10 | Amazon AWS Cloud Hosting            | infra        |   R$ 185,20 │
│ │ 22/10 | Restaurante Ponto Chic              | alimentacao  |   R$  89,00 │
│ ├────────────────────────────────────────────────────────────────────────┤ │
│ │ TOTAL CALCULADO (14 ITENS): R$ 1.840,50                                │ │
│ │ [AÇÃO] > [CONSOLIDAR E AGENDAR DESPESA NO EXTRATO (ENTER)]             │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 🧭 Critérios de Aceite para Entrega

- [ ] Campo `status` (`EFETIVADO` / `PREVISTO`) adicionado a `LancamentoFinanceiro` com migração aplicada.
- [ ] Modelos `FaturaCartao` e `ItemFaturaCartao` criados com `UniqueConstraint` anti-duplicidade e relacionamento `OneToOne` com o lançamento consolidado.
- [ ] Parser de PDF de fatura implementado em `services.py` com extração de data, descrição e valor.
- [ ] Função `salvar_fatura_e_agendar_despesa` persistindo itens e gerando lançamento único no vencimento com `status='PREVISTO'`.
- [ ] Cálculo analítico duplo em `selectors.py` (`saldo_efetivado` e `saldo_projetado`).
- [ ] Modal HUD em Terminal Dark (`[F4]`) com upload de PDF, tabela de itens e confirmação em 1 clique.
- [ ] Exibição diferenciada no extrato com badge `[PREV]` e atalho `[VER_FATURA]`.
- [ ] Cobertura de testes automatizados com `django.test.TestCase` para parsing, agendamento atômico, restrição anti-duplicação e cálculos de saldo projetado.

