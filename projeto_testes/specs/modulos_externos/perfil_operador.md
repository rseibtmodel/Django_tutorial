# 🖥️ Módulo Externo: Perfil do Operador (Usuário)

Este documento descreve o módulo de gerenciamento de perfil e avatar do usuário/operador humano.

---

## 1. Objetivo
Permitir que o operador personalize sua presença no sistema carregando uma foto de perfil e preenchendo seus dados biográficos, gerando duas vantagens imediatas:
1. **Identificação Visual:** A foto do usuário aparece ao lado das mensagens enviadas no chat e no rodapé da barra lateral.
2. **Hiper-Personalização das Respostas:** Os dados biográficos (nome de exibição, profissão e bio) são compilados no System Prompt, permitindo que a IA converse sabendo o contexto profissional e as preferências de quem está perguntando.

---

## 2. Campos do Perfil (`PerfilUsuario`)
- **Nome de Exibição (`nome_exibicao`):** Nome pelo qual a IA e a interface devem chamar o operador.
- **Profissão / Ocupação (`profissao`):** Cargo ou área de atuação (ex: "Desenvolvedor Backend", "Médico Radiologista", "Cientista de Dados").
- **Data de Nascimento (`data_nascimento`):** Opcional para calibração demográfica.
- **Bio Pessoal (`bio`):** Descrição das preferências e objetivos de trabalho do usuário.
- **Foto de Perfil (`foto`):** Imagem circular exibida nas mensagens enviadas no terminal.

---

## 3. Gestão na Interface
Aba `#perfil` em `/chat/personas/`:
- Mostra avatar de 120x120px com a foto atual ou iniciais do username.
- Formulário com salvamento via `POST /chat/perfil/salvar/` com validações no `services.py`.

