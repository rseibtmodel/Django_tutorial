---
id: ACT-003
titulo: Serviço de Exclusão de Personas e Tratamento de Sessões Ativas
modulo: app_chatbot
relacionado_review: REV-0002
data_criacao: 2026-11-02
status: concluido
data_conclusao: 2026-11-02
autores: [/review, /architect, /doc_master]
---

# Proposta de Ação ACT-003: Serviço de Exclusão de Personas e Tratamento de Sessões Órfãs

## 1. Problema Identificado no Review
Na view `deletar_persona` ([views.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/views.py#L400-L413)):
1. A operação de exclusão ocorre diretamente na View (`persona.delete()`), violando o padrão *Fat Services / Thin Views* preconizado pelo *Two Scoops of Django*.
2. Quando a persona é excluída, as sessões do usuário associadas a ela sofrem `on_delete=models.SET_NULL`, ficando com `persona = None`. Se o operador voltar a essa sessão, ela perde a identidade até que o usuário execute um refresh manual.

---

## 2. Parecer do Arquiteto de Software (/architect)

> **Decisão Arquitetural:**
> Encapsular o ciclo de vida de deleção em `deletar_persona_customizada(*, persona, usuario)` na camada de `services.py`.
>
> **Política de Fallback de Persona Ativa:**
> Em vez de deixar as sessões com `persona = None`, o serviço deve reassociar atômica e explicitamente todas as sessões que utilizavam a persona deletada para a **Persona Padrão** do sistema:
>
> ```python
> persona_padrao = obter_persona_padrao()
> SessaoChat.objects.filter(persona=persona).update(persona=persona_padrao)
> ```
> Isso garante consistência de domínio ininterrupta para a inferência de LLM.

---

## 3. Especificação Técnica da Solução

### Novo Serviço em `services.py`:
```python
@transaction.atomic
def deletar_persona_customizada(
    *,
    persona: Persona,
    usuario: User
) -> str:
    """Exclui com segurança a persona customizada, apaga avatar do disco e reatribui sessões ativas para o preset padrão.

    Args:
        persona: Instância da persona a ser excluída.
        usuario: Usuário solicitante (trava IDOR).

    Returns:
        str: Nome da persona excluída para feedback.

    Raises:
        PersonaInvalidaError: Se a persona for do sistema ou não pertencer ao usuário.
    """
```

### Checklist de Implementação para o /coder:
- [x] Implementar `deletar_persona_customizada` em `services.py` com reatribuição para a persona padrão e expurgo da foto do disco.
- [x] Refatorar a view `deletar_persona` para consumir o novo serviço.
- [x] Adicionar teste unitário garantindo que após a exclusão da persona customizada, sessões vinculadas apontem para o preset `padrao`.

