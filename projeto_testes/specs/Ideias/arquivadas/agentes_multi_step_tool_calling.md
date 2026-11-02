# 💡 Ideia: Agentes Multi-Step com Tool Calling (Function Calling)

- **Autor(es):** Arquiteto de Software
- **Data:** 02/11/2026
- **Status:** Implementada & Arquivada (Fase 4)
- **Data de Conclusão:** 02/11/2026
- **Spec Oficial Consolidada:** [`specs/modulos_internos/agentes_multi_step_tool_calling.md`](../modulos_internos/agentes_multi_step_tool_calling.md)

---

## 1. 🎯 Declaração do Problema
O assistente atual é conversacional e ancorado em RAG. No entanto, ele não consegue executar ações reais no ambiente (como rodar um comando SQL no banco do Django, testar um trecho de código Python ou consultar uma API externa de cotações).

---

## 2. 🏛️ Arquitetura Proposta
- **Suporte a Tools do Gemini (`tools=[...]` no SDK):**
  Definir funções Python decoradas com schemas tipados (via Pydantic ou type hints):
  - `consultar_tabelas_banco()`
  - `executar_calculo_cientifico()`
  - `buscar_na_web()`
- **Loop de Execução de Ferramentas:**
  Quando o modelo devolve um `function_call`, o backend Django executa a função de domínio e envia o `function_response` de volta ao modelo para síntese final.

