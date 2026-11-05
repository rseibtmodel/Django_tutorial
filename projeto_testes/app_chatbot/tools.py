"""Módulo de ferramentas (Tool Calling / Function Calling) seguras para o Chatbot.

Define ferramentas executáveis pelo Gemini de forma estritamente controlada,
sem risco de Remote Code Execution (RCE) ou injeções arbitrárias de SQL.
"""

import ast
import logging
import operator
from datetime import datetime
from typing import Any, Callable, Optional, Union
from zoneinfo import ZoneInfo
from django.utils import timezone

from .models import SessaoChat

logger = logging.getLogger(__name__)

# Operadores matemáticos estritamente permitidos para avaliação por AST
OPERADORES_ARITMETICOS: dict[type, Callable[..., Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def avaliar_expressao_matematica_segura(expressao: str) -> str:
    """Avalia expressões matemáticas puramente numéricas com segurança absoluta via AST.

    Analisa a árvore sintática abstrata (AST) rejeitando sumariamente variáveis,
    chamadas de métodos, imports e acessos de atributos.

    Args:
        expressao: Expressão aritmética como string (ex: '((25 * 4) + 10) / 2').

    Returns:
        str: Resultado do cálculo formatado ou mensagem de erro explicativa.
    """
    expressao_limpa = expressao.strip()
    if not expressao_limpa:
        return "Erro: Expressão matemática vazia."

    if len(expressao_limpa) > 200:
        return "Erro: Expressão excede o limite máximo de 200 caracteres."

    try:
        arvore = ast.parse(expressao_limpa, mode="eval")
    except SyntaxError as e_syn:
        return f"Erro de sintaxe na expressão matemática: {e_syn.msg}."

    # Varredura anti-código: bloqueia qualquer nó perigoso antes da avaliação
    for no in ast.walk(arvore):
        if isinstance(
            no,
            (
                ast.Call,
                ast.Attribute,
                ast.Name,
                ast.Import,
                ast.ImportFrom,
                ast.Lambda,
                ast.ListComp,
                ast.DictComp,
                ast.SetComp,
                ast.GeneratorExp,
            ),
        ):
            return f"Operação bloqueada por segurança: o elemento '{type(no).__name__}' não é permitido."

    def _avaliar_no(no_atual: ast.AST) -> Union[int, float]:
        if isinstance(no_atual, ast.Expression):
            return _avaliar_no(no_atual.body)
        if isinstance(no_atual, ast.Constant):
            if isinstance(no_atual.value, (int, float)):
                return no_atual.value
            raise ValueError(f"Constante não numérica '{no_atual.value}' rejeitada.")
        if isinstance(no_atual, ast.BinOp):
            tipo_op = type(no_atual.op)
            if tipo_op not in OPERADORES_ARITMETICOS:
                raise ValueError(f"Operador binário '{tipo_op.__name__}' não suportado.")
            esq = _avaliar_no(no_atual.left)
            dir_val = _avaliar_no(no_atual.right)
            if tipo_op == ast.Pow and (dir_val > 1000 or dir_val < -1000):
                raise ValueError("Expoente excessivo fora do limite de segurança (máx 1000).")
            if tipo_op in (ast.Div, ast.FloorDiv, ast.Mod) and dir_val == 0:
                raise ZeroDivisionError("Divisão por zero não é permitida.")
            return OPERADORES_ARITMETICOS[tipo_op](esq, dir_val)
        if isinstance(no_atual, ast.UnaryOp):
            tipo_unario = type(no_atual.op)
            if tipo_unario not in OPERADORES_ARITMETICOS:
                raise ValueError(f"Operador unário '{tipo_unario.__name__}' não suportado.")
            return OPERADORES_ARITMETICOS[tipo_unario](_avaliar_no(no_atual.operand))
        raise ValueError(f"Elemento de sintaxe '{type(no_atual).__name__}' rejeitado.")

    try:
        resultado = _avaliar_no(arvore)
        # Formata inteiros sem casas decimais supérfluas
        if isinstance(resultado, float) and resultado.is_integer():
            resultado = int(resultado)
        return str(resultado)
    except ZeroDivisionError:
        return "Erro matemático: Divisão por zero."
    except Exception as erro:
        return f"Erro ao calcular expressão: {str(erro)}."


def obter_data_e_hora_oficial() -> str:
    """Retorna a data e o horário oficial do sistema no fuso horário do Brasil.

    Use esta ferramenta sempre que o usuário perguntar que horas são, a data de hoje,
    o dia da semana atual ou solicitar cálculos de prazos e datas.

    Returns:
        str: Texto formatado com data, hora e fuso horário oficial.
    """
    logger.info("Ferramenta 'obter_data_e_hora_oficial' invocada pelo assistente.")
    try:
        fuso_br = ZoneInfo("America/Sao_Paulo")
        agora = timezone.now().astimezone(fuso_br)
    except Exception:
        agora = timezone.now()

    dias_semana = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]
    dia_extenso = dias_semana[agora.weekday()]
    formato_humano = agora.strftime("%d/%m/%Y às %H:%M:%S")
    formato_iso = agora.isoformat()

    return f"Data e hora oficial: {dia_extenso}, {formato_humano} (Fuso: America/Sao_Paulo, ISO: {formato_iso})."


def executar_calculo_matematico(expressao: str) -> str:
    """Executa cálculos matemáticos de forma exata e segura via analisador sintático.

    Use esta ferramenta para resolver expressões numéricas, regras de três, porcentagens,
    potências ou contas financeiras sem cometer erros de cálculo de LLM.

    Args:
        expressao: A fórmula ou expressão aritmética a ser calculada (ex: '1500 * (1 - 0.15)' ou '(45 + 12) * 3').

    Returns:
        str: O resultado numérico exato ou uma descrição do erro.
    """
    logger.info("Ferramenta 'executar_calculo_matematico' invocada com: %s", expressao)
    resultado = avaliar_expressao_matematica_segura(expressao)
    return f"Resultado do cálculo '{expressao}': {resultado}"


def obter_ferramentas_para_sessao(sessao: SessaoChat) -> list[Callable[..., Any]]:
    """Gera o catálogo de ferramentas ativas vinculadas com segurança à sessão informada.

    Isola as consultas ao escopo estrito da sessão e do usuário autenticado (anti-IDOR).

    Args:
        sessao: Instância da sessão de chat em execução.

    Returns:
        list[Callable[..., Any]]: Lista de callables prontos para serem consumidos pelo Gemini SDK.
    """
    def consultar_documentos_sessao() -> str:
        """Retorna a lista e o status de todos os documentos anexados para RAG nesta conversa.

        Use esta ferramenta se o usuário perguntar quais arquivos foram anexados ou sobre o que versam os documentos.

        Returns:
            str: Relação estruturada de documentos disponíveis nesta sessão.
        """
        logger.info("Ferramenta 'consultar_documentos_sessao' invocada para sessao %s", sessao.id)
        docs = sessao.documentos.all().order_by("nome_original")
        if not docs.exists():
            return "Nenhum documento anexado nesta sessão de chat até o momento."

        linhas = [f"Total de documentos indexados: {docs.count()}"]
        for d in docs:
            tamanho_kb = round(d.tamanho_bytes / 1024, 1)
            linhas.append(f"- Arquivo: '{d.nome_original}' ({tamanho_kb} KB, {d.total_chunks} chunks indexados)")
        return "\n".join(linhas)

    def obter_informacoes_sessao() -> str:
        """Retorna os metadados da sessão de chat ativa e da persona vinculada.

        Use esta ferramenta para obter o título da conversa, quem é a persona ativa e quantas mensagens foram trocadas.

        Returns:
            str: Metadados consolidados da conversa.
        """
        logger.info("Ferramenta 'obter_informacoes_sessao' invocada para sessao %s", sessao.id)
        nome_persona = sessao.persona.nome if sessao.persona else "Assistente Padrão"
        total_mensagens = sessao.mensagens.count()
        criado = sessao.criado_em.strftime("%d/%m/%Y %H:%M")
        return (
            f"Sessão ID: {str(sessao.id)[:8]}\n"
            f"Título: '{sessao.titulo}'\n"
            f"Persona Ativa: {nome_persona}\n"
            f"Criada em: {criado}\n"
            f"Total de turnos de mensagem registrados: {total_mensagens}"
        )

    def consultar_telemetria_operador() -> str:
        """Retorna as métricas de consumo de tokens e custos estimados do operador na aplicação.

        Use esta ferramenta quando o usuário perguntar sobre gastos, cotas, tokens consumidos ou estatísticas de uso.

        Returns:
            str: Resumo de métricas de telemetria do usuário.
        """
        logger.info("Ferramenta 'consultar_telemetria_operador' invocada para sessao %s", sessao.id)
        if not sessao.usuario:
            return "Operador não autenticado (sessão anônima): telemetria individual indisponível."

        from .selectors import obter_metricas_telemetria_usuario
        metricas = obter_metricas_telemetria_usuario(usuario=sessao.usuario)
        return (
            f"Métricas do Operador @{sessao.usuario.username}:\n"
            f"- Total de conversas: {metricas.get('total_sessoes', 0)}\n"
            f"- Mensagens trocadas: {metricas.get('total_mensagens', 0)}\n"
            f"- Tokens consumidos: {metricas.get('total_tokens', 0):,}\n"
            f"- Custo financeiro estimado da API: ${metricas.get('custo_total_usd', 0.0):.4f} USD\n"
            f"- Documentos RAG ativos: {metricas.get('total_documentos', 0)}"
        )

    def registrar_transacao_financeira(
        tipo: str,
        valor: str,
        descricao: str,
        categoria: str = "outros",
        data_competencia: str = "",
    ) -> str:
        """Registra uma nova receita (crédito) ou despesa (débito) nas finanças do usuário autenticado.

        Use esta ferramenta quando o usuário pedir para registrar, anotar, lançar ou salvar um gasto,
        despesa, compra, receita, salário, pagamento ou ganho financeiro.

        Args:
            tipo: 'DESPESA' para saídas/gastos ou 'RECEITA' para entradas/ganhos.
            valor: Valor monetário como texto (ex: '45.00', '150,50', '1200').
            descricao: Descrição detalhada do que foi comprado ou recebido.
            categoria: Categoria opcional (ex: alimentacao, moradia, transporte, lazer, salario, freela).
            data_competencia: Data opcional no formato AAAA-MM-DD (se omitida, usa a data de hoje).

        Returns:
            str: Confirmação contábil do registro com ID e valor ou mensagem de erro.
        """
        logger.info("Ferramenta 'registrar_transacao_financeira' invocada para sessao %s", sessao.id)
        if not sessao.usuario:
            return "Erro: Operador não autenticado (sessão anônima). Impossível registrar finanças."

        try:
            from app_financas.services import criar_lancamento
            lancamento = criar_lancamento(
                usuario=sessao.usuario,
                tipo=tipo,
                valor=valor,
                descricao=descricao,
                categoria=categoria,
                data_competencia=data_competencia if data_competencia else None,
            )
            sinal = "+" if lancamento.tipo == lancamento.TIPO_RECEITA else "-"
            return (
                f"Transação contábil registrada com sucesso no banco de dados local!\n"
                f"- ID: #{lancamento.id}\n"
                f"- Tipo: {lancamento.tipo}\n"
                f"- Valor: {sinal}R$ {lancamento.valor:.2f}\n"
                f"- Categoria: {lancamento.categoria}\n"
                f"- Descrição: {lancamento.descricao}\n"
                f"- Data de Competência: {lancamento.data_competencia.strftime('%d/%m/%Y')}"
            )
        except Exception as err:
            logger.warning("Falha ao registrar transação financeira via ferramenta: %s", err)
            return f"Erro ao registrar transação financeira: {str(err)}"

    def consultar_extrato_financeiro(
        ano: int = 0,
        mes: int = 0,
        categoria: str = "",
    ) -> str:
        """Consulta o extrato financeiro, saldo, total de receitas, despesas e lançamentos do usuário.

        Use esta ferramenta quando o usuário perguntar quanto gastou no mês, qual é seu saldo,
        seus maiores gastos, extrato, fluxo de caixa ou transações financeiras.

        Args:
            ano: Ano de competência numérico (ex: 2026). Se 0, utiliza o ano atual.
            mes: Mês de competência (1 a 12). Se 0, utiliza o mês atual.
            categoria: Filtro opcional por slug de categoria (ex: 'alimentacao', 'transporte').

        Returns:
            str: Resumo orçamentário do período com lista das transações encontradas.
        """
        logger.info("Ferramenta 'consultar_extrato_financeiro' invocada para sessao %s", sessao.id)
        if not sessao.usuario:
            return "Erro: Operador não autenticado (sessão anônima). Impossível consultar finanças."

        try:
            from app_financas.selectors import calcular_balanco_periodo, obter_extrato_mensal
            agora = timezone.localdate()
            ano_final = ano if ano > 0 else agora.year
            mes_final = mes if 1 <= mes <= 12 else agora.month

            balanco = calcular_balanco_periodo(
                usuario=sessao.usuario,
                ano=ano_final,
                mes=mes_final,
            )
            lancamentos = obter_extrato_mensal(
                usuario=sessao.usuario,
                ano=ano_final,
                mes=mes_final,
                categoria=categoria if categoria else None,
            )

            linhas = [
                f"=== BALANÇO FINANCEIRO LOCAL ({mes_final:02d}/{ano_final}) ===",
                f"- Saldo Líquido: R$ {balanco['saldo_liquido']}",
                f"- Total de Receitas (+): R$ {balanco['total_receitas']}",
                f"- Total de Despesas (-): R$ {balanco['total_despesas']}",
                f"- Taxa de Poupança: {balanco['taxa_poupanca']}%",
                f"- Total de Lançamentos: {balanco['total_lancamentos']}",
            ]

            transacoes_recentes = list(lancamentos[:15])
            if transacoes_recentes:
                linhas.append("\nÚltimos Lançamentos:")
                for l in transacoes_recentes:
                    sinal = "+" if l.tipo == l.TIPO_RECEITA else "-"
                    linhas.append(
                        f"  * #{l.id} [{l.data_competencia.strftime('%d/%m')}] {sinal}R$ {l.valor:.2f} "
                        f"({l.categoria}): {l.descricao}"
                    )
            else:
                linhas.append("\n(Nenhum lançamento registrado nesta competência)")

            return "\n".join(linhas)
        except Exception as err:
            logger.warning("Falha ao consultar extrato financeiro via ferramenta: %s", err)
            return f"Erro ao consultar extrato financeiro: {str(err)}"

    # Retorna o catálogo completo de ferramentas ativas
    return [
        obter_data_e_hora_oficial,
        executar_calculo_matematico,
        consultar_documentos_sessao,
        obter_informacoes_sessao,
        consultar_telemetria_operador,
        registrar_transacao_financeira,
        consultar_extrato_financeiro,
    ]

