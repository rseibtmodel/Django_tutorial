# 🖥️ Módulo Externo: Autenticação & Multi-sessão

Este documento especifica o fluxo de acesso, autenticação de operadores e o isolamento de sessões no chatbot.

---

## 1. Visão Geral
O sistema opera sob modelo estrito de controle de acesso: nenhum usuário não autenticado pode enviar mensagens, acessar histórico ou disparar requisições ao Gemini.

---

## 2. Fluxo de Autenticação (`login_view` & `logout_view`)
- **Rota de Login:** `/chat/login/` (definida também em `LOGIN_URL` no `settings.py`).
- **Comportamento:**
  - Usuários já autenticados que visitam `/chat/login/` são redirecionados automaticamente para o painel principal (`/chat/`).
  - Suporta redirecionamento contextual via parâmetro `next` (ex: `/chat/login/?next=/chat/?sessao_id=...`).
  - Interface com visual dark terminal (`login.html`) contendo feedback visual de erro em caso de credenciais inválidas.
- **Rota de Logout:** `/chat/logout/` encerra a sessão com `django.contrib.auth.logout` e redireciona para a tela de login.

---

## 3. Isolamento Multi-Tenant & Restauração Automática
- **Prevenção Estrita de IDOR (Insecure Direct Object Reference):**
  Um usuário autenticado (ex: Rodrigo) **nunca** consegue visualizar, alterar ou excluir conversas de outro usuário (ex: Lucas). O acesso direto a uma URL com UUID de outro usuário (`/chat/?sessao_id=UUID_ALHEIO`) retorna **HTTP 404 Not Found**.
- **Restauração do Último Acesso:**
  Ao fazer login ou acessar `/chat/` sem informar `sessao_id`, o sistema busca no banco a conversa com o acesso mais recente do usuário (`SessaoChat.objects.filter(usuario=request.user).order_by("-acessado_em").first()`).
  O operador volta exatamente para a conversa onde parou antes de fechar a aba ou deslogar.

