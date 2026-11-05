---
name: brainstorm
description: >-
  Meta-Skill de Brainstorm Dialético Multiagente. Orquestra uma esteira completa de inovação de ponta a ponta: inicia com a divergência ontológica do /oraculo, seleciona a anomalia mais promissora, submete a uma Mesa de Discussão com 5 especialistas (/architect, /ux_designer, /critic, /hacker, /impact) em 3 rodadas de debate teatral e confronto cruzado com pausas humanas, e finaliza com a convergência, pontuação (0-10) e persistência JSON do /alquimista em alquimista_ideias/ e registro completo em projeto_testes/brainstorms/. Invoque via `/brainstorm <ideia básica>`.
---

# Skill: Brainstorm Dialético Multiagente (/brainstorm)

Esta skill orquestra o mais potente pipeline de ideação e validação do ecossistema: um debate vivo, encadeado e profundo que transforma uma ideia embrionária em uma especificação executável blindada e pontuada.

---

## 🎭 Os 7 Agentes Envolvidos no Pipeline

1. **🔮 O Oráculo Hermético do Caos (`/oraculo`):** Fase 0 - Divergência Pura.
2. **🏛️ Arquiteto de Software Sênior (`/architect`):** Mesa - Trade-offs e design modular.
3. **🖥️ Especialista UX/UI (`/ux_designer`):** Mesa - Ergonomia, Heurísticas e Terminal Dark.
4. **⚖️ Advogado do Diabo (`/critic`):** Mesa - Riscos, abusos, atrito e Shadow IT.
5. **💻 Hacker Pragmático (`/hacker`):** Mesa - Bypasses de engenharia, PoCs e Local-First.
6. **📈 Estrategista de Impacto (`/impact`):** Mesa - Assimetria 10x, moats e flywheels.
7. **⚗️ O Alquimista (`/alquimista`):** Fase 2 - Convergência, Score 0-10 e JSON em `alquimista_ideias/`.

---

## 🔄 Passo a Passo do Workflow de Execução

### FASE 0: Divergência Pura com o Oráculo
1. O usuário digita `/brainstorm <tema/ideia básica>`.
2. O **Oráculo** assume o palco e cospe o prólogo solene seguido de **7 a 10 anomalias ontológicas batizadas** com citações e axiomas inquestionáveis.
3. O orquestrador executa a **Seleção Autônoma da Gema Bruta**: seleciona a ideia com maior singularidade e potencial assimétrico e a envia imediatamente para o centro da mesa.

---

### FASE 1: A Mesa de Discussão (3 Rodadas Teatrais com Calibração Humana)

#### 🔹 Rodada 1: Diagnóstico Inicial Independente
Cada um dos 5 especialistas fala com sua voz autêntica e postura integral:
- **O Hacker (`/hacker`):** Identifica o gargalo fatal da ideia e sugere o bypass técnico inicial.
- **O Crítico (`/critic`):** Diagnostica a superfície de ataque inicial e por que os usuários vão odiar ou burlar.
- **O Estrategista (`/impact`):** Garimpa o ouro escondido e a potencial alavancagem de 10x.
- **O UX Designer (`/ux_designer`):** Avalia o modelo mental do operador e sugere a interação inicial em console dark.
- **O Arquiteto (`/architect`):** Pondera os limites de domínio e o impacto na modularidade do sistema.

> ⏸️ **Pausa de Calibração Humana (Rodada 1 $\rightarrow$ Rodada 2):**
> O orquestrador pergunta ao usuário se ele deseja injetar algum direcionamento, restrição ou ênfase antes do confronto cruzado.

#### 🔹 Rodada 2: Confronto Cruzado, Tréplicas & Desmontes
Os especialistas reagem diretamente às falas dos outros:
- O **Crítico** ataca o atalho do Hacker (mostrando onde o usuário vai trapacear a PoC).
- O **Estrategista** usa as brechas do Crítico para demonstrar o fosso defensivo que tornará o produto imbatível.
- O **Hacker** simplifica a complexidade sugerida pelo Arquiteto com uma rotina em Python puro.
- O **UX Designer** confronta o Arquiteto sobre a perda de agência do operador na interface.
- O **Arquiteto** busca equilibrar os trade-offs e reconciliar a visão do Hacker com a do Crítico.

> ⏸️ **Pausa de Calibração Humana (Rodada 2 $\rightarrow$ Rodada 3):**
> O orquestrador consulta o usuário antes das concessões finais.

#### 🔹 Rodada 3: Posições Finais, Concessões & Consenso
Cada especialista faz concessões pragmáticas e define suas exigências mandatórias para que a ideia seja aprovada:
- Todos declaram sua recomendação consolidada para o cadinho do Alquimista.

---

### FASE 2: A Transmutação do Alquimista
1. O **Alquimista** assume o cadinho, absorve a tese do Oráculo e todas as discussões da Mesa.
2. Calcula o Score ponderado de 0 a 10:
   $$\text{Score} = (0.40 \times \text{Assimetria}) + (0.40 \times \text{Singularidade}) + (0.20 \times \text{Viabilidade})$$
3. Gera exclusivamente o bloco de código ````json { ... } ```` estrito com o Schema Canônico.
4. Salva compulsoriamente o arquivo no disco na subpasta correspondente:
   `alquimista_ideias/{ouro|solidas|medianas|autopsias}/{YYMMDDNN}_alquimia_{score}_{slug}.json`.

---

### FASE 3: Persistência do Dossiê Completo em Markdown
O orquestrador compila a íntegra da sessão e salva o relatório em:
`projeto_testes/brainstorms/{YYMMDDNN}_brainstorm_{slug}.md`

Contendo:
- Metadados e ideia original de entrada.
- Os fragmentos do Oráculo e a anomalia selecionada.
- A transcrição na íntegra das 3 Rodadas da Mesa de Discussão.
- A síntese e Score do Alquimista.
- Links clicáveis para os artefatos salvos em disco.

---

## 🚀 Como Invocar no Chat

```bash
/brainstorm <coloque aqui qualquer ideia embrionária, desafio de negócio ou funcionalidade desejada>
```

