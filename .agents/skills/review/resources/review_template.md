# Template Oficial de Revisão de Código

Apresente a revisão com uma introdução ácida e contextualizada sobre os arquivos inspecionados, seguida pelos itens agrupados e numerados sequencialmente.

```markdown
# 🔬 Relatório de Code Review — Tech Lead

**Arquivo(s) Analisado(s):** `caminho/do/arquivo.py`  
**Arquivos de Apoio Inspecionados:** `caminho/do/relacionado.py`  
**Status Geral:** [APROVADO COM RESSALVAS | REPROVADO PARA PRODUÇÃO]

---

### Resumo Executivo
[Breve parágrafo destilando o sarcasmo técnico necessário, resumindo o estado geral do código e seus maiores crimes contra a computação moderna.]

---

### Apontamentos Técnicos

#### 1. `[CRÍTICO]` Consulta N+1 em loop dentro de view/serializer
- **Código Original:**
```python
for item in pedido.itens.all():
    total += item.produto.preco * item.quantidade
```
- **Diagnóstico & Crítica:**
  Parabéns, você acabou de inventar uma máquina de fritar banco de dados. Iterar sobre uma relação sem `select_related` dentro de um laço de repetição dispara uma query SQL individual por item. Para um pedido com 100 itens, são 101 queries. O DBA já está chorando no canto da sala.
- **Impacto:**
  Degradação exponencial da latência conforme a base cresce, exaustão do pool de conexões do PostgreSQL e tempo de resposta inaceitável.
- **Refatoração Sugerida:**
```python
# No queryset inicial ou prefetch:
pedido = Pedido.objects.prefetch_related(
    Prefetch("itens", queryset=ItemPedido.objects.select_related("produto"))
).get(id=pedido_id)

# Ou calculando via agregação no próprio banco:
from django.db.models import F, Sum

total = pedido.itens.aggregate(
    total=Sum(F("produto__preco") * F("quantidade"))
)["total"] or Decimal("0.00")
```

---

#### 2. `[ALERTA]` Regra de negócio orquestrada dentro de View Django
- **Código Original:**
```python
class ProcessarPagamentoView(APIView):
    def post(self, request):
        # 50 linhas manipulando saldo, chamando gateway de pagamento e enviando email
```
- **Diagnóstico & Crítica:**
  A clássica "Fat View". Views devem apenas orquestrar HTTP (validar entrada, chamar serviço de domínio, responder status HTTP). Quando você coloca transações financeiras e chamadas de API externa no handler da view, você assassina a testabilidade unitária e viola o princípio da responsabilidade única.
- **Impacto:**
  Impossibilidade de reutilizar a lógica em tasks assíncronas (Celery) ou comandos de CLI (`management commands`), além de testes lentos e frágeis.
- **Refatoração Sugerida:**
```python
# services/pagamento_service.py
class PagamentoService:
    @classmethod
    @transaction.atomic
    def processar(cls, *, pedido_id: int, cartao_token: str) -> Transacao:
        ...

# views.py
class ProcessarPagamentoView(APIView):
    def post(self, request):
        serializer = PagamentoInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transacao = PagamentoService.processar(**serializer.validated_data)
        return Response(TransacaoSerializer(transacao).data, status=status.HTTP_200_OK)
```

---

### Propostas de Arquitetura (Opcional / Consultivo)
[Sugestões estruturais de maior porte, como extração de camada de Service, criação de Custom QuerySets ou isolamento de pipelines de LLM.]

> ⚠️ **Lembrete:** Nenhuma refatoração ou patch foi aplicado. Para prosseguir com quaisquer alterações em seus arquivos, solicite explicitamente no chat.
```
