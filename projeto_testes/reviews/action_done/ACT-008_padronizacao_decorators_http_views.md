---
id: ACT-008
titulo: Padronização de Decorators Nativos de Verbos HTTP nas Views
modulo: app_chatbot
relacionado_review: REV-0003
data_criacao: 2026-11-02
status: concluido
data_conclusao: 2026-11-02
autores: [/review, /architect, /doc_master]
---

# Proposta de Ação ACT-008: Padronização de Decorators HTTP

## 1. Problema Identificado no Review
Em [views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py):
1. A view `chat_stream` implementa checagem manual do método HTTP (`if request.method != "POST": return StreamingHttpResponse(...)`), em desacordo com o padrão canônico do Django.
2. Diversas views estritamente de leitura (`painel_chat`, `listar_mensagens`, `gerenciar_personas`, `exportar_sessao_markdown`, `dashboard_telemetria`) não possuem o decorator `@require_GET`, permitindo requisições acidentais via `POST`, `PUT` ou `DELETE`.

---

## 2. Parecer do Arquiteto de Software (/architect)

> **Diagnóstico Arquitetural:**
> O manual *Two Scoops of Django* estabelece como regra de ouro a aplicação explícita de restrição de verbos HTTP em FBVs (Function-Based Views).
> A utilização de decorators nativos (`@require_GET`, `@require_POST`):
> - Responde automaticamente com código HTTP padrão `405 Method Not Allowed`.
> - Inclui o cabeçalho `Allow` apropriado na resposta HTTP, respeitando os padrões da RFC 9110.
> - Elimina código *boilerplate* defensivo manual de dentro do corpo das views.

---

## 3. Especificação Técnica da Solução

### Mapeamento de Views e Decorators em `views.py`:

| View | Decorators Obrigatórios |
| :--- | :--- |
| `painel_chat` | `@login_required`, `@require_GET` |
| `nova_sessao` | `@login_required`, `@require_POST` |
| `deletar_sessao` | `@login_required`, `@require_POST` |
| `upload_documento_sessao` | `@login_required`, `@require_POST` |
| `deletar_documento_sessao` | `@login_required`, `@require_POST` |
| `listar_mensagens` | `@login_required`, `@require_GET` |
| `chat_stream` | `@login_required`, `@require_POST` |
| `gerenciar_personas` | `@login_required`, `@require_GET` |
| `criar_persona` | `@login_required`, `@require_POST` |
| `editar_persona` | `@login_required`, `@require_POST` |
| `deletar_persona` | `@login_required`, `@require_POST` |
| `atualizar_perfil_usuario` | `@login_required`, `@require_POST` |
| `exportar_sessao_markdown` | `@login_required`, `@require_GET` |
| `dashboard_telemetria` | `@login_required`, `@require_GET` |

### Checklist de Implementação para o /coder:
- [x] Importar `require_GET` e `require_POST` de `django.views.decorators.http`.
- [x] Aplicar `@require_GET` em todas as views de renderização/leitura pura.
- [x] Substituir a checagem manual em `chat_stream` pelo decorator canônico `@require_POST`.
- [x] Validar que os testes unitários cobrem respostas 405 para métodos não permitidos.

