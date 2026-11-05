# Dossiê de Brainstorm: Faturas de Cartão, Agendamento Futuro & Causalidade Multimês

- **Código:** `BRN-26110402`
- **Data da Sessão:** 04/11/2026
- **Agentes Participantes:** O Oráculo Hermético do Caos, Arquiteto de Software, Especialista em UX/UI, Advogado do Diabo, Hacker Pragmático, Estrategista de Impacto & O Alquimista
- **Síntese Alquímica Consolidada:** [`alquimista_ideias/ouro/26110402_alquimia_93_faturas_cartao_fluxo_multimes.json`](file:///Users/rodrigomodel/agentes_inteligentes/alquimista_ideias/ouro/26110402_alquimia_93_faturas_cartao_fluxo_multimes.json)
- **Score Final:** `9.3 / 10.0 (Ouro Puro)`

---

## 1. 🎯 Desafio de Entrada do Operador

> *"Quero agora que pense em algumas features muito importantes: poder adicionar transações de meses diferentes, poder programar despesas para o futuro, permitir carregar a fatura de um cartão de crédito em que vai fazer duas operações: uma janela em que poderei consultar a fatura e a outra é cadastrar a despesa no vencimento do cartão."*

---

## 2. 🔮 Fase 0: Divergência Pura do Oráculo

O Oráculo gerou 7 anomalias ontológicas explorando causalidade reversa e bipartição epistemológica. A anomalia central selecionada foi:

> ### A BIPARTIÇÃO CRIPTOGRÁFICA DO CARTÃO (O ESPELHO E A GUILHOTINA)
> *“Ver o detalhe da gula não deve contaminar a solene simplicidade do abate.”*
> 
> Uma fatura de cartão não é um conjunto de transações correntes; é um fóssil coletivo que hiberna até o instante do vencimento. O sistema cria dois planos: a câmara hermética onde cada café é inspecionado isoladamente, e a guilhotina única no extrato que consolida o débito total no vencimento.

---

## 3. ⚔️ Fase 1: As Rodadas da Mesa de Discussão

### Rodada 1: Diagnóstico Inicial
- **Hacker Pragmático:** Proposta de modelagem bipartida (`FaturaCartao` e `ItemFaturaCartao`) fora do extrato geral. Transações futuras como queries de data sem necessidade de Celery/Redis.
- **Advogado do Diabo:** Alerta crítico sobre **dupla contagem contábil** se compras do cartão coexistirem com a despesa da fatura no mesmo extrato.
- **Estrategista de Impacto:** Criação do conceito de **Saldo Espectral (Cash Flow Runway)**: projeção antecipada de solvência para os próximos 60 dias sem exigir Open Finance.
- **UX Designer:** Esboço do layout com atalhos de competência e badge `[PREV]` para transações futuras agendadas.
- **Arquiteto:** Segregação com status `EFETIVADO` vs `PREVISTO` no model e cálculo de balanço duplo.

### Calibração do Operador:
1. Compras do cartão ficam restritas à janela da fatura; no extrato geral entra apenas a despesa única no vencimento.
2. Formato de ingestão prioritário: PDF de fatura.

### Rodada 2: Confronto Cruzado & Bypasses
- **Crítico vs Hacker:** O Crítico questionou a fragilidade de PDFs bancários brasileiros e o risco de duplo clique. O Hacker contra-atacou com uma `UniqueConstraint(usuario, cartao, ano, mes)` que impede agendamentos duplicados a nível de banco de dados, e propôs uma janela de conferência editável antes do commit.
- **Estrategista:** Enfatizou que o processamento local de PDF é um fosso defensivo que aniquila a necessidade de Open Banking invasivo.
- **UX Designer:** Apresentou o **Modal HUD de Inspeção de Fatura** (`[F4]`), com pré-visualização, drag & drop e confirmação em 1 clique.
- **Arquiteto:** Fechou o design com relacionamento `OneToOne` entre a fatura e a despesa consolidada agendada.

### Rodada 3: Consenso & Exigências
- Zero dupla contagem garantida por separação de tabelas.
- Parser local de PDF tolerante com fallback editável na interface.
- Balanço mensal com exibição de Saldo Efetivado e Saldo Projetado.

---

## 4. ⚗️ Fase 2: Parecer e Score do Alquimista

- **Assimetria de Valor:** `9.4`
- **Singularidade:** `9.2`
- **Viabilidade e Custo:** `9.0`
- **Score Ponderado:** `9.3 / 10.0 (Ouro Puro)`

A proposta lapidada preserva a soberania local, unifica o fluxo temporal em qualquer mês e resolve o gerenciamento de faturas sem poluição contábil.

---

## 5. 🚀 Próximos Passos
1. Encaminhar para o `/architect` para estruturação do **ADR 007** e especificação formal das entidades.
2. Desenhar com o `/ux_designer` os componentes do Modal HUD de Fatura em ASCII.
3. Repassar ao `/doc_master` para sincronização do `ROADMAP.md` e `SPECs.md`.

