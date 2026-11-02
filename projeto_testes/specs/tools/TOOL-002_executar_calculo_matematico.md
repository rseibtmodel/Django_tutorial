---
id: TOOL-002
titulo: Ferramenta de Cálculo Matemático Seguro por AST
modulo: tools
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-02
autores: [/doc_master, /architect, /coder]
---

# 🔢 Ferramenta TOOL-002: `executar_calculo_matematico`

- **Função Python:** `app_chatbot.tools.executar_calculo_matematico`
- **Escopo:** Global
- **Mecanismo:** Analisador Sintático Seguro de Abstract Syntax Tree (`ast`)

---

## 1. 🎯 Finalidade Operacional
Modelos de linguagem sofrem com imprecisões severas ao multiplicar números decimais, realizar divisões compostas ou resolver contas financeiras complexas. Esta ferramenta executa cálculos aritméticos exatos garantindo **100% de blindagem contra ataques de injeção de código (RCE)**.

---

## 2. 📝 Assinatura & Especificação Técnica

```python
def executar_calculo_matematico(expressao: str) -> str:
    """Executa cálculos matemáticos de forma exata e segura via analisador sintático.

    Args:
        expressao: Fórmula ou expressão aritmética (ex: '((1500 * 0.85) + 320) / 4').

    Returns:
        str: Resultado numérico exato ou mensagem de erro explicativa.
    """
```

### Parâmetros de Entrada:
- `expressao` (`str`): String contendo a expressão aritmética (limite de 200 caracteres).

### Retorno:
- `str`: String contendo o resultado numérico exato ou mensagem de erro.

---

## 3. 🛡️ Blindagem de Segurança (Anti-RCE)
A função utiliza a função interna `avaliar_expressao_matematica_segura`, que:
1. Gera a árvore sintática através de `ast.parse(expressao, mode='eval')`.
2. Percorre todos os nós (`ast.walk`) e **aborta sumariamente** se encontrar:
   - Chamadas de função (`ast.Call`) como `__import__` ou `eval`.
   - Acesso a variáveis ou identificadores (`ast.Name`).
   - Acesso a propriedades ou métodos (`ast.Attribute`).
   - Imports (`ast.Import`, `ast.ImportFrom`), lambdas ou compreensões.
3. Permite apenas operadores seguros mapeados no dicionário `OPERADORES_ARITMETICOS`:
   - Adição (`+`), Subtração (`-`), Multiplicação (`*`), Divisão (`/`), Divisão Inteira (`//`), Módulo (`%`), Exponenciação (`**`).
4. Trava defensiva contra DoS por potência: expoentes maiores que 1000 são rejeitados.
5. Captura graciosa de `ZeroDivisionError` sem crash do processo.

---

## 4. 💬 Exemplo de Chamada pela IA
**Pergunta do Usuário:** *"Quanto é (450 * 12) + (1350 / 3)?"*  
**Ação do Modelo:** `FunctionCall: executar_calculo_matematico(expressao="(450 * 12) + (1350 / 3)")`  
**Resposta da Ferramenta:** `"Resultado do cálculo '(450 * 12) + (1350 / 3)': 5850"`  
**Síntese da IA:** *"O resultado da operação é 5.850."*

