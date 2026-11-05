---
id: TOOL-006
titulo: Registro Determinístico de Transações Financeiras
modulo: tools
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-04
autores: [/doc_master, /architect, /coder]
---

# 🛠️ TOOL-006: `registrar_transacao_financeira`

## 1. 🎯 Finalidade Operacional
Permite que o assistente de IA registre transações contábeis de receitas (créditos) e despesas (débitos) no banco de dados local do operador de forma atômica e determinística, eliminando riscos de alucinação contábil ou injeções de dados.

---

## 2. 🐍 Assinatura Python
```python
def registrar_transacao_financeira(
    tipo: str,
    valor: str,
    descricao: str,
    categoria: str = "outros",
    data_competencia: str = "",
) -> str
```

---

## 3. 📋 Parâmetros & Tipos

| Parâmetro | Tipo | Obrigatório | Descrição |
| :--- | :--- | :--- | :--- |
| `tipo` | `str` | Sim | `'DESPESA'` para saídas ou `'RECEITA'` para entradas. |
| `valor` | `str` | Sim | Valor monetário como texto (ex: `'45.00'`, `'150,50'`). Sanitizado para `Decimal(0.01)`. |
| `descricao` | `str` | Sim | Resumo textual da transação (máx 255 caracteres). |
| `categoria` | `str` | Não | Categoria normalizada em minúsculas (default: `'outros'`). |
| `data_competencia` | `str` | Não | Data contábil em formato ISO (`AAAA-MM-DD`). Se omitida, usa a data atual. |

---

## 4. 🔒 Protocolo de Segurança & Isolamento Anti-IDOR
- **Tenant Seguro:** A tool opera em uma closure capturando `sessao.usuario`. O modelo de IA não possui parâmetros para indicar IDs de outros usuários.
- **Sanitização Decimal:** O backend rejeita montantes $\le 0$ ou formatações ilegíveis através de `sanitizar_e_validar_valor()`.
- **Transação Atômica:** Mutação envolvida em `@transaction.atomic`.

