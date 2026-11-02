# SPECs - Módulos: 06. Painel Administrativo (`exemplo01/admin.py`)

## 1. Visão Geral e Responsabilidade

O arquivo [bdpratico/exemplo01/admin.py](file:///Users/rodrigomodel/agentes_inteligentes/bdpratico/exemplo01/admin.py) estende o Django Admin nativo para gerenciamento backoffice das três entidades do app. Ele implementa uma classe `ModelAdmin` altamente customizada (`PessoaCustomizado`), com ações em lote e uma coluna calculada dinamicamente para exibição de idade.

---

## 2. Código-Fonte da Implementação

```python
from datetime import date
from typing import Union
from django.contrib import admin
from .models import pessoa, procedimento, procedimento_executado

@admin.action(description="Habilitar Registros Selecionados")
def habilitar_pessoas(ModelAdmin, request, queryset):
    for p in queryset:
        p.ativo = True
        p.save()

@admin.action(description="Desabilitar Registros Selecionados")
def desabilitar_pessoas(ModelAdmin, request, queryset):
    queryset.update(ativo=False)

class PessoaCustomizado(admin.ModelAdmin):
    """Configuração customizada do modelo pessoa no Django Admin."""

    list_display = ('nome', 'email', 'celular', 'funcao', 'ativo', 'calcula_idade')
    list_filter = ('funcao', 'ativo')
    actions = [habilitar_pessoas, desabilitar_pessoas]

    @admin.display(description='Idade')
    def calcula_idade(self, obj: pessoa) -> Union[int, str]:
        if not obj.nascimento:
            return 'Não informado'

        hoje: date = date.today()
        ja_fez_aniversario: bool = (hoje.month, hoje.day) >= (
            obj.nascimento.month,
            obj.nascimento.day,
        )
        idade: int = hoje.year - obj.nascimento.year - (0 if ja_fez_aniversario else 1)
        return idade

admin.site.register(pessoa, PessoaCustomizado)
admin.site.register(procedimento)
admin.site.register(procedimento_executado)
```

---

## 3. Detalhamento dos Componentes

### 3.1. Ações em Lote Customizadas (`@admin.action`)

O Django Admin permite selecionar múltiplos checkboxes de registros e aplicar ações em bloco através do dropdown:

1. **`habilitar_pessoas`:**
   - Itera sobre cada registro selecionado no `queryset`, marca `p.ativo = True` e executa `p.save()`.
   - *Comportamento:* Dispara individualmente métodos `save()` e sinais (`post_save`) do Django para cada linha.
2. **`desabilitar_pessoas`:**
   - Executa `queryset.update(ativo=False)`.
   - *Comportamento:* Executa uma única instrução SQL direta no banco (`UPDATE exemplo01_pessoa SET ativo = 0 WHERE id IN (...)`). É uma operação atômica e de alta performance.

### 3.2. Configurações de Exibição (`PessoaCustomizado`)

- **`list_display`:** Define as colunas visíveis na tabela:
  `'nome'`, `'email'`, `'celular'`, `'funcao'`, `'ativo'` e o campo calculado `'calcula_idade'`.
- **`list_filter`:** Adiciona painel lateral de filtros rápidos por `'funcao'` e pelo status `'ativo'`.
- **`actions`:** Registra as duas ações customizadas de ativação e desativação em massa.

### 3.3. Cálculo Dinâmico de Idade (`calcula_idade`)

O método decorado com `@admin.display(description='Idade')` calcula a idade precisa do indivíduo:
1. Valida se a data de nascimento existe (`if not obj.nascimento`). Caso contrário, retorna `'Não informado'`.
2. Obtém a data corrente do sistema com `date.today()`.
3. Compara a tupla `(mês_atual, dia_atual)` com `(mês_nascimento, dia_nascimento)` para verificar se o indivíduo já fez aniversário no ano presente.
4. Realiza a subtração `ano_atual - ano_nascimento`, decrementando `1` caso ainda não tenha comemorado o aniversário no ano.

---

## 4. Registro dos Demais Modelos

- `admin.site.register(procedimento)`: Registra o catálogo de procedimentos com a visualização padrão.
- `admin.site.register(procedimento_executado)`: Registra a tabela associativa de execuções com formulários de seleção por chave estrangeira.

---

## 5. Parecer Crítico do Arquiteto & Oportunidades de Refatoração

1. **Diferença de Performance entre as Ações em Lote:**
   - Em `habilitar_pessoas`, o código utiliza um loop `for p in queryset: p.save()`, gerando $N$ queries `UPDATE` no banco.
   - Em `desabilitar_pessoas`, utiliza `queryset.update(ativo=False)`, gerando 1 única query.
   - *Recomendação:* Padronizar `habilitar_pessoas` com `queryset.update(ativo=True)`, a menos que haja necessidade estrita de disparar `signals` do Django a cada alteração.
2. **Inlines para Atendimentos:**
   - Na tela da pessoa, não é possível ver quais procedimentos ela já executou sem navegar até a tabela de `procedimento_executado`.
   - *Recomendação:* Adicionar um `admin.TabularInline` de `procedimento_executado` dentro de `PessoaCustomizado`, permitindo visualizar e lançar procedimentos diretamente na ficha da pessoa.
3. **Ordenação pelo Campo Calculado:**
   - Campos calculados em Python como `calcula_idade` não podem ser ordenados nativamente por clique no cabeçalho da coluna no Admin, pois não existem como coluna real no banco de dados SQL. Caso a ordenação por idade se torne necessária, deve-se utilizar `annotate` com funções de data do banco.

