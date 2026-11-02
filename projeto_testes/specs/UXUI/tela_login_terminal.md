# 🎨 UX/UI: Tela de Login Terminal (`login.html`)

Este documento detalha o design da tela de autenticação de operadores.

---

## 1. Esboço Visual (Wireframe em ASCII)

```text
┌────────────────────────────────────────────────────────┐
│                                                        │
│             ┌────────────────────────────┐             │
│             │ >_ TERMINAL LOGIN // AUTH  │             │
│             ├────────────────────────────┤             │
│             │ [!] Credenciais inválidas. │             │
│             │                            │             │
│             │ > USUÁRIO:                 │             │
│             │ [ rsmodel                ] │             │
│             │                            │             │
│             │ > SENHA:                   │             │
│             │ [ ********************** ] │             │
│             │                            │             │
│             │ [ AUTENTICAR NO TERMINAL ] │             │
│             └────────────────────────────┘             │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 2. Princípios de Ergonomia
- **Foco Centralizado:** Caixa de login contida com largura máxima de 420px centralizada vertical e horizontalmente na tela.
- **Autofocus Inteligente:** O cursor é posicionado automaticamente no campo de usuário ao abrir a página.
- **Teclado:** Submissão direta ao pressionar `Enter` a partir de qualquer campo.
- **Feedback de Falha:** Alerta em vermelho escuro com borda neon vermelha informando erro de credenciais sem vazar se o erro foi no usuário ou na senha (boa prática de segurança).

