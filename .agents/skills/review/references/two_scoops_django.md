# Referência Técnica: Two Scoops of Django & Clean Code Python

Este guia consolida os princípios inegociáveis para a revisão técnica de código no ecossistema Django e fluxos de Inteligência Artificial.

---

## 1. Princípios Fundamentais do "Two Scoops of Django"

### 1.1 "Fat Models, Thin Views" vs. Service Layer
- **A Regra:** Views devem apenas receber a requisição HTTP, acionar a validação (via Forms/Serializers) e delegar a execução para uma camada de serviço ou método de domínio.
- **Evolução Moderna:** Models não devem virar "Deuses". Se a lógica envolve múltiplos models, APIs externas, emails ou processamento de IA, ela pertence a um **Service Layer** (`services/`), nunca ao `save()` do model ou ao corpo da view.

### 1.2 O Perigo dos Django Signals
- **Diretriz:** Evite usar `post_save` e `pre_save` para disparar lógica de negócio primária.
- **Motivo:** Signals introduzem acoplamento invisível e implícito, dificultam o rastreamento do fluxo de execução, tornam testes unitários imprevisíveis e frequentemente provocam loops infinitos ou side-effects descontrolados em migrações e fixtures.
- **Alternativa:** Chame explicitamente a função de serviço correspondente após a persistência.

### 1.3 ORM: Concorrência e Consultas N+1
- **ForeignKeys & OneToOne:** Sempre utilize `select_related()` para junções SQL em chaves estrangeiras únicas.
- **ManyToMany & Reverse ForeignKeys:** Sempre utilize `prefetch_related()` (ou objetos `Prefetch` com querysets refinados).
- **Condições de Corrida:** Nunca faça `objeto.saldo += valor; objeto.save()` em ambientes concorrentes. Utilize `F()` expressions (`F('saldo') + valor`) ou `select_for_update()` encapsulado em um bloco `transaction.atomic()`.
- **Bulk Operations:** Substitua loops de `.save()` ou `.create()` por `bulk_create()` e `bulk_update()`.

### 1.4 Custom QuerySets e Managers
- Encapsule filtros de banco repetitivos em métodos encadeáveis de `models.QuerySet`:
  ```python
  class PedidoQuerySet(models.QuerySet):
      def ativos(self):
          return self.filter(status=PedidoStatus.ATIVO)

      def com_itens(self):
          return self.prefetch_related("itens__produto")
  ```

---

## 2. Padrões de Integração com Inteligência Artificial

### 2.1 Bloqueios Síncronos
- **Crime:** Fazer chamadas diretas a LLMs (OpenAI, Gemini, Anthropic, Ollama) no ciclo de vida síncrono de uma View Django.
- **Correção:** Delegue a inferência para uma task assíncrona (Celery / RQ) ou utilize Django Channels / StreamingHttpResponse com timeouts rigorosos.

### 2.2 Transmissão de Estados em Tasks
- **Crime:** Passar instâncias de models do Django como argumentos de tasks do Celery (ex.: `minha_task.delay(pedido)`).
- **Correção:** Passe apenas identificadores primitivos (ex.: `minha_task.delay(pedido.id)`). A task deve buscar a instância fresca no banco dentro do seu escopo para evitar dados obsoletos (*stale state*).

### 2.3 Resiliência e Timeouts
- Todas as chamadas para provedores de IA devem conter timeouts explícitos (`timeout=15.0`), retries com backoff exponencial e fallbacks bem definidos para quando a API falhar.

---

## 3. PEP 8 e Clean Code Essentials

- **Nomenclatura:** `snake_case` para funções e variáveis, `PascalCase` para classes, `UPPER_SNAKE_CASE` para constantes.
- **Complexidade Ciclomática:** Métodos com múltiplos níveis de aninhamento (`if` dentro de `for` dentro de `if`) devem ser fatiados em funções pequenas com *Early Returns* (*Guard Clauses*).
- **Tipagem Estática:** Incentive Type Hints (`from typing import Optional, List...`) em novos métodos e services.
