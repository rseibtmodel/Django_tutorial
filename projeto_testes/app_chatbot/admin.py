from django.contrib import admin
from .models import SessaoChat, MensagemChat


class MensagemChatInline(admin.TabularInline):
    model = MensagemChat
    extra = 0
    readonly_fields = ('papel', 'conteudo', 'criado_em')
    can_delete = True


@admin.register(SessaoChat)
class SessaoChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'usuario', 'criado_em', 'atualizado_em')
    list_filter = ('criado_em', 'atualizado_em')
    search_fields = ('titulo', 'id')
    inlines = [MensagemChatInline]


@admin.register(MensagemChat)
class MensagemChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'sessao', 'papel', 'conteudo_resumo', 'criado_em')
    list_filter = ('papel', 'criado_em')
    search_fields = ('conteudo',)

    @admin.display(description="Conteúdo")
    def conteudo_resumo(self, obj: MensagemChat) -> str:
        return obj.conteudo[:60] + "..." if len(obj.conteudo) > 60 else obj.conteudo
