# Regras do Construtor de Agentes (Agent Builder)

Sempre que o usuário solicitar a **criação, desenvolvimento, ideação ou especificação de um novo agente**, você DEVE OBRIGATORIAMENTE utilizar o fluxo de entrevista guiada da skill `agent_builder`.

## Diretrizes Inegociáveis:
1. **Nunca crie o agente diretamente sem entrevista prévia:**
   - Mesmo que o usuário forneça uma descrição inicial, atue como o **Orquestrador / Agente Triador** e pergunte:
     1. O objetivo detalhado do agente a ser criado.
     2. Quantas perguntas ele gostaria de responder para calibrar o agente.
2. **Formato das perguntas (Fase 2):**
   - Agrupe por especialistas temáticos coerentes.
   - Cada pergunta DEVE conter: **O que influencia** e **Exemplos de respostas com seus respectivos impactos**.
3. **Fase de Síntese antes da geração final (Fase 3):**
   - Resuma os requisitos acordados e peça validação do usuário antes de escrever o prompt final.
4. **Entrega Final (Fase 4):**
   - Entregue o prompt de produção estruturado e, quando aplicável, gere os arquivos correspondentes em `.agents/skills/<nome>/SKILL.md` ou `.agents/rules/<nome>.md`.

