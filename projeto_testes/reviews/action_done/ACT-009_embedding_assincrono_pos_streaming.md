---
id: ACT-009
titulo: Desacoplamento da Indexação Vetorial Pós-Streaming
modulo: app_chatbot
relacionado_review: REV-0003
data_criacao: 2026-11-02
status: concluido
data_conclusao: 2026-11-02
autores: [/review, /architect, /ux_designer, /doc_master]
---

# Proposta de Ação ACT-009: Desacoplamento da Indexação Vetorial Pós-Streaming

## 1. Problema Identificado no Review
No método `executar_chat_stream` em [services.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/services.py#L1266-L1277), após o término dos chunks de texto gerados pelo modelo Gemini, o gerador executa de forma síncrona:
```python
texto_final: str = "".join(resposta_completa)
if texto_final.strip():
    MensagemChat.objects.create(...)
    try:
        self._indexar_memoria(texto_usuario, texto_final)
    except Exception as e_mem:
        logger.warning(...)
```
O método `_indexar_memoria` realiza uma requisição externa de rede para a API de Embeddings do Gemini e grava os vetores resultantes no ChromaDB. Por estar localizado dentro do corpo do gerador antes de seu término, o cliente HTTP permanece com o socket TCP aberto esperando o fechamento da conexão, mesmo após ter recebido toda a mensagem visualmente no navegador.

---

## 2. Parecer do Arquiteto de Software (/architect)

> **Diagnóstico Arquitetural:**
> O objetivo principal de um endpoint de streaming HTTP (`StreamingHttpResponse`) é fornecer resposta de baixa latência ao cliente.
> Ao embutir a indexação vetorial síncrona (chamada de embeddings + gravação no ChromaDB) no encerramento do gerador:
> 1. A thread do WSGI fica presa por 500ms a 2s adicionais para cada interação finalizada.
> 2. O cliente web não pode liberar o estado de "digitando..." até que o socket HTTP seja fechado pelo servidor.
>
> **Trade-offs de Arquitetura:**
> - *Opção A (Fila Assíncrona Celery/Redis):* Arquitetura ideal de longo prazo (prevista na Fase 5 de `Architeture.md`).
> - *Opção B (Thread Não-Bloqueante Segura no Processo Atual):* Como solução imediata de baixo acoplamento antes da migração para Celery/ASGI, despachar a tarefa `_indexar_memoria` em uma thread em background (`threading.Thread(target=..., daemon=True).start()`) ou executar após o fechamento do stream, liberando o gerador para fechar a conexão HTTP imediatamente.

---

## 3. Parecer do Especialista em UX/UI (/ux_designer)

> **Impacto na Percepção de Fluidez do Usuário:**
> Quando o streaming de texto termina na tela mas a conexão continua pendente, o cursor de digitação verde neon (`.cursor-blink`) continua ativo por 1 a 2 segundos adicionais e o botão "Enviar" permanece desabilitado. O operador tem a falsa sensação de lentidão no encerramento da resposta. Desacoplar a indexação libera o campo de texto instantaneamente, reforçando a Heurística 1 (Visibilidade do status do sistema) e a sensação de alta performance típica de interfaces de console.

---

## 4. Especificação Técnica da Solução

### Abordagem em `ChatOrchestratorService`:
1. Salvar o registro da mensagem no SQLite (`MensagemChat.objects.create`).
2. Despachar a chamada de indexação de memória (`_indexar_memoria`) de modo desacoplado (via thread daemon ou runner isolado com tratamento de exceções robusto).
3. Finalizar o gerador sem reter o ciclo de vida da requisição HTTP do navegador.

### Checklist de Implementação para o /coder:
- [x] Refatorar `_indexar_memoria` em `ChatOrchestratorService` para execução desacoplada não-bloqueante da finalização do stream HTTP.
- [x] Garantir que logs defensivos capturem falhas na thread sem derrubar o processo principal.
- [x] Validar cobertura de testes unitários para a persistência da mensagem e disparo da indexação.

