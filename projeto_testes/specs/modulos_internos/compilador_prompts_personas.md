# ⚙️ Módulo Interno: Compilador de Prompts de Personas (`Prompt Assembler`)

Este documento detalha o algoritmo que converte a ficha cadastral da Persona e o Perfil do Operador em uma instrução de sistema (`system_instruction`) concisa, coerente e com alta aderência comportamental.

---

## 1. O Desafio da Engenharia de Prompts
Quando permitimos que o usuário defina idade, escolaridade, histórico de vida, tom de voz e diretrizes livres, o risco de **diluição de atenção** (*attention sink*) é imenso. Se a instrução for confusa, prolixa ou contraditória, o LLM ignora as regras e volta ao tom genérico padrão.

O **Compilador de Prompts** (`compilar_system_prompt_persona`) atua como uma esteira de síntese hierárquica que organiza o prompt em blocos modulares.

---

## 2. Estrutura dos Blocos Compilados

```text
[BLOCO 1: IDENTIDADE & PAPEL]
- Nome do Personagem
- Ocupação / Especialidade
- Tom de Voz Prevalente
- Resumo de Papel (1 linha)

[BLOCO 2: PERFIL DEMOGRÁFICO]
- Idade aparente (ex: 45 anos)
- Identidade de Gênero (se definida)
- Formação Acadêmica (ex: Doutorado)

[BLOCO 3: HISTÓRICO & BACKSTORY]
- Narrativa de vida do personagem que dá ancoragem emocional e intelectual

[BLOCO 4: DIRETRIZES DE COMPORTAMENTO]
- Regras explícitas do que fazer e do que não fazer nas respostas

[BLOCO 5: PERFIL DO INTERLOCUTOR (OPERADOR)]
- Nome do usuário logado
- Profissão e Bio do operador para calibrar o vocabulário e a profundidade

[BLOCO 6: DIRETRIZES DE EXECUÇÃO]
- Manutenção do personagem
- Uso de português do Brasil
- Prioridade para documentos RAG anexados
```

---

## 3. Implementação Técnica
Localizado em `app_chatbot/services.py`:
- Função pura: `compilar_system_prompt_persona(*, persona: Persona, perfil_usuario: Optional[PerfilUsuario] = None) -> str`.
- Sanitização: Todo texto livre passa por `strip_tags()` antes da persistência para garantir que injeções de prompt ou tags HTML não corrompam a estrutura.
- Fallback: Se a sessão não tiver persona associada, o sistema invoca automaticamente a persona padrão (`obter_persona_padrao()`).

