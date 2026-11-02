---
id: SPEC-EXT-006
titulo: Exportador de Conversas em Markdown Estruturado
modulo: modulos_externos
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-02
autores: [/coder, /architect, /doc]
---

# 📑 Exportador de Conversas em Markdown Estruturado

O módulo de exportação permite que o operador extraia com um único clique a transcrição integral e formatada de qualquer sessão de conversa ativa no Chatbot, respeitando o isolamento do usuário (IDOR).

---

## 1. 🎯 Objetivos e Valor para o Operador

- **Exportação Rápida:** Geração instantânea de arquivo `.md` contendo todos os turnos de diálogo, metadados da sessão, identificador UUID e data/hora exata de exportação.
- **Portabilidade de Conhecimento:** Permite salvar insights, código gerado e discussões em wikis corporativas (Notion, Obsidian, GitHub Discussions) ou anexar em relatórios.
- **Segurança e Privacidade:** Trava de autorização que garante que apenas o proprietário da sessão possa exportar seu histórico.

---

## 2. 🏛️ Arquitetura e Contratos de Dados

### Camada `services.py`
A função `gerar_markdown_conversa` centraliza a lógica de formatação:

```python
def gerar_markdown_conversa(
    *,
    sessao: SessaoChat,
    usuario: Union[AbstractBaseUser, AnonymousUser]
) -> str:
    """Gera um arquivo Markdown estruturado contendo a transcrição completa da sessão.

    Raises:
        SessaoNaoEncontradaError: Se a sessão não pertencer ao usuário autenticado.
    """
```

### Cabeçalho e Metadados do Arquivo Gerado
```markdown
# Transcrição de Conversa // {sessao.titulo}
> Relatório gerado automaticamente pelo Workspace Chatbot Terminal.

## 📋 Metadados da Sessão
- **ID da Sessão:** `{sessao.id}`
- **Operador:** `{nome_operador}`
- **Persona Ativa:** `{persona_nome}` [{persona_cargo}]
- **Total de Mensagens:** {len(mensagens)} turnos
- **Total de Tokens Registrados:** {total_tokens:,} tokens
- **Data da Exportação:** {data_exportacao}
```

### Camada `views.py` e Rota
- **View:** `exportar_sessao_markdown(request, sessao_id)` protegida por `@login_required`.
- **Rota:** `sessao/<uuid:sessao_id>/exportar/markdown/` (nome: `app_chatbot:exportar_sessao_markdown`).
- **Headers HTTP:** `Content-Type: text/markdown; charset=utf-8` e `Content-Disposition: attachment; filename="conversa_{slug}_{data}.md"`.

---

## 3. 🎨 Ergonomia e Pontos de Acesso na Interface

1. **Cabeçalho do Terminal:** Botão `[⬇ .MD]` posicionado ao lado dos controles da sessão ativa.
2. **Barra de Atalhos Rápidos:** Chip `⬇ Baixar .MD` na área de envio de mensagens.
3. **Tabela de Sessões no Dashboard:** Botão de download rápido para cada uma das conversas listadas.

