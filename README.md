# 🤖 Chatbot Inteligente // Terminal AI & RAG Platform

> Plataforma completa de assistência conversacional construída em **Python & Django** com arquitetura modular, **Memória Híbrida persistente** (SQLite + ChromaDB), **RAG On-Demand para documentos locais**, **Personas Comportamentais Customizáveis** e interface visual imersiva em **Terminal Dark com acentos Verde Neon**.

---

## ⚡ Guia Rápido de Início (Setup & Execução)

### 1. Pré-requisitos
- **Python:** 3.11+ (ou ambiente virtual `BigData-env` configurado).
- **Chave de API do Google Gemini:** Necessária para inferência (`gemini-2.5-flash`) e embeddings vetoriais (`gemini-embedding-001`).

### 2. Configuração de Ambiente
Na pasta `projeto_testes/`, certifique-se de que o arquivo `.env` contenha a sua chave da Google GenAI:
```bash
# projeto_testes/.env
GEMINI_API_KEY="sua_chave_do_google_ai_aqui"
```

### 3. Migrações e Banco de Dados
Abra o terminal e execute as migrações:
```bash
cd projeto_testes
../BigData-env/bin/python manage.py migrate
```
*(A migração inicial já cria os 4 presets de personas do sistema: Assistente Geral, Tech Lead Django, Arquiteto Socrático e Executivo Conciso).*

### 4. Executando a Suíte de Testes Automatizados
O projeto conta com **32 testes automatizados** com 100% de cobertura de sucesso:
```bash
cd projeto_testes
../BigData-env/bin/python manage.py test app_chatbot
```

### 5. Iniciando o Servidor Local
Para subir o servidor de desenvolvimento:
```bash
cd projeto_testes
../BigData-env/bin/python manage.py runserver
```
O servidor estará disponível em: **`http://127.0.0.1:8000/chat/`**

---

## 🎮 Como Interagir com o Sistema (Guia do Operador)

### 1. Acesso & Login (`/chat/login/`)
- Ao acessar a rota `/chat/`, se você não estiver autenticado, será redirecionado para a tela de login.
- O sistema possui controle de acesso estrito: cada usuário enxerga apenas suas próprias conversas, documentos e personas customizadas (proteção total contra IDOR).
- **Restauração Automática:** Ao entrar, o sistema abre diretamente a **última sessão que você acessou antes de fechar a aba/deslogar**.

### 2. Interface do Chat Terminal (`/chat/`)
- **Avatares Duplos:** Suas mensagens aparecem à direita com a sua foto de perfil; as respostas do assistente aparecem à esquerda com a foto da persona ativa e seu cargo/especialidade.
- **Edição In-Place de Título:** Dê um **duplo clique** no título da conversa no topo (ou clique no ícone `✏️`) para renomear. Pressione **`Enter`** para salvar ou **`Esc`** para cancelar. A alteração sincroniza instantaneamente com a barra lateral.
- **Filtro em Tempo Real na Sidebar:** Digite no campo `> filtrar sessões...` para localizar conversas antigas instantaneamente sem recarregar a tela.
- **Atalho Global `/`:** Pressione a tecla **`/`** em qualquer lugar da tela para focar imediatamente no prompt de envio de mensagens.

### 3. Sistema de Personas Comportamentais
- **Seleção Dinâmica:** No cabeçalho do terminal, use o dropdown `[🎭 Persona ▾]` para alternar entre as personas do sistema ou suas personas customizadas.
- **Comando Slash:** Alterne a qualquer momento digitando:
  - `/persona coder` : Ativa o Tech Lead Django (Clean Code, PEP 8, Two Scoops).
  - `/persona socratico` : Ativa o Arquiteto Thought Partner (advogado do diabo, questionador).
  - `/persona resumidor` : Ativa o Executivo Conciso (bullet points de 3 linhas).
  - `/persona padrao` : Retorna ao assistente geral.

### 4. RAG com Documentos Anexados (`[📎 DOCS]`)
- No cabeçalho do chat, clique no botão **`[📎 DOCS (N)]`** para abrir a gaveta retrátil de documentos.
- **Formatos suportados:** `.pdf`, `.txt`, `.md`, `.csv`, `.json`, `.py` (máx. 5MB).
- O arquivo é fatiado em blocos semânticos de 1000 caracteres (com overlap de 150) e vetorizado no ChromaDB.
- O assistente passa a responder suas perguntas consultando prioritariamente o conteúdo do documento anexado!
- Digite **/docs** no prompt para listar os arquivos atualmente ativos na sessão.

### 5. Central de Personas & Perfil (`/chat/personas/`)
Clique no botão **`⚙️ PERSONAS`** no topo do chat (ou acesse `/chat/personas/`):
- **Aba Galeria:** Visualize os cards de todas as personas disponíveis com fotos, tags e demografia.
- **Aba Criar/Editar Persona (Split-Screen):** Configure o nome, foto, idade, escolaridade, cargo, tom de voz, história de vida (backstory) e diretrizes comportamentais, visualizando o card em **tempo real na coluna esquerda** enquanto digita!
- **Aba Meu Perfil:** Carregue sua foto de operador, defina seu nome de exibição e sua profissão (a IA utiliza esses dados para calibrar o vocabulário e a profundidade das respostas para você).

---

## 🤖 Comandos Disponíveis no Terminal (Slash Commands)

| Comando | Descrição |
| :--- | :--- |
| **`/status`** | Exibe o diagnóstico do sistema: ID da sessão, persona ativa, docs RAG e mensagens no SQLite. |
| **`/docs`** | Lista os documentos anexados à conversa com contagem de chunks vetoriais. |
| **`/persona <slug>`** | Altera instantaneamente a persona comportamental da conversa ativa. |
| **`/ajuda`** | Exibe a lista rápida de comandos no terminal. |

---

## 🏛️ Documentação Técnica & Especificações

Para detalhes completos de engenharia e governança de software, consulte a central de conhecimento localizada no projeto (`projeto_testes/`):
- [📑 Índice Mestre de Especificações (`projeto_testes/specs/SPECs.md`)](projeto_testes/specs/SPECs.md)
- [🏛️ Visão Arquitetural Global (`projeto_testes/specs/Architeture.md`)](projeto_testes/specs/Architeture.md)
- [🧭 Roadmap de Evolução (`projeto_testes/specs/ROADMAP.md`)](projeto_testes/specs/ROADMAP.md)
- [⚙️ Módulos Internos (`projeto_testes/specs/modulos_internos/`)](projeto_testes/specs/modulos_internos/)
- [🖥️ Módulos Externos (`projeto_testes/specs/modulos_externos/`)](projeto_testes/specs/modulos_externos/)
- [🎨 Especificações de UX/UI (`projeto_testes/specs/UXUI/`)](projeto_testes/specs/UXUI/)
- [💡 Laboratório de Ideias Futuras (`projeto_testes/specs/Ideias/`)](projeto_testes/specs/Ideias/)
- [🔍 Central de Auditorias & Laudos (`projeto_testes/reviews/`)](projeto_testes/reviews/)
- [📜 Architecture Decision Records (`projeto_testes/specs/architeture/`)](projeto_testes/specs/architeture/)
- [📦 Resumos Executivos de Entregas (`docs/entregas/`)](docs/entregas/)

---

## 👥 Roster de Agentes Especialistas Integrados

Este projeto adota um ecossistema multiagente com especialidades orquestradas:
- **`🤖 /review` (Tech Lead Reviewer):** Auditoria cirúrgica de Python, Django e Clean Code.
- **`🏛️ /architect` (Arquiteto de Software):** Ideação, trade-offs e registros formais de ADRs.
- **`💻 /coder` (Estagiário Codificador):** Braço de implementação 100% tipado, testável e Two Scoops.
- **`🖥️ /ux` ou `/ui` (Especialista em UX/UI):** Consultoria de design Terminal Dark, heurísticas de Nielsen e wireframes ASCII.
- **`📚 /doc` ou `/specs` (Guardião da Documentação):** Governança de specs, catalogação em `reviews/` e mediação de consenso.


