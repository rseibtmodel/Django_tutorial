# ⚙️ Módulo Interno: Orquestrador do Chat & Streaming de IA

Este documento especifica a classe `ChatOrchestratorService`, responsável por mediar a interação entre requisições HTTP, o motor de inferência do Gemini e a persistência de turnos.

---

## 1. Responsabilidades do `ChatOrchestratorService`
1. **Roteamento de Comandos Determinísticos:**  
   Identifica e responde imediatamente a comandos como `/status`, `/docs`, `/persona <slug>` e `/ajuda` antes de acionar a API externa, economizando tokens e latência.
2. **Batismo Automático de Título:**  
   Se a sessão ainda tiver o título padrão ("Nova Conversa"), utiliza os primeiros 35 caracteres da primeira mensagem com sanitização anti-XSS para nomear a conversa.
3. **Composição do Payload de Contexto:**  
   Combina:
   - System instruction compilada com a Persona ativa e o Perfil do Operador.
   - Trechos semânticos de conversas anteriores e documentos RAG.
   - Histórico imediato dos últimos 6 turnos válidos do SQLite.
4. **Streaming Token a Token:**  
   Executa `client.models.generate_content_stream()` e gera chunks em tempo real via gerador Python (`Generator[str, None, None]`) transmitidos pelo `StreamingHttpResponse`.

---

## 2. Blindagem contra Auto-Intoxicação de Prompt
Se a chamada à API do Google Gemini falhar por estouro de cota (HTTP 429), erro de conexão ou timeout de rede:
- A exceção é capturada e logada via `logger.error(..., exc_info=True)`.
- Uma mensagem explicativa é enviada ao usuário no stream: `"⚠️ Erro temporário na comunicação com o assistente: ..."`.
- **Regra de Ouro:** A mensagem de erro **NUNCA é persistida no banco SQLite como mensagem do modelo**.
- **Benefício:** Evita que falhas transitórias de infraestrutura virem "memória" no histórico de contexto dos turnos seguintes, impedindo que o modelo alucine tentando responder ao próprio stack trace.

---

## 3. Telemetria e Captura de Tokens
Ao final do stream, o orquestrador inspeciona o objeto `usage_metadata` retornado pelos chunks finais do Gemini e persiste a contagem de `total_token_count` no campo `MensagemChat.tokens_utilizados`, viabilizando análises de custo e volumetria.

