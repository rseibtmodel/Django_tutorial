# SPECs - Módulos: 07. Tabelas e Frontend (`tables.py` & Templates)

## 1. Visão Geral e Arquitetura de Interface

A camada de interface do usuário (UI) utiliza o framework **Bootstrap 5** (via pacote `django-bootstrap5`) combinado com o **`django_tables2`** para geração de tabelas ricas com suporte nativo a paginação, links de ação contextual e estilização responsiva.

---

## 2. Código-Fonte de `exemplo01/tables.py`

Arquivo: [bdpratico/exemplo01/tables.py](file:///Users/rodrigomodel/agentes_inteligentes/bdpratico/exemplo01/tables.py#L1-L17)

```python
import django_tables2 as tables
from django_tables2.utils import A
from django.utils.html import format_html
from .models import pessoa

class pessoa_table(tables.Table):
    nome = tables.LinkColumn("pessoa_update_alias", args=[A("pk")])
    email = tables.LinkColumn("pessoa_update_alias", args=[A("pk")])
    celular = tables.LinkColumn("pessoa_update_alias", args=[A("pk")])
    funcao = tables.LinkColumn("pessoa_update_alias", args=[A("pk")])
    nascimento = tables.LinkColumn("pessoa_update_alias", args=[A("pk")])
    ativo = tables.Column()
    id = tables.LinkColumn("pessoa_delete_alias", args=[A("pk")], verbose_name="Excluir")

    class Meta:
        model = pessoa
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome', 'email', 'celular', 'funcao', 'nascimento', 'ativo')
```

---

## 3. Detalhamento dos Componentes de Tabela

### 3.1. Transformação de Colunas em Links (`tables.LinkColumn`)
- A função de utilidade `A("pk")` (Accessors do `django_tables2`) extrai a chave primária da linha atual do modelo.
- Todas as colunas informativas (`nome`, `email`, `celular`, `funcao`, `nascimento`) são renderizadas como hiperlinks HTML que apontam diretamente para a rota `pessoa_update_alias`, facilitando o clique para edição rápida.
- A coluna `id` é renomeada visualmente para **"Excluir"** (`verbose_name="Excluir"`) e aponta para a rota de exclusão `pessoa_delete_alias`.

### 3.2. Metadados e Estilos (`Meta`)
- **`attrs`:** Aplica classes CSS utilitárias do Bootstrap (`table`, `thead-light`, `table-striped`, `table-hover`) para zebrar as linhas e destacar o ponteiro do mouse ao passar por cima.
- **`template_name`:** Define o template base de renderização do `django_tables2` (`django_tables2/bootstrap4.html`).
- **`fields`:** Estabelece a ordem e quais campos do modelo serão renderizados na tabela.

---

## 4. Integração nos Templates HTML

### 4.1. `pessoa_menu.html` (Dashboard Principal)
```html
{% load static %}
{% load bootstrap5 %}
{% bootstrap_css %}
{% bootstrap_javascript %}
{% bootstrap_messages %}
{% load render_table from django_tables2 %}

<div class="container">
    <div class="col-md-12">
        <center>
            <img src="{% static 'pessoa.png' %}" class="img-fluid" width="15%">
            {% render_table table %}
        </center>
    </div>
</div>
```
* **O que faz:** Carrega os estilos e scripts do Bootstrap 5, renderiza mensagens flash e utiliza a tag `{% render_table table %}` para injetar a tabela gerada por `pessoa_table` com os controles de paginação inferior.

---

## 5. Parecer Crítico do Arquiteto & Oportunidades de Refatoração

1. **Descompasso entre Bootstrap 4 e Bootstrap 5:**
   - O projeto possui a biblioteca `bootstrap5` instalada e carregada nos templates (`{% load bootstrap5 %}`).
   - No entanto, a classe de tabela declara:
     ```python
     template_name = "django_tables2/bootstrap4.html"
     ```
   - *Impacto:* Classes depreciadas do Bootstrap 4 (como `thead-light`) deixam de ter efeito pleno no Bootstrap 5. O recomendado é utilizar o template específico `"django_tables2/bootstrap5.html"` caso disponível na versão instalada da biblioteca.
2. **Excesso de Colunas com Link:**
   - Praticamente todos os campos da tabela (`nome`, `email`, `celular`, `funcao`, `nascimento`) foram transformados em links de atualização.
   - *UX Recommendation:* Manter apenas o `nome` como link clicável para abrir a edição, e adicionar uma coluna dedicada de **Ações** contendo botões ou ícones para *Editar* e *Excluir*, melhorando a usabilidade em dispositivos móveis e evitando cliques acidentais.
3. **Tags HTML Depreciadas (`<center>`):**
   - O template utiliza a tag obsoleta `<center>`. Em padrões modernos de HTML5 e Bootstrap 5, o alinhamento deve ser feito através de classes de layout como `class="text-center"` ou `d-flex justify-content-center`.

