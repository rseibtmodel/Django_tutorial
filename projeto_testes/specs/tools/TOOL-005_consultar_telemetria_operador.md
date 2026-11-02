---
id: TOOL-005
titulo: Ferramenta de Consulta de Telemetria e Custos do Operador
modulo: tools
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-02
autores: [/doc_master, /architect, /coder]
---

# 📊 Ferramenta TOOL-005: `consultar_telemetria_operador`

- **Função Python:** `app_chatbot.tools.obter_ferramentas_para_sessao.<locals>.consultar_telemetria_operador`
- **Escopo:** Usuário Autenticado (Factory Closure)
- **Tipo de Execução:** Consulta agregada via `selectors.obter_metricas_telemetria_usuario`

---

## 1. 🎯 Finalidade Operacional
Permite ao assistente responder a perguntas do operador sobre consumo de tokens, cotas de IA, custos estimados em dólares (USD) e quantidade de conversas e documentos vinculados à sua conta.

---

## 2. 📝 Assinatura & Especificação Técnica

```python
def consultar_telemetria_operador() -> str:
    """Retorna as métricas de consumo de tokens e custos estimados do operador na aplicação.

    Returns:
        str: Resumo de métricas de telemetria do usuário.
    """
```

### Parâmetros de Entrada:
- *Nenhum parâmetro requerido.*

### Retorno:
- `str`: String formatada contendo total de conversas, total de mensagens, tokens acumulados, custo estimado em USD e quantidade de documentos RAG ativos.

---

## 3. 🛡️ Segurança & Anti-IDOR
- Se a sessão for anônima, a função retorna imediatamente aviso de indisponibilidade sem tocar em métricas alheias.
- Quando o usuário é autenticado, a consulta é restrita ao `sessao.usuario`.

---

## 4. 💬 Exemplo de Chamada pela IA
**Pergunta do Usuário:** *"Quanto eu já gastei de tokens no sistema até agora?"*  
**Ação do Modelo:** `FunctionCall: consultar_telemetria_operador()`  
**Resposta da Ferramenta:** `"Métricas do Operador @rodrigo:\n- Total de conversas: 8\n- Mensagens trocadas: 64\n- Tokens consumidos: 125,400\n- Custo financeiro estimado da API: $0.0376 USD\n- Documentos RAG ativos: 3"`  
**Síntese da IA:** *"Você já utilizou 125.400 tokens em 8 conversas, totalizando um custo estimado de aproximadamente $0.0376 USD na API do Gemini."*

