# Resumo Executivo: Módulo de RAG (Upload de Documentos) & Sistema de Personas

- **Identificador da Entrega:** 26110104
- **Data:** 01/11/2026
- **Responsável:** Estagiário Codificador
- **Origem da Demanda:** Especificação Arquitetural (`/architect`) e Design de UX/UI (`/ux_designer`)

---

## 1. Escopo & ADRs Atendidas
- **Objetivo da Entrega:** Implementação dos módulos de RAG (Retrieval-Augmented Generation) com ingestão e chunking de documentos locais no ChromaDB e sistema dinâmico de Personas comportamentais com comandos de terminal.
- **Destaques Técnicos:**
  - **Módulo de Personas:** Adição do campo `persona` em `SessaoChat` com 4 modos especializados (`padrao`, `coder`, `socratico`, `resumidor`) integrados a prompts de sistema modulares e comutação via dropdown ou comando `/persona <tipo>`.
  - **Módulo RAG de Documentos:** Novo modelo `DocumentoSessao` com suporte a upload de arquivos `.pdf`, `.txt`, `.md`, `.csv`, `.json`, `.py`, pipeline de chunking semântico (1000 caracteres, overlap de 150) e vetorização no ChromaDB vinculada à sessão.
  - **Consultas Semânticas Híbridas:** Recuperação no ChromaDB combinando memórias episódicas e trechos de documentos anexados (`tipo="documento_rag"`), com injeção priorizada no prompt de inferência.
  - **UX Terminal Enriquecida:** Seletor de persona no header, gaveta retrátil de documentos com upload e contagem de chunks, filtro de sessões em tempo real na sidebar e atalho global `/` para foco no prompt.
  - **Proteção IDOR e Limites de Segurança:** Limite estrito de 5MB por arquivo, máx 50 chunks no MVP, exclusão segura de arquivos e expurgo atômico de vetores no ChromaDB.

---

## 2. Mapa de Arquivos

- `projeto_testes/app_chatbot/models.py`: [Modificado] — Adicionado campo `persona` em `SessaoChat` e criado modelo `DocumentoSessao`.
- `projeto_testes/app_chatbot/migrations/0003_sessaochat_persona_documentosessao.py`: [Criado] — Migração de schema aplicada com sucesso.
- `projeto_testes/app_chatbot/exceptions.py`: [Modificado] — Adicionadas exceções `PersonaInvalidaError` e `DocumentoInvalidoError`.
- `projeto_testes/app_chatbot/selectors.py`: [Modificado] — Adicionados seletores `listar_documentos_sessao` e `obter_documento_por_id`.
- `projeto_testes/app_chatbot/services.py`: [Modificado] — Implementadas matriz de prompts de personas, funções `alterar_persona_sessao`, `extrair_texto_de_arquivo`, `fatiar_texto_em_chunks`, `processar_e_indexar_documento`, `remover_documento_e_vetores` e integração de RAG no streaming.
- `projeto_testes/app_chatbot/views.py`: [Modificado] — Criadas views `alterar_persona`, `upload_documento` e `deletar_documento` com `@require_POST` e isolamento IDOR.
- `projeto_testes/app_chatbot/urls.py`: [Modificado] — Registradas novas rotas `/persona/`, `/upload-doc/` e `/doc/<uuid>/deletar/`.
- `projeto_testes/app_chatbot/templates/app_chatbot/chat.html`: [Modificado] — Interface atualizada com seletor de persona, gaveta RAG retrátil, filtro de sidebar e atalho global `/`.
- `projeto_testes/app_chatbot/tests.py`: [Modificado] — Suíte expandida de 18 para 25 testes automatizados cobrindo personas, comandos slash, upload de arquivo, chunking e remoção de documentos.

---

## 3. Roteiro de Execução Local & Testes

```bash
# 1. Aplicar migrações
cd projeto_testes
../BigData-env/bin/python manage.py migrate

# 2. Executar suíte de testes
../BigData-env/bin/python manage.py test app_chatbot
```

**Resultado dos Testes:**
- `Ran 25 tests in 6.612s — OK` (100% de sucesso).

---

## 4. Pontos de Atenção para Deploy & Produção

- **Armazenamento de Arquivos:** Arquivos enviados são armazenados na pasta `media/docs_chat/%Y/%m/`. Para produção, recomenda-se configurar storage em S3 / GCS.
- **Dependências Externas:** Zero novas bibliotecas externas adicionadas ao projeto.
- **Segurança:** Validação defensiva de tipos de arquivo e exclusão em cascata de vetores no ChromaDB para evitar vazamento de dados entre sessões.

