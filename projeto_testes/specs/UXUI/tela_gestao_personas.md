# 🎨 UX/UI: Tela de Gestão de Personas & Perfil (`personas.html`)

Este documento detalha a experiência de usuário na central de gerenciamento de personas customizadas e perfil do operador.

---

## 1. Esboço Geral da Tela (Wireframe em ASCII)

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ >_ WORKSPACE // GERENCIADOR DE PERSONAS & PERFIL               [< Voltar ao Chat] [Sair]│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [🎭 MINHAS PERSONAS (4)]    [➕ CRIAR NOVA PERSONA]    [👤 MEU PERFIL DE OPERADOR]      │
├──────────────────────────┬─────────────────────────────────────────────────────────────┤
│ PREVIEW DO AGENTE (Live) │ FORMULÁRIO DE CONFIGURAÇÃO DA PERSONA                       │
│                          │                                                             │
│ ┌──────────────────────┐ │ 1. DADOS DE IDENTIDADE                                      │
│ │      [ FOTO ]        │ │ Nome da Persona:  [ Dra. Helena Rocha                     ] │
│ │     [ 120x120 ]      │ │ Descrição Curta:  [ Especialista em Bioética e IA         ] │
│ │  [Carregar Imagem]   │ │ Foto/Avatar:      [ Escolher arquivo... (png/jpg máx 2MB) ] │
│ └──────────────────────┘ │                                                             │
│                          │ 2. PERFIL DEMOGRÁFICO & FORMAÇÃO                            │
│ Nome: Dra. Helena Rocha  │ Idade: [ 45 ]  Sexo: [ Feminino ▾ ]  Escolaridade: [ Doutorado ▾ ] │
│ Cargo: Especialista IA   │ Profissão/Especialidade: [ Pesquisadora Sênior            ] │
│ Escolaridade: Doutorado  │                                                             │
│ Tom: [Acadêmico/Crítico] │ 3. PERSONALIDADE & TOM DE VOZ                               │
│                          │ Tom de Voz: [ Acadêmico & Científico ▾ ]                    │
│ "A ética não é um detalhe│                                                             │
│ técnico, mas o alicerce."│ 4. HISTÓRICO & BACKSTORY (História de Vida)                 │
│                          │ ┌─────────────────────────────────────────────────────────┐ │
│ [ Status: Ativo ● ]      │ │ Formada pela USP com pós-doc em Oxford...               │ │
│                          │ └─────────────────────────────────────────────────────────┘ │
│                          │ 5. DIRETRIZES DE COMPORTAMENTO (System Prompt)              │
│                          │ ┌─────────────────────────────────────────────────────────┐ │
│                          │ │ Sempre questione o viés estatístico de cada solução...  │ │
│                          │ └─────────────────────────────────────────────────────────┘ │
│                          │                                                             │
│                          │ [💾 SALVAR PERSONA]                           [CANCELAR]    │
└──────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 2. Abas e Interações

### 2.1 Aba 1: Galeria de Personas
- Grid responsivo de cards em Bootstrap Dark (`col-md-6 col-lg-4`).
- Cada card contém:
  - Avatar circular de 72px com borda neon.
  - Badges de demografia (`[45 anos]`, `[Doutorado]`, `[SISTEMA]` ou `[CUSTOM]`).
  - Resumo de 1 linha.
  - Botão `[USAR NO CHAT]` que abre o chat com a persona vinculada.
  - Ações de `[EDITAR]` e `[EXCLUIR]` (disponíveis apenas para personas customizadas do usuário).

### 2.2 Aba 2: Editor Split-Screen com Live Preview
- **Coluna da Esquerda (Sticky):**
  - Card de preview de 120px que responde instantaneamente aos eventos de digitação (`input`, `change`) dos campos de formulário.
  - Se o usuário selecionar um arquivo de foto, um leitor assíncrono via `FileReader` substitui as iniciais pelo preview da imagem real antes de salvar.
- **Coluna da Direita:**
  - Formulário categorizado em 3 blocos lógicos: Identidade, Demografia e Comportamento/Backstory.
  - Botão de submissão neon `[💾 SALVAR PERSONA]`.

### 2.3 Aba 3: Perfil do Operador
- Upload de foto pessoal de 120px com recorte circular.
- Inputs para Nome de Exibição, Cargo, Data de Nascimento e Bio de contexto.

