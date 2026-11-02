# 🖥️ Módulo Externo: Central de Personas Customizadas

Este documento especifica a interface e a lógica de criação, edição e gerenciamento de Personas dinâmicas do chatbot.

---

## 1. Visão Geral
A Central de Personas (`/chat/personas/`) permite que o operador configure a personalidade, o nível de profundidade e o estilo de comunicação do assistente.

---

## 2. Abas de Funcionalidade (`personas.html`)

### 2.1 Galeria de Personas (`#galeria`)
- Apresenta cards visuais para cada persona acessível pelo operador:
  - **Presets Globais do Sistema (`is_sistema=True`):**
    1. *Assistente Geral (`padrao`):* Respostas balanceadas e claras.
    2. *Tech Lead Django (`coder`):* Clean Code, Two Scoops, type hints e boas práticas.
    3. *Arquiteto Socrático (`socratico`):* Thought Partner provocativo e questionador.
    4. *Executivo Conciso (`resumidor`):* Bullet points de no máximo 3 a 5 linhas.
  - **Personas Customizadas do Usuário (`is_sistema=False`):**
    Criadas pelo operador com foto, tags de idade, escolaridade e botões de `[Editar]` e `[Excluir]`.
- Botão direto `[USAR NO CHAT]` que redireciona para a conversa ativa com a persona selecionada.

### 2.2 Editor Split-Screen (`#editor`)
- **Coluna Esquerda (Live Preview Card):**
  Exibe em tempo real o card de identificação da persona conforme o usuário digita seu nome, cargo, idade e escolhe o tom de voz.
  Mostra o avatar com preview instantâneo da foto enviada via `FileReader` no JavaScript ou as iniciais do nome.
- **Coluna Direita (Formulário de Configuração):**
  - *Identidade:* Nome da persona, foto/avatar e resumo de 1 linha.
  - *Demografia:* Idade (0 a 150), gênero/identidade, nível de escolaridade e profissão/especialidade.
  - *Comportamento:* Tom de voz primário (objetivo, rigoroso, socrático, acadêmico, descontraído, empático, conciso).
  - *Histórico & Backstory:* A trajetória de vida do personagem que fornece bagagem contextual às respostas.
  - *Diretrizes de Comportamento:* Regras estritas do que fazer e do que evitar durante o chat.

---

## 3. Segurança & Proteção de Presets
- Personas do sistema possuem `is_sistema=True`. O backend rejeita tentativas de edição ou exclusão de presets do sistema com `PersonaInvalidaError`.
- Personas customizadas possuem `usuario=request.user`. Tentativas de editar ou excluir personas de outros usuários são barradas via `get_object_or_404(Persona, id=..., usuario=request.user)`.

