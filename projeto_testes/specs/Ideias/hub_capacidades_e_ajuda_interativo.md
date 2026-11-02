# 💡 Hub Interativo de Ajuda, Ferramentas & Habilidades do Modelo

- **Autor(es):** Arquiteto de Software & UX Designer
- **Data de Proposição:** 02/11/2026
- **Status da Ideia:** Aprovada para Roadmap (Fase 4)
- **Prioridade Estimada:** Alta
- **Spec de Ferramentas Relacionada:** [`specs/tools/README.md`](../tools/README.md)

---

## 1. 🎯 Declaração do Problema & Hipótese de Valor

- **Qual a dor atual do operador ou desenvolvedor?**
  Com a evolução do chatbot para um agente com *Tool Calling* (Function Calling), RAG e personas customizadas, o operador humano perde a visibilidade sobre **o que o modelo é capaz de fazer**. Comandos de terminal como `/docs` e `/tools` exigem memorização (violando a Heurística 6 de Nielsen - reconhecimento em vez de recordação), e não há uma forma visual de inspecionar quais ferramentas estão ativas, como funcionam e quais habilidades específicas cada Persona possui.

- **Qual a solução proposta?**
  Criação do **Hub Interativo de Ajuda e Habilidades (Capabilities & Help Modal)**, acessível tanto por atalho de teclado (`?` ou `F1`), comando `/ajuda`, ou por um botão dedicado no topo da interface do chat (`[?] Habilidades & Ajuda`). 
  O modal exibe um HUD em estilo Terminal Dark Cyber-Clean categorizado em 3 abas interativas:
  1. **🛠️ Ferramentas da IA:** Lista as tools ativas (`obter_data_e_hora_oficial`, `executar_calculo_matematico`, etc.), o que cada uma faz, exemplos de perguntas que as acionam e seu status de segurança.
  2. **⌨️ Comandos do Terminal:** Comandos slash disponíveis (`/persona`, `/tools`, `/docs`, `/status`, `/limpar`, `/ajuda`) com botão de clique rápido para inseri-los no input.
  3. **🎭 Habilidades das Personas:** Mapeamento visual das personas disponíveis, suas especialidades técnicas, estilo de comunicação e tom de voz.

- **Qual o ganho prático?**
  Acelera em 100% o *onboarding* de novos operadores, elimina erros de digitação em comandos slash, torna transparente a auditoria das capacidades de IA e dá previsibilidade operacional ao usuário.

---

## 2. 🏛️ Impacto Arquitetural Previsto (/architect)

> **Parecer do Arquiteto:**  
> A exposição dos metadados das ferramentas e comandos deve ser desacoplada da execução pesada da IA para garantir renderização instantânea (latência zero no frontend).
>
> **Diretrizes Arquiteturais:**
> 1. *Camada `selectors.py`:* Criar a função `obter_catalogo_capacidades_sistema(sessao, usuario) -> dict[str, Any]` que agrega os metadados de `tools.py`, os comandos do terminal e as personas cadastradas.
> 2. *Estratégia de Renderização:* Injetar esses metadados estruturados diretamente no contexto de `painel_chat` (`context["capacidades"]`) para renderização server-side via Django templates com Bootstrap 5 modal nativo, evitando round-trips HTTP desnecessários.
> 3. *Zero Dependências:* Utilizar estritamente o Bootstrap 5 Dark nativo e vanilla JavaScript já presentes no projeto.

- **Novos Modelos de Dados necessários:**
  Nenhum. A funcionalidade consome os modelos existentes (`Persona`, `DocumentoSessao`, `SessaoChat`) e o catálogo estático/dinâmico de `tools.py`.
- **Alterações em `services.py` e `selectors.py`:**
  - `selectors.py`: `obter_catalogo_capacidades_sistema(sessao, usuario)`.
  - `views.py`: Envio de `capacidades` no contexto de `painel_chat`.
- **Dependências Externas requeridas:**
  Zero novas dependências pip ou npm.
- **Riscos Técnicos & Pontos Cegos:**
  Risco de vazar metadados de documentos de outras sessões caso a consulta não respeite o isolamento da sessão ativa. O seletor deve receber a instância de `sessao` previamente autenticada.

---

## 3. 🎨 Esboço de UX/UI & Ergonomia de Uso (/ux_designer)

> **Parecer do UX Designer:**  
> A usabilidade deve honrar as 10 Heurísticas de Nielsen:
> - **Heurística 6 (Reconhecimento em vez de Recordação):** O operador clica no comando desejado dentro do modal e ele é automaticamente colado no prompt de comando.
> - **Heurística 10 (Ajuda e Documentação):** Explicações concisas de cada ferramenta em linguagem humana e clara.
> - **Estética Cyber-Clean:** Modal escuro (`#0a0e14`), bordas verde neon translúcidas (`rgba(0, 255, 102, 0.25)`), fontes monoespaçadas e badges de status.

### Acesso:
- Botão no cabeçalho: `[?] HABILIDADES & AJUDA`
- Atalho de teclado global: Tecla `?` ou `F1` (quando o foco não estiver em um input de texto)
- Comando de chat: `/ajuda` ou `/help`

### Esboço em ASCII da Interface (Modal Flutuante):

```text
┌────────────────────────────────────────────────────────────────────────┐
│  [?] HUB DE HABILIDADES, FERRAMENTAS & AJUDA DO ASSISTENTE       [ESC] │
├────────────────────────────────────────────────────────────────────────┤
│  [ 🛠️ FERRAMENTAS (5) ]   [ ⌨️ COMANDOS (6) ]   [ 🎭 PERSONAS (4) ]     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  🛠️ FERRAMENTAS EXECUTÁVEIS ATIVAS (GEMINI FUNCTION CALLING):          │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ ⏱️  obter_data_e_hora_oficial                        [GLOBAL]    │  │
│  │    Informa a data, hora e fuso horário oficial de Brasília.      │  │
│  │    Ex: "Que horas são agora?" ou "Qual a data de hoje?"          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 🔢  executar_calculo_matematico                      [AST SEGURA]│  │
│  │    Calculadora de alta precisão imune a alucinações matemáticas. │  │
│  │    Ex: "Calcule (1500 * 0.85) + 320"                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 📎  consultar_documentos_sessao                      [SESSÃO RAG]│  │
│  │    Inspeciona arquivos indexados na conversa ativa.              │  │
│  │    Ex: "Quais arquivos você tem acesso nesta sessão?"            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 📊  consultar_telemetria_operador                    [USUÁRIO]   │  │
│  │    Exibe consumo de tokens e custos estimados em USD do operador.│  │
│  │    Ex: "Quantos tokens já consumi hoje?"                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  Dica: Pressione [ESC] ou clique fora para retornar ao terminal.       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 🧭 Critérios de Aceite para Entrega

- [ ] Criar seletor `obter_catalogo_capacidades_sistema` em `selectors.py` centralizando metadados de tools, comandos e personas.
- [ ] Implementar o modal Bootstrap 5 no template `chat.html` com estética Terminal Dark e abas interativas.
- [ ] Implementar atalho de teclado `?` / `F1` e botão no cabeçalho do chat.
- [ ] Permitir que o clique em um comando slash o copie diretamente para o campo de digitação do chat.
- [ ] Cobrir com testes automatizados em `tests.py` validando o seletor e a presença dos elementos no HTML.
- [ ] Arquivar esta ideia em `specs/Ideias/arquivadas/` e consolidar a spec definitiva em `specs/modulos_externos/hub_capacidades_e_ajuda.md` após implementação.

