
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
        """Calcula a idade da pessoa com base na data de nascimento.

        Args:
            obj (pessoa): Instância do modelo pessoa.

        Returns:
            Union[int, str]: Idade em anos completos ou mensagem caso a data não exista.
        """
        if not obj.nascimento:
            return 'Não informado'

        hoje: date = date.today()
        # Subtrai 1 ano se ainda não fez aniversário no ano corrente
        ja_fez_aniversario: bool = (hoje.month, hoje.day) >= (
            obj.nascimento.month,
            obj.nascimento.day,
        )
        idade: int = hoje.year - obj.nascimento.year - (0 if ja_fez_aniversario else 1)
        return idade


admin.site.register(pessoa, PessoaCustomizado)
admin.site.register(procedimento)
admin.site.register(procedimento_executado)