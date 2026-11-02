# 🎨 UX/UI: Diretrizes Visuais & Estética Terminal Dark

Este guia consolida os princípios de design, paleta de cores, tipografia e heurísticas de usabilidade que regem todas as interfaces do ecossistema.

---

## 1. Princípios Fundamentais de Design

1. **Estética Cyber-Clean / Terminal Operacional:**
   - Evitar ruídos visuais decorativos desnecessários.
   - Cada pixel na tela deve servir à informação ou à ação rápida.
   - Inspiração em consoles de comando (CLI), interfaces de monitoramento e IDEs modernas.
2. **Alta Densidade de Informação:**
   - Aproveitamento inteligente do espaço com margens e paddings contidos (`p-2`, `p-3`).
   - Tabelas e listas compactas com rolagem interna preservando os cabeçalhos.
3. **Consistência em Neon Funcional:**
   - O verde neon nunca é usado como cor de fundo geral; é reservado estritamente para status ativos, ações principais de envio e realces de foco.

---

## 2. Paleta de Cores e Tokens Visuais

| Token | Código Hexadecimal | Aplicação Principal |
| :--- | :--- | :--- |
| **Deep Space** | `#06090e` | Fundo principal da página (`body`) |
| **Console Panel** | `#0d1117` | Fundo do painel do terminal e cards |
| **Dark Sub-panel** | `#090d13` | Fundo de sidebars, inputs e gavetas retráteis |
| **Neon Accent** | `#00ff66` | Botões de ação primária, bordas ativas, status dots |
| **Neon Hover** | `#00cc52` | Estado de foco e hover em botões primários |
| **Muted Grey** | `#8b949e` | Textos secundários, bordas sutis e ícones inativos |
| **Terminal White** | `#f0f6fc` | Texto das mensagens do usuário |
| **Alert Red** | `#ff4d4f` | Botões de exclusão e mensagens de erro |

---

## 3. Tipografia
- **Famílias Monoespaçadas Prioritárias:**  
  `'SF Mono', 'Fira Code', 'Cascadia Code', monospace`
- **Escala de Tamanhos:**
  - Títulos de painel: `0.90rem` / `0.95rem` (peso 700).
  - Texto de mensagens: `0.88rem` com `line-height: 1.55`.
  - Badges e legendas técnicas: `0.70rem` / `0.75rem`.

---

## 4. Aplicação das 10 Heurísticas de Nielsen
- **Heurística 1 (Visibilidade do Status):** Indicadores `status-dot` piscantes e badges de UUID/modelo.
- **Heurística 3 (Controle do Usuário):** Cancelamento de ações com tecla `Esc` e confirmação antes de deleções destrutivas.
- **Heurística 7 (Eficiência e Flexibilidade):** Atalhos de teclado como `/` para foco no prompt, comandos slash e botões de atalho rápido (*quick chips*).

