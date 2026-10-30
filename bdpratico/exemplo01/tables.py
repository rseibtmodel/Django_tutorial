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
    id = tables.LinkColumn("pessoa_delete_alias", args=[A("pk")],verbose_name="Excluir")
    class Meta:
        model = pessoa
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome', 'email', 'celular', 'funcao', 'nascimento', 'ativo')