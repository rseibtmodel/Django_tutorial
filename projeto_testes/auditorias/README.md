# Auditorias Forenses de Fricção, Abuso & Integridade

Esta pasta é o repositório oficial de laudos periciais e testes de estresse comportamental gerados pelo **Advogado do Diabo (`/critic` ou `/advogado`)**.

---

## 📋 Convenção de Nomenclatura dos Laudos

Os laudos salvos neste diretório devem seguir o padrão cronológico em `snake_case`:
```text
projeto_testes/auditorias/{YYMMDDNN}_laudo_{slug_do_tema}.md
```
*Exemplo:* `26110301_laudo_politica_descontos_chatbot.md`

---

## 🚦 Semáforo Padrão de Riscos

Todo laudo pericial catalogado utiliza a taxonomia forense:
- `🔴 VETOR DE FRAUDE`: Risco crítico de segurança, arbitragem de negócio ou vulnerabilidade em regras.
- `🟡 RESISTÊNCIA DO USUÁRIO`: Fricção humana severa, risco de abandono ou criação de Shadow IT.
- `🟢 LACUNA MENOR`: Detalhes secundários de consistência ou atrito leve de usabilidade.

---

## 🔄 Fluxo de Governança Multiagente

1. **Auditoria:** O `/critic` formula o laudo forense e salva o relatório nesta pasta.
2. **Catalogação:** O `/doc_master` lê o laudo e gera propostas de ação em `reviews/action/ACT-NNN_{slug}.md`.
3. **Decisão:** O `/architect` formaliza as contramedidas mandatórias em ADRs ou especificações técnicas.
4. **Implementação:** O `/coder` desenvolve as travas determinísticas no backend com testes automatizados.

