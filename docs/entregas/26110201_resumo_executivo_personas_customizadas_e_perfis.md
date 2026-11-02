# Resumo Executivo: Sistema de Personas Customizáveis & Perfis de Operador com Avatares

- **Identificador da Entrega:** 26110201
- **Data:** 02/11/2026
- **Responsável:** Estagiário Codificador
- **Origem da Demanda:** Especificação Arquitetural (`/architect`) e Design de UX/UI (`/ux_designer`)

---

## 1. Escopo & ADRs Atendidas
- **Objetivo da Entrega:** Implementação da plataforma de Personas dinâmicas configuráveis e Perfis de Usuário com suporte a fotos/avatares e compilação comportamental de System Prompts para o Gemini.
- **Destaques Técnicos:**
  - **Novo Modelo `Persona`:** Suporte a personas do sistema (presets protegidos) e personas customizadas criadas pelos usuários, com demografia (idade, sexo, escolaridade), profissão/cargo, tom de voz, backstory detalhada, diretrizes de comportamento e foto/avatar.
  - **Novo Modelo `PerfilUsuario`:** Perfil estendido com foto de perfil, nome de exibição, profissão e bio, injetado no compilador de contexto para que a IA adapte suas respostas especificamente ao operador.
  - **Migração do `SessaoChat.persona`:** Migrado de `CharField` estático para `ForeignKey(Persona, on_delete=models.SET_NULL)`, acompanhado de *data migration* com pré-povoamento dos 4 presets globais do sistema (`padrao`, `coder`, `socratico`, `resumidor`).
  - **Compilador de Prompt da Persona (`Prompt Assembler`):** Motor no `services.py` que sintetiza os atributos demográficos, tom e história da persona em um System Prompt hierárquico e conciso, evitando *prompt bloat* e mantendo alta aderência de comportamento no Gemini 2.5 Flash.
  - **Nova Tela Central `/personas/` (`personas.html`):** Interface completa em estética Cyber-Clean Terminal Dark com três abas:
    1. Galeria de Personas com cards visuais, fotos e tags de especialidade.
    2. Editor Split-Screen com Live Preview do card em tempo real enquanto o usuário digita e formulário categorizado.
    3. Meu Perfil de Operador para configuração de nome, ocupação e upload de foto.
  - **Chat Enriquecido com Avatares Duplos (`chat.html`):** Bolha do usuário com avatar à direita e bolha do assistente com avatar da persona à esquerda encimada pelo nome do personagem.
  - **Zero Dependências Externas Adicionais:** Utilização de `FileField` com validações nativas em Python, eliminando a dependência do `Pillow` em conformidade com as regras do projeto.

---

## 2. Mapa de Arquivos

- `projeto_testes/projeto_testes/settings.py`: [Modificado] — Adicionadas configurações de `MEDIA_URL` e `MEDIA_ROOT`.
- `projeto_testes/projeto_testes/urls.py`: [Modificado] — Habilitado roteamento de arquivos de mídia em modo `DEBUG`.
- `projeto_testes/app_chatbot/models.py`: [Modificado] — Criados modelos `PerfilUsuario` e `Persona`, e atualizado campo `persona` em `SessaoChat` para `ForeignKey`.
- `projeto_testes/app_chatbot/migrations/0004_persona_perfilusuario_alter_sessaochat_persona.py`: [Criado] — Migração de schema e seeding de dados aplicada com sucesso.
- `projeto_testes/app_chatbot/exceptions.py`: [Modificado] — Adicionadas exceções `PersonaInvalidaError` e `PerfilInvalidoError`.
- `projeto_testes/app_chatbot/selectors.py`: [Modificado] — Adicionados seletores `listar_personas_disponiveis`, `obter_persona_por_id_ou_slug`, `obter_persona_padrao` e `obter_ou_criar_perfil_usuario`.
- `projeto_testes/app_chatbot/services.py`: [Modificado] — Implementados `compilar_system_prompt_persona`, `criar_persona_customizada`, `atualizar_persona_customizada`, `atualizar_perfil_usuario` e integração no `ChatOrchestratorService`.
- `projeto_testes/app_chatbot/views.py`: [Modificado] — Criadas views `gerenciar_personas`, `salvar_persona`, `deletar_persona` e `salvar_perfil_usuario` com `@require_POST` e travas IDOR.
- `projeto_testes/app_chatbot/urls.py`: [Modificado] — Registradas novas rotas `/personas/`, `/personas/salvar/`, `/personas/<uuid>/deletar/` e `/perfil/salvar/`.
- `projeto_testes/app_chatbot/templates/app_chatbot/personas.html`: [Criado] — Template da Central de Personas e Perfil com Split-Screen Live Preview.
- `projeto_testes/app_chatbot/templates/app_chatbot/chat.html`: [Modificado] — Renderização de avatares duplos nas bolhas de mensagem e seletor dinâmico de personas.
- `projeto_testes/app_chatbot/tests.py`: [Modificado] — Suíte expandida de 25 para 32 testes automatizados com 100% de cobertura.

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
- `Ran 32 tests in 8.226s — OK` (100% de sucesso).

---

## 4. Pontos de Atenção para Deploy & Produção

- **Armazenamento de Mídia:** Fotos enviadas para personas e perfis são salvas em `media/personas/` e `media/perfis/`. Para ambientes de nuvem, recomenda-se configurar backend de S3 / Cloud Storage via `django-storages`.
- **Integridade de Personas do Sistema:** Personas com `is_sistema=True` são bloqueadas contra exclusão e edição indevida por usuários comuns.

