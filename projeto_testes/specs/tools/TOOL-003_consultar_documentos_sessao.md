---
id: TOOL-003
titulo: Ferramenta de Consulta de Documentos RAG da Sessão
modulo: tools
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-02
autores: [/doc_master, /architect, /coder]
---

# 📎 Ferramenta TOOL-003: `consultar_documentos_sessao`

- **Função Python:** `app_chatbot.tools.obter_ferramentas_para_sessao.<locals>.consultar_documentos_sessao`
- **Escopo:** Sessão Ativa (Factory Closure)
- **Tipo de Execução:** Consulta relacional via Django ORM

---

## 1. 🎯 Finalidade Operacional
Permite ao assistente inspecionar quais documentos foram anexados à conversa ativa pelo operador, seus tamanhos em KB e a quantidade de chunks vetorizados no ChromaDB, auxiliando o modelo a informar ao usuário se o contexto documental necessário está disponível.

---

## 2. 📝 Assinatura & Especificação Técnica

```python
def consultar_documentos_sessao() -> str:
    """Retorna a lista e o status de todos os documentos anexados para RAG nesta conversa.

    Returns:
        str: Relação estruturada de documentos disponíveis nesta sessão.
    """
```

### Parâmetros de Entrada:
- *Nenhum parâmetro requerido* (a sessão é injetada automaticamente via *closure*).

### Retorno:
- `str`: Lista formatada com os nomes originais dos arquivos, tamanho em KB e número de chunks, ou mensagem indicando ausência de anexos.

---

## 3. 🛡️ Segurança & Anti-IDOR
- A ferramenta é gerada dentro do escopo da sessão corrente (`obter_ferramentas_para_sessao(sessao)`).
- O modelo não recebe nem manipula IDs de banco de dados, impossibilitando qualquer ataque de enumeração de arquivos de outros usuários (*Insecure Direct Object Reference*).

---

## 4. 💬 Exemplo de Chamada pela IA
**Pergunta do Usuário:** *"Quais manuais eu enviei para você ler nesta conversa?"*  
**Ação do Modelo:** `FunctionCall: consultar_documentos_sessao()`  
**Resposta da Ferramenta:** `"Total de documentos indexados: 1\n- Arquivo: 'manual_arquitetura.txt' (1.2 KB, 8 chunks indexados)"`  
**Síntese da IA:** *"Nesta conversa, você anexou o arquivo `manual_arquitetura.txt`, que está indexado e dividido em 8 fragmentos de busca."*

