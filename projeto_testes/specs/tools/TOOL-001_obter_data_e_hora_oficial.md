---
id: TOOL-001
titulo: Ferramenta de Data e Hora Oficial do Sistema
modulo: tools
versao: 1.0.0
status: estavel
ultima_atualizacao: 2026-11-02
autores: [/doc_master, /architect, /coder]
---

# ⏱️ Ferramenta TOOL-001: `obter_data_e_hora_oficial`

- **Função Python:** `app_chatbot.tools.obter_data_e_hora_oficial`
- **Escopo:** Global (sem dependência de sessão)
- **Tipo de Execução:** Leitura de relógio do sistema com fuso horário

---

## 1. 🎯 Finalidade Operacional
Modelos de linguagem não possuem noção temporal intrínseca e frequentemente alucinam a data corrente ou calculam dias da semana incorretamente. Esta ferramenta fornece ao Gemini o timestamp exato, o dia da semana em português e o formato ISO oficial de Brasília (`America/Sao_Paulo`).

---

## 2. 📝 Assinatura & Especificação Técnica

```python
def obter_data_e_hora_oficial() -> str:
    """Retorna a data e o horário oficial do sistema no fuso horário do Brasil.

    Use esta ferramenta sempre que o usuário perguntar que horas são, a data de hoje,
    o dia da semana atual ou solicitar cálculos de prazos e datas.

    Returns:
        str: Texto formatado com data, hora e fuso horário oficial.
    """
```

### Parâmetros de Entrada:
- *Nenhum parâmetro requerido.*

### Retorno:
- `str`: String descritiva com o dia da semana, data formatada (`DD/MM/YYYY às HH:MM:SS`), fuso horário e string ISO 8601.

---

## 3. 🛡️ Segurança & Confiabilidade
- Não realiza operações de I/O em disco ou rede externa.
- Utiliza a biblioteca nativa `zoneinfo.ZoneInfo("America/Sao_Paulo")` com fallback para `django.utils.timezone.now()`.
- Imune a manipulações externas de entrada.

---

## 4. 💬 Exemplo de Chamada pela IA
**Pergunta do Usuário:** *"Que dia da semana é hoje e qual a hora exata?"*  
**Ação do Modelo:** `FunctionCall: obter_data_e_hora_oficial()`  
**Resposta da Ferramenta:** `"Data e hora oficial: Segunda-feira, 02/11/2026 às 15:45:00 (Fuso: America/Sao_Paulo, ISO: 2026-11-02T15:45:00-03:00)."`  
**Síntese da IA:** *"Hoje é segunda-feira, 02 de novembro de 2026, e agora são 15:45 (horário de Brasília)."*

