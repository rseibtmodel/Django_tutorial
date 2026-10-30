# SPECs - Módulos: 05. Roteamento de URLs (`urls.py`)

## 1. Visão Geral e Estrutura Hierárquica

O roteamento da aplicação é descentralizado em duas camadas:
1. **Roteador Global do Projeto (`bdpratico/urls.py`):** Define os prefixos das aplicações e delega o processamento via `include()`.
2. **Roteadores de Aplicação (`exemplo01/urls.py` e `exemplo02/urls.py`):** Mapeiam os endpoints específicos para suas respectivas views e aliases de rota.

---

## 2. Código-Fonte do Roteador Principal

Arquivo: [bdpratico/bdpratico/urls.py](file:///Users/rodrigomodel/agentes_inteligentes/bdpratico/bdpratico/urls.py#L20-L25)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('exemplo01.urls')),
    path('exemplo01/', include('exemplo01.urls')),
    path('exemplo02/', include('exemplo02.urls')),
    path('admin/', admin.site.urls)
]
```

* **Comportamento Chave:** A aplicação `exemplo01` está duplamente registrada: tanto na raiz (`/`) quanto no subdiretório (`/exemplo01/`). Isso significa que rotas como `menu` podem ser acessadas tanto por `http://127.0.0.1:8000/menu` quanto por `http://127.0.0.1:8000/exemplo01/menu`.

---

## 3. Código-Fonte do Roteador de `exemplo01`

Arquivo: [bdpratico/exemplo01/urls.py](file:///Users/rodrigomodel/agentes_inteligentes/bdpratico/exemplo01/urls.py#L5-L19)

```python
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index_alias'),
    path('pagina0', views.pagina0, name='pagina0'),
    path('pagina1', views.pagina1, name='pagina1'),
    path('pagina2', views.pagina2, name='pagina2'),
    path('pagina3', views.pagina3, name='pagina3'),
    path('pagina4', views.pagina4, name='pagina4_alias'),
    path('pagina5', views.pagina5, name='pagina5_alias'),
    path('menu', views.pessoa_menu.as_view(), name='menu_alias'),
    path("pessoa_create/", views.pessoa_create.as_view(), name='pessoa_create_alias'),
    path("pessoa_list/", views.pessoa_list.as_view(), name='pessoa_list_alias'),
    path("pessoa_update/<int:pk>/", views.pessoa_update.as_view(), name='pessoa_update_alias'),
    path('pessoa_delete/<int:pk>/', views.pessoa_delete.as_view(), name='pessoa_delete_alias'),
]
```

---

## 4. Tabela Completa de Rotas e Parâmetros

| Rota Relativa | Tipo de View | Classe / Função | Nome da Rota (`name`) | Descrição e Parâmetros |
| :--- | :--- | :--- | :--- | :--- |
| `''` | FBV | `views.index` | `index_alias` | Tela de Login / Início |
| `'pagina0'` | FBV | `views.pagina0` | `pagina0` | Demonstração estática 0 |
| `'pagina1'` | FBV | `views.pagina1` | `pagina1` | Demonstração com arquivos estáticos |
| `'pagina2'` | FBV | `views.pagina2` | `pagina2` | Renderização com ORM simples |
| `'pagina3'` | FBV | `views.pagina3` | `pagina3` | Tabela Bootstrap com loop de pessoas |
| `'pagina4'` | FBV | `views.pagina4` | `pagina4_alias` | Recepção e print de parâmetros POST |
| `'pagina5'` | FBV | `views.pagina5` | `pagina5_alias` | Formulário e criação manual no banco |
| `'menu'` | CBV | `views.pessoa_menu.as_view()` | `menu_alias` | Painel geral com tabela e paginação |
| `'pessoa_create/'` | CBV | `views.pessoa_create.as_view()` | `pessoa_create_alias` | Formulário de criação de pessoa |
| `'pessoa_list/'` | CBV | `views.pessoa_list.as_view()` | `pessoa_list_alias` | Lista filtrada de pessoas ativas |
| `'pessoa_update/<int:pk>/'` | CBV | `views.pessoa_update.as_view()` | `pessoa_update_alias` | Edição com chave primária numérica |
| `'pessoa_delete/<int:pk>/'` | CBV | `views.pessoa_delete.as_view()` | `pessoa_delete_alias` | Exclusão com chave primária numérica |

---

## 5. Parecer Crítico do Arquiteto & Oportunidades de Refatoração

1. **Ausência de Padronização de Trailing Slash (`/`):**
   - Várias rotas foram declaradas sem a barra final (ex.: `'pagina0'`, `'pagina1'`, `'menu'`), enquanto outras foram declaradas com barra (ex.: `'pessoa_create/'`).
   - *Impacto:* O Django, por padrão, utiliza a configuração `APPEND_SLASH = True`. Misturar rotas com e sem barra gera inconsistências em requisições de navegadores e clientes REST/API. O padrão canônico do Django é terminar todos os paths com barra: `'pagina0/'`, `'menu/'`.
2. **Alinhamento do Nome da Rota `menu_alias`:**
   - Em `views.py`, o `reverse_lazy` está buscando `'pessoa_menu_alias'`. É essencial renomear a rota no `urls.py` para `name='pessoa_menu_alias'` ou alterar a view para evitar quebras de fluxo.
3. **Uso de `app_name` (Namespacing de URLs):**
   - Atualmente, não há namespace declarado (`app_name = 'exemplo01'`). À medida que novos apps forem adicionados ao projeto, colisões de nomes como `name='index'` ocorrerão.
   - *Recomendação:* Adicionar `app_name = 'exemplo01'` e referenciar nos templates como `{% url 'exemplo01:pessoa_list_alias' %}`.

