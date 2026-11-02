---
id: ACT-005
titulo: Expurgo de Mutações na Camada de Seletores e Migração de Dados de Personas
modulo: app_chatbot
relacionado_review: REV-0003
data_criacao: 2026-11-02
status: concluido
data_conclusao: 2026-11-02
autores: [/review, /architect, /doc_master]
---

# Proposta de Ação ACT-005: Expurgo de Mutações na Camada de Seletores

## 1. Problema Identificado no Review
Na função `obter_persona_padrao` em [selectors.py](file:///Users/rodrigomodel/agentes_inteligentes/projeto_testes/app_chatbot/selectors.py#L181-L200), há uma instrução de escrita no banco de dados (`Persona.objects.create(...)`) caso a tabela de personas esteja vazia. Além disso, `obter_ou_criar_perfil_usuario` também executa `PerfilUsuario.objects.get_or_create(...)` dentro de `selectors.py`.
Isso quebra a segregação de responsabilidades (CQRS), onde **seletores devem ser estritamente funções de leitura puras sem efeitos colaterais**.

---

## 2. Parecer do Arquiteto de Software (/architect)

> **Diagnóstico Arquitetural:**
> Seletores são o "R" do CRUD. Quando um seletor muta o banco, os testes unitários tornam-se imprevisíveis (testes de leitura passam a criar dados ocultos), transações de leitura passam a requerer locks de escrita e pipelines de leitura em réplicas de Read-Only (como RDS Read Replica) quebram com exceções de `ReadOnlyDatabaseError`.
>
> **Trade-offs de Resolução:**
> 1. *Data Migration (Seed):* Criar uma data migration no Django (`000X_popular_personas_iniciais.py`) garantindo que as personas essenciais do sistema (`padrao`, `coder`, `architect`, `ux_designer`) já existam no banco após o `migrate`.
> 2. *Transferência de Responsabilidade de Criação:*
>    - Manter em `selectors.py` apenas `obter_persona_padrao() -> Optional[Persona]`.
>    - Mover funções do tipo `obter_ou_criar_*` para `services.py`, mantendo a escrita onde ela pertence.
> 3. *Graceful Fallback:* Caso a persona padrão não exista no banco (cenário extremo), o seletor retorna a primeira persona do sistema encontrada, ou `None`, permitindo que a camada de serviço/orquestração instancie ou levante erro controlado.

---

## 3. Especificação Técnica da Solução

### 1. Refatoração em `selectors.py`:
- `obter_persona_padrao() -> Optional[Persona]`: Apenas lê (`filter(slug="padrao", is_sistema=True).first()` ou `.first()`), sem nenhuma chamada a `.create()`.
- Transferir `obter_ou_criar_perfil_usuario` para `services.py` (ou delegar a criação explícita para a camada de serviços).

### 2. Criação de Migration de Dados:
- Migration que insere os registros padrão do sistema de forma idempotente (`get_or_create`).

### Checklist de Implementação para o /coder:
- [x] Refatorar `obter_persona_padrao` em `selectors.py` para remover qualquer chamada de criação (`Persona.objects.create`).
- [x] Transferir a criação/provisionamento de perfil e personas padrão para `services.py`.
- [x] Criar migração de dados no Django para popular a persona padrão e presets do sistema caso não existam.
- [x] Atualizar chamadas em `views.py` e `services.py` para respeitar a nova separação de camadas.
- [x] Atualizar testes unitários em `tests.py` validando que leituras são puras e testes continuam 100% verdes.

