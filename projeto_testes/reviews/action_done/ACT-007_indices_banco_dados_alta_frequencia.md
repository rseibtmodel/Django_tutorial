---
id: ACT-007
titulo: Criação de Índices Estruturais e Compostos para Sessões e Mensagens
modulo: app_chatbot
relacionado_review: REV-0003
data_criacao: 2026-11-02
status: concluido
data_conclusao: 2026-11-02
autores: [/review, /architect, /doc_master]
---

# Proposta de Ação ACT-007: Índices de Alta Frequência em Sessões e Mensagens

## 1. Problema Identificado no Review
Em [models.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/models.py):
1. O modelo `SessaoChat` define `ordering = ['-acessado_em']` na classe `Meta`, e os seletores utilizam `.order_by("-acessado_em")` repetidamente. Contudo, o campo `acessado_em` não possui `db_index=True`.
2. O modelo `MensagemChat` armazena o histórico de cada conversa e é consultado em toda troca de mensagens (filtro por `sessao` e ordenação por `criado_em`). Não há índice composto para o par `(sessao, criado_em)`.

---

## 2. Parecer do Arquiteto de Software (/architect)

> **Diagnóstico Arquitetural:**
> Conforme a base de dados cresce em produção, a ausência de índices nos campos de ordenação e filtros de alta frequência provoca *Sequential Scans* (varredura completa da tabela) no banco relacional.
> Em um sistema conversacional de IA:
> - O histórico recente da conversa (`filter(sessao=sessao).order_by("-criado_em")[:6]`) é chamado em todo turno do Gemini.
> - Um índice B-Tree composto `(sessao, criado_em)` no modelo `MensagemChat` transforma essa busca de $O(N)$ para $O(\log N)$, eliminando locks e garantindo resposta instantânea.
> - Da mesma forma, indexar `SessaoChat.acessado_em` acelera a renderização da barra lateral de conversas.

---

## 3. Especificação Técnica da Solução

### Alterações em `models.py`:

```python
class SessaoChat(models.Model):
    ...
    acessado_em = models.DateTimeField(
        default=timezone.now,
        db_index=True,  # Adição de índice direto
        verbose_name="Último Acesso"
    )

class MensagemChat(models.Model):
    ...
    class Meta:
        ordering = ['criado_em']
        verbose_name = "Mensagem de Chat"
        verbose_name_plural = "Mensagens de Chat"
        indexes = [
            models.Index(fields=['sessao', 'criado_em'], name='idx_msg_sessao_criado'),
        ]
```

### Checklist de Implementação para o /coder:
- [x] Adicionar `db_index=True` ao campo `acessado_em` em `SessaoChat`.
- [x] Adicionar índice composto `models.Index(fields=['sessao', 'criado_em'], name='idx_msg_sessao_criado')` no `Meta` de `MensagemChat`.
- [x] Gerar nova migration com `python manage.py makemigrations app_chatbot`.
- [x] Aplicar migration com `python manage.py migrate`.
- [x] Executar suíte de testes garantindo 100% de compatibilidade.

