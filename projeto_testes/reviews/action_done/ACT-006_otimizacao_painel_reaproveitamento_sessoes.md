---
id: ACT-006
titulo: Otimização do Painel de Chat e Eliminação de Escritas Desnecessárias em GET
modulo: app_chatbot
relacionado_review: REV-0003
data_criacao: 2026-11-02
status: concluido
data_conclusao: 2026-11-02
autores: [/review, /architect, /ux_designer, /doc_master]
---

# Proposta de Ação ACT-006: Otimização do Painel de Chat

## 1. Problema Identificado no Review
Na view `painel_chat` em [views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py#L99-L135), ocorrem os seguintes problemas de performance e semântica HTTP:
1. Uma requisição `GET` passiva executa um comando de escrita direto no banco: `SessaoChat.objects.filter(id=sessao.id).update(acessado_em=timezone.now())`. A cada reload de página pelo operador, uma query de UPDATE desnecessária é disparada.
2. A lista `sessoes = listar_sessoes_usuario(...)` é consultada antes de verificar se a sessão existe, e se for criada uma nova, a consulta é executada uma segunda vez na mesma requisição.
3. Se a sessão ativa foi atualizada no passo 1, a lista de sessões consultada no início pode conter o `acessado_em` desatualizado no HTML.

---

## 2. Parecer do Arquiteto de Software (/architect)

> **Diagnóstico Arquitetural:**
> O protocolo HTTP define requisições `GET` como métodos seguros e essencialmente idempotentes (*safe methods*). Fazer `UPDATE` em tabela a cada carregamento de página gera:
> - Concorrência desnecessária no SQLite (lock de escrita em páginas de leitura).
> - Poluição do timestamp de atividade (o operador apenas visualizou a página, não interagiu).
>
> **Diretriz de Design:**
> - O timestamp `acessado_em` deve ser atualizado apenas em interações ativas: quando uma mensagem é enviada (`chat_stream`) ou quando uma sessão é explicitamente selecionada/alternada pelo usuário.
> - O fluxo de inicialização da view deve resolver primeiro a sessão ativa (recuperar ou instanciar) e apenas então carregar a lista de sessões, garantindo que uma única consulta ao banco alimente o contexto.

---

## 3. Parecer do Especialista em UX/UI (/ux_designer)

> **Avaliação de Experiência do Operador:**
> O comportamento de reordenar ou reatualizar o timestamp a cada F5 provoca uma sensação de instabilidade na lista lateral de conversas. Ao evitar atualizações espúrias de timestamp, a sidebar preserva a ordem cronológica real de interação, mantendo a previsibilidade espacial do operador (Heurística 7 de Nielsen - Flexibilidade e Eficiência de Uso).

---

## 4. Especificação Técnica da Solução

### Fluxo Otimizado em `views.painel_chat`:
1. Validar `sessao_id` vindo do `request.GET`:
   - Se fornecido, recuperar via `obter_sessao_por_id`.
   - Se ausente, recuperar via `obter_ultima_sessao_acessada`.
2. Se nenhuma sessão existir, chamar serviço `criar_sessao_para_usuario`.
3. Consultar a lista de sessões (`listar_sessoes_usuario`) uma única vez após a determinação da sessão ativa.
4. Remover o `update(acessado_em=timezone.now())` do fluxo `GET` do painel.

### Checklist de Implementação para o /coder:
- [x] Remover a chamada redundante de `update(acessado_em=...)` no `GET` da view `painel_chat`.
- [x] Reorganizar o fluxo de queries em `painel_chat` para consultar a lista de sessões do usuário uma única vez.
- [x] Validar que o `chat_stream` continua atualizando o `acessado_em` a cada nova mensagem enviada.
- [x] Ajustar testes unitários relacionados ao fluxo de painel e sessões.

