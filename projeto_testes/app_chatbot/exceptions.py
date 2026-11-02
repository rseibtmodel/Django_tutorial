"""Exceções de domínio do aplicativo de Chatbot."""


class ChatbotException(Exception):
    """Exceção base para todas as falhas de domínio do Chatbot."""
    pass


class TituloInvalidoError(ChatbotException):
    """Lançada quando um título fornecido viola regras de validação ou segurança."""
    pass


class InferenciaAIError(ChatbotException):
    """Lançada quando a comunicação ou geração com o modelo de IA falha."""
    pass


class SessaoNaoEncontradaError(ChatbotException):
    """Lançada quando uma sessão solicitada não existe ou não pertence ao usuário."""
    pass


class PersonaInvalidaError(ChatbotException):
    """Lançada quando a persona selecionada ou editada é inválida ou não pertence ao usuário."""
    pass


class DocumentoInvalidoError(ChatbotException):
    """Lançada quando o documento enviado excede tamanho, formato ou limites de segurança."""
    pass


class PerfilInvalidoError(ChatbotException):
    """Lançada quando dados do perfil do usuário violam regras de validação."""
    pass
