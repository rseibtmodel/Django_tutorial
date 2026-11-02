# 🖥️ Módulo Externo: Anexo de Documentos para RAG

Este documento especifica a interação do usuário com a gaveta de documentos RAG da sessão ativa.

---

## 1. Visão Geral
Cada sessão de conversa possui um repositório isolado de documentos. Ao anexar um arquivo à sessão ativa, o operador permite que o assistente consulte o conteúdo do documento para responder a perguntas factuais em tempo real.

---

## 2. A Gaveta Retrátil de Documentos (`#painel-docs`)
- **Abertura/Fechamento:**
  No cabeçalho do terminal, o botão `[📎 DOCS (N)]` exibe a contagem de documentos indexados. Ao clicar nele, a gaveta retrátil se expande suavemente no topo da área do chat.
- **Formulário de Upload:**
  - Campo de arquivo com suporte a formatos `.pdf`, `.txt`, `.md`, `.csv`, `.json`, `.py`.
  - Botão de ação neon `[ANEXAR]`.
  - Limite de 5MB por arquivo.
- **Lista de Documentos da Sessão:**
  - Exibe o nome do arquivo, tamanho e quantidade de chunks indexados no ChromaDB (ex: `📄 manual.pdf (14 chunks)`).
  - Botão de lixeira `[X]` em vermelho neon para remoção imediata via requisição POST (`/chat/sessao/<id>/doc/<doc_id>/deletar/`).

---

## 3. Comandos de Terminal Integrados
- O operador pode digitar `/docs` diretamente no campo de texto para visualizar no histórico a lista completa dos documentos atualmente disponíveis para o modelo.

