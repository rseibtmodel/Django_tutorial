# 🏛️ ADR 005: Modelagem de Personas Dinâmicas & Compilação Modular de Prompts

- **Status:** Aprovado & Implementado
- **Decisores:** Arquiteto de Software, Especialista em UX/UI, Estagiário Codificador
- **Data:** 02/11/2026

---

## 1. Contexto & Problema
Inicialmente, personas eram apenas opções estáticas em um `CharField(choices=...)` com instruções codificadas direto no Python. Para permitir que operadores criem agentes customizados com demografia, história de vida e diretrizes próprias, o modelo precisou se tornar dinâmico, exigindo um mecanismo de compilação para não estourar a atenção do modelo.

---

## 2. Decisão Arquitetural
1. **Entidade `Persona` Relacional:**
   - Criação da tabela `Persona` no SQLite.
   - Suporte a personas globais do sistema (`is_sistema=True`, protegidas contra deleção/edição) e personas customizadas do usuário (`usuario=request.user`).
   - Migração do campo `SessaoChat.persona` para `ForeignKey(Persona, on_delete=models.SET_NULL)`.
2. **Entidade `PerfilUsuario`:**
   - OneToOne com `User`, permitindo que o operador insira seu nome de exibição, profissão e foto.
3. **Compilador Estruturado (`Prompt Assembler`):**
   - Função pura `compilar_system_prompt_persona()` que sintetiza demografia, tom, história e perfil em blocos concisos e previsíveis, eliminando o risco de alucinação por instruções conflitantes.
4. **Armazenamento de Fotos com Zero Dependências:**
   - Utilização de `FileField` com validações manuais de extensão para evitar a obrigatoriedade da biblioteca `Pillow`.

---

## 3. Consequências & Trade-offs
- **Positivas:**
  - Flexibilidade total: qualquer usuário pode criar dezenas de agentes com personalidades distintas.
  - A IA passa a responder adaptada tanto à sua própria persona quanto à profissão do operador.
- **Negativas:**
  - Complexidade adicional no carregamento do System Prompt (busca da Persona e do Perfil no banco a cada request).

