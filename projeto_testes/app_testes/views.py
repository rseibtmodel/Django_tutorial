from django.http import HttpRequest, JsonResponse


def index(request: HttpRequest) -> JsonResponse:
    """View de teste de saúde e boas-vindas do app_testes."""
    return JsonResponse({
        "status": "online",
        "mensagem": "Projeto Django e app de testes inicializados com sucesso!",
        "app": "app_testes"
    })
