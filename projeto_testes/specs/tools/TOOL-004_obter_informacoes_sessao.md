---
id: TOOL-004
titulo: Ferramenta de Consulta de Metadados da Sessão Ativa
modulo: tools
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-02
autores: [/doc_master, /architect, /coder]
---

# 💬 Ferramenta TOOL-004: `obter_informacoes_sessao`

- **Função Python:** `app_chatbot.tools.obter_ferramentas_para_sessao.<locals>.obter_informacoes_sessao`
- **Escopo:** Sessão Ativa (Factory Closure)
- **Tipo de Execução:** Leitura relacional de metadados

---

## 1. 🎯 Finalidade Operacional
Fornece ao assistente visibilidade sobre os parâmetros da própria conversa: qual título está atribuído, qual a persona atualmente ativa, a data de criação e a quantidade total de turnos de mensagem registrados no histórico.

---

## 2. 📝 Assinatura & Especificação Técnica

```python
def obter_informacoes_sessao() -> str:
    """Retorna os metadados da sessão de chat ativa e da persona vinculada.

    Returns:
        str: Metadados consolidados da conversa.
    """
```

### Parâmetros de Entrada:
- *Nenhum parâmetro requerido.*

### Retorno:
- `str`: Texto estruturado com ID truncado, título, persona, data de criação e contagem de mensagens.

---

## 3. 🛡️ Segurança & Anti-IDOR
- Acessa estritamente os atributos da instância `sessao` previamente validada e autenticada no endpoint de streaming.

---

## 4. 💬 Exemplo de Chamada pela IA
**Pergunta do Usuário:** *"Qual persona você está usando agora e quantas mensagens já trocamos aqui?"*  
**Ação do Modelo:** `FunctionCall: obter_informacoes_sessao()`  
**Resposta da Ferramenta:** `"Sessão ID: a1b2c3d4\nTítulo: 'Debate de Arquitetura'\nPersona Ativa: Tech Lead Django\nCriada em: 02/11/2026 14:30\nTotal de turnos de mensagem registrados: 14"`  
**Síntese da IA:** *"Estamos na conversa 'Debate de Arquitetura' com a persona Tech Lead Django ativa, e já registramos 14 turnos de mensagem no histórico."*

