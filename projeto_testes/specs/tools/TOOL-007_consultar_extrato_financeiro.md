---
id: TOOL-007
titulo: Consulta Analítica de Extrato e Balanço Financeiro
modulo: tools
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-04
autores: [/doc_master, /architect, /coder]
---

# 🛠️ TOOL-007: `consultar_extrato_financeiro`

## 1. 🎯 Finalidade Operacional
Permite ao assistente de IA consultar o saldo líquido, total de receitas, total de despesas, taxa de poupança percentual e a lista das transações mais recentes do operador em uma competência mensal específica, permitindo aconselhamento financeiro socrático seguro.

---

## 2. 🐍 Assinatura Python
```python
def consultar_extrato_financeiro(
    ano: int = 0,
    mes: int = 0,
    categoria: str = "",
) -> str
```

---

## 3. 📋 Parâmetros & Tipos

| Parâmetro | Tipo | Obrigatório | Descrição |
| :--- | :--- | :--- | :--- |
| `ano` | `int` | Não | Ano de competência contábil (ex: `2026`). Se `0`, assume o ano corrente. |
| `mes` | `int` | Não | Mês de competência (1 a 12). Se `0`, assume o mês corrente. |
| `categoria` | `str` | Não | Filtro opcional por slug de categoria (ex: `'alimentacao'`, `'projetos'`). |

---

## 4. 🔒 Protocolo de Segurança & Performance
- **Leitura Pura (CQRS):** Consulta estritamente somente-leitura através da camada `selectors.py`.
- **Soft Delete Ativo:** Filtra compulsoriamente `ativo=True`, ocultando lançamentos cancelados.
- **Agregação SQL Nativada:** Agregação direta no SQLite via `Sum(...)` sem trazer linhas redundantes para a memória.

