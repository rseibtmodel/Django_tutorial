# Referência Prática: Padrão Service / Selector & FBV com Google Docstrings

Exemplo canônico de como o **Estagiário Codificador** estrutura o código Python/Django em cada camada.

---

### 1. Camada de Exceções de Domínio (`exceptions.py`)

```python
"""Exceções de domínio específicas do módulo financeiro."""


class SaldoInsuficienteException(Exception):
    """Lançada quando a conta de origem não possui saldo suficiente para a transação."""


class ContaInativaException(Exception):
    """Lançada ao tentar operar sobre uma conta inativa ou bloqueada."""
```

---

### 2. Camada de Consultas (`selectors.py`)

```python
"""Camada de leitura e consultas otimizadas do módulo financeiro."""

from decimal import Decimal
from typing import Optional
from django.db.models import QuerySet
from financeiro.models import Transacao, Conta


def get_conta_por_id(*, conta_id: int) -> Optional[Conta]:
    """Recupera uma conta específica pelo seu identificador único.

    Args:
        conta_id: Identificador numérico da conta bancária.

    Returns:
        Instância de Conta se encontrada, ou None.
    """
    return Conta.objects.filter(id=conta_id).first()


def listar_transacoes_da_conta(*, conta_id: int) -> QuerySet[Transacao]:
    """Lista o histórico de transações de uma conta otimizando relações com select_related.

    Args:
        conta_id: Identificador da conta pesquisada.

    Returns:
        QuerySet de Transacao contendo os relacionamentos de origem e destino pré-carregados.
    """
    # Evitamos N+1 pré-carregando os dados das duas contas associadas à transação
    return (
        Transacao.objects.filter(origem_id=conta_id)
        .select_related("origem", "destino")
        .order_by("-criado_em")
    )
```

---

### 3. Camada de Regras e Mutações (`services.py`)

```python
"""Camada de mutação, orquestração de transações e regras de negócio."""

from decimal import Decimal
from django.db import transaction
from financeiro.models import Conta, Transacao
from financeiro.exceptions import SaldoInsuficienteException, ContaInativaException
from financeiro import selectors


def _validar_transferencia(*, origem: Conta, destino: Conta, valor: Decimal) -> None:
    """Valida as regras de negócio antes de efetivar uma transferência financeira.

    Args:
        origem: Conta debitada.
        destino: Conta creditada.
        valor: Valor monetário da transferência.

    Raises:
        ContaInativaException: Se alguma das contas estiver inativa.
        SaldoInsuficienteException: Se a conta origem não tiver saldo suficiente.
        ValueError: Se o valor da transferência for menor ou igual a zero.
    """
    if valor <= Decimal("0.00"):
        raise ValueError("O valor da transferência deve ser estritamente positivo.")

    if not origem.ativa or not destino.ativa:
        raise ContaInativaException("Ambas as contas precisam estar ativas para realizar a operação.")

    if origem.saldo < valor:
        raise SaldoInsuficienteException(
            f"Saldo insuficiente. Disponível: R$ {origem.saldo}, Solicitado: R$ {valor}"
        )


@transaction.atomic
def realizar_transferencia(*, origem_id: int, destino_id: int, valor: Decimal) -> Transacao:
    """Executa a transferência atômica entre duas contas bancárias.

    Garante que os saldos sejam atualizados sob lock (select_for_update) dentro de
    uma transação atômica do banco de dados, criando o registro de auditoria da Transacao.

    Args:
        origem_id: ID da conta que enviará o recurso.
        destino_id: ID da conta que receberá o recurso.
        valor: Montante a ser transferido.

    Returns:
        Instância de Transacao persistida no banco de dados.

    Raises:
        ContaInativaException: Se alguma das contas estiver bloqueada.
        SaldoInsuficienteException: Se a conta de origem não possuir fundos suficientes.
    """
    # Buscamos as instâncias aplicando lock para evitar condições de corrida em concorrência
    origem: Conta = Conta.objects.select_for_update().get(id=origem_id)
    destino: Conta = Conta.objects.select_for_update().get(id=destino_id)

    # Validação manual desacoplada antes da mutação
    _validar_transferencia(origem=origem, destino=destino, valor=valor)

    # Execução das mutações
    origem.saldo -= valor
    origem.save(update_fields=["saldo", "atualizado_em"])

    destino.saldo += valor
    destino.save(update_fields=["saldo", "atualizado_em"])

    # Criação do registro formal de auditoria
    transacao: Transacao = Transacao.objects.create(
        origem=origem,
        destino=destino,
        valor=valor,
    )

    return transacao
```

---

### 4. Camada de Views (FBVs com Decorators) (`views.py`)

```python
"""Endpoints HTTP implementados prioritariamente como Function-Based Views (FBVs)."""

from decimal import Decimal
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from financeiro import services, selectors
from financeiro.exceptions import SaldoInsuficienteException, ContaInativaException


@login_required
def transferir_fundos_view(request: HttpRequest) -> HttpResponse:
    """Processa a solicitação de transferência bancária via POST ou exibe o formulário via GET.

    Args:
        request: Requisição HTTP recebida pelo Django.

    Returns:
        HttpResponse renderizada com formulário ou redirecionamento pós-sucesso.
    """
    if request.method == "POST":
        try:
            destino_id: int = int(request.POST.get("destino_id", 0))
            valor: Decimal = Decimal(request.POST.get("valor", "0.00"))

            # Delegamos estritamente a execução para a camada de serviço
            transacao = services.realizar_transferencia(
                origem_id=request.user.conta.id,
                destino_id=destino_id,
                valor=valor,
            )
            return redirect("financeiro:detalhe_transacao", transacao_id=transacao.id)

        except (SaldoInsuficienteException, ContaInativaException, ValueError) as err:
            # Tratamento amigável das exceções de negócio na camada de apresentação
            return render(
                request,
                "financeiro/transferir.html",
                {"erro": str(err)},
                status=400,
            )

    # No fluxo GET, consultamos dados apenas através de selectors
    transacoes_recentes = selectors.listar_transacoes_da_conta(conta_id=request.user.conta.id)
    return render(request, "financeiro/transferir.html", {"transacoes": transacoes_recentes})
```
