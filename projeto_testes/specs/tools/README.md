---
id: SPEC-TOOLS-INDEX
titulo: Inventário Central de Ferramentas de IA (Function Calling)
modulo: tools
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-02
autores: [/doc_master, /architect, /coder]
---

# 🛠️ Central de Ferramentas de IA (`specs/tools/`)

Este diretório armazena o catálogo oficial, as especificações técnicas e as diretrizes de segurança de todas as **ferramentas executáveis (*Tools / Function Calling*)** disponibilizadas para os modelos de Inteligência Artificial no ecossistema Django.

---

## 📌 Padrão de Nomenclatura e Governança

Toda ferramenta implementada no módulo [`app_chatbot/tools.py`](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/tools.py) DEVE possuir uma especificação dedicada neste diretório seguindo a taxonomia:
- **Formato:** `TOOL-{NNN}_{slug_da_funcao}.md`
- **Frontmatter Obrigatório:** `id`, `titulo`, `modulo: tools`, `versao`, `status`, `ultima_atualizacao`, `autores`.
- **Seções Mínimas:** Finalidade operacional, Assinatura Python tipada, Parâmetros, Retorno, Protocolo de Segurança (Blindagem anti-RCE e anti-SQL) e Exemplo de Interação.

---

## 📋 Catálogo Geral de Ferramentas Ativas

| ID | Ferramenta Python | Finalidade | Escopo | Segurança |
| :--- | :--- | :--- | :--- | :--- |
| [**TOOL-001**](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/specs/tools/TOOL-001_obter_data_e_hora_oficial.md) | `obter_data_e_hora_oficial` | Fornece data, hora e dia da semana oficial no fuso `America/Sao_Paulo` | Global | Leitura de relógio do SO |
| [**TOOL-002**](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/specs/tools/TOOL-002_executar_calculo_matematico.md) | `executar_calculo_matematico` | Avalia expressões matemáticas aritméticas complexas com precisão | Global | AST pura (sem `eval`/`exec`) |
| [**TOOL-003**](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/specs/tools/TOOL-003_consultar_documentos_sessao.md) | `consultar_documentos_sessao` | Lista os documentos e contagem de chunks indexados para RAG na sessão | Sessão Ativa | Isolamento anti-IDOR |
| [**TOOL-004**](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/specs/tools/TOOL-004_obter_informacoes_sessao.md) | `obter_informacoes_sessao` | Metadados da conversa ativa (título, persona ativa e contagem de turnos) | Sessão Ativa | Isolamento anti-IDOR |
| [**TOOL-005**](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/specs/tools/TOOL-005_consultar_telemetria_operador.md) | `consultar_telemetria_operador` | Métricas agregadas de consumo de tokens e estimativas de custo financeiro em USD | Usuário Autenticado | Trava multi-tenant de usuário |

---

## 🔒 Princípios Inegociáveis de Segurança das Tools

1. **Zero Código Arbitrário (Anti-RCE):** Jamais expor interpretadores Python livres, `eval()`, `exec()` ou importação dinâmica de bibliotecas para os modelos.
2. **Zero Injeção de SQL:** Nenhuma ferramenta aceita queries SQL livres vindas do modelo. Toda persistência passa pelo ORM do Django.
3. **Isolamento de Tenant (Anti-IDOR):** Ferramentas contextuais utilizam factories com *closures* no Python (`obter_ferramentas_para_sessao(sessao)`), garantindo que o modelo nunca consiga forjar ou passar IDs de outros operadores.

