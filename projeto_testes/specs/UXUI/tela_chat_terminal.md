# 🎨 UX/UI: Tela do Chat Terminal (`chat.html`)

Este documento detalha os componentes visuais, ergonomia de uso e micro-interações da tela principal de conversação.

---

## 1. Esboço Geral da Tela (Wireframe em ASCII)

```text
┌───────────────────────────┬────────────────────────────────────────────────────────────────────────┐
│ >_ SESSÕES         [12]   │ > Projeto Django API ✏️   [🎭 Dra. Helena ▾] [📎 DOCS (1)] [⚙️ PERSONAS]│
├───────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ [🔍 filtrar sessões...]   │ ┌── [GAVETA RAG DE DOCUMENTOS RETRÁTIL] ─────────────────────────────┐ │
│                           │ │ Arquivo: 📄 manual.pdf (1.2 MB) [14 chunks]                [Remover]│ │
│ > Projeto Django API  [X] │ │ [+ Anexar Documento (.pdf, .txt, .md - máx 5MB)]          [ANEXAR] │ │
│   Refatoração Auth    [X] │ └────────────────────────────────────────────────────────────────────┘ │
│   Setup ChromaDB      [X] │                                                                        │
│                           │                                                        ┌─────────────┐ │
│                           │                       Qual a função do compilador?     │ (Foto User) │ │
│                           │                                                        │   rodrigo   │ │
│                           │ ┌─────────────┐                                        └─────────────┘ │
│                           │ │ (Foto Doc)  │ > Dra. Helena Rocha [Pesquisadora]:                    │
│                           │ │   Helena    │ O compilador sintetiza a demografia, tom e história em │
│                           │ └─────────────┘ uma instrução modular concisa para o Gemini...         │
├───────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ [➕ NOVA SESSÃO]          │ [/status] [/docs] [/persona coder] [/persona socratico] [+ Criar]      │
│ (Avatar) rodrigo   [Sair] │ [ Digite sua mensagem para a Dra. Helena Rocha... (/ para focar) ] [->]│
└───────────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento dos Componentes

### 2.1 Barra Lateral (Sidebar Esquerda)
- **Header:** Contador numérico de sessões ativas do usuário e status dot verde neon.
- **Ação Principal:** Botão neon `[+ NOVA SESSÃO]`.
- **Filtro em Tempo Real:** Input que esconde/exibe sessões conforme o operador digita, com zero recarregamento de página.
- **Lista de Conversas:** Itens truncados com indicação de conversa ativa (`.active`), link direto e botão de exclusão `[X]` com mini-form POST.
- **Rodapé:** Avatar circular de 26px do operador com nome de exibição e botão de logout `[Sair]`.

### 2.2 Cabeçalho da Área Principal
- **Título In-Place Edit:** Título da sessão com suporte a duplo clique ou botão `✏️` para renomeação rápida sem sair do chat.
- **Seletor de Persona Dinâmico:** Dropdown estilizado que comuta a persona ativa na hora via `fetch()`.
- **Botão `[📎 DOCS (N)]`:** Expande ou recolhe a gaveta de documentos RAG.
- **Botão `[⚙️ PERSONAS]`:** Atalho de um clique para a tela de gestão e criação de personas.

### 2.3 Área de Mensagens (Avatares Duplos)
- **Turnos do Usuário:** Bolha escura alinhada à direita, ladeada pelo avatar circular do usuário (ou iniciais).
- **Turnos do Assistente:** Bolha com borda verde neon alinhada à esquerda, ladeada pelo avatar da persona ativa, encimada pelo nome e especialidade do personagem.
- **Cursor Streaming:** Efeito de digitação em tempo real com cursor piscante `.cursor-blink`.

### 2.4 Barra de Envio e Atalhos
- **Chips de Ação Rápida:** Botões para `/status`, `/docs`, `/persona coder`, `/persona socratico` e link direto para criar personas.
- **Atalho Global `/`:** Pressionar `/` em qualquer lugar da tela foca no campo de digitação imediatamente.

