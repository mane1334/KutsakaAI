"""
Exceções customizadas do Agente IA
"""

class AgenteError(Exception):
    """Exceção base para erros do agente."""
    pass

class ConfigError(AgenteError):
    """Erro de configuração."""
    pass

class LLMError(AgenteError):
    """Erro na comunicação com o modelo de linguagem."""
    pass

class ToolError(AgenteError):
    """Erro no uso de uma ferramenta."""
    pass

class SecurityError(AgenteError):
    """Erro de segurança."""
    pass

class ValidationError(AgenteError):
    """Erro de validação."""
    pass

class FileError(ToolError):
    """Erro na manipulação de arquivos."""
    pass

class WebError(ToolError):
    """Erro em operações web."""
    pass

class CommandError(ToolError):
    """Erro na execução de comandos."""
    pass

class HistoryError(AgenteError):
    """Erro no gerenciamento de histórico."""
    pass

class ModelError(LLMError):
    """Erro específico do modelo."""
    pass

class ConnectionError(LLMError):
    """Erro de conexão com o servidor."""
    pass

class TimeoutError(LLMError):
    """Erro de timeout na comunicação."""
    pass

class AuthenticationError(LLMError):
    """Erro de autenticação."""
    pass

class RateLimitError(LLMError):
    """Erro de limite de requisições."""
    pass

class ParsingError(AgenteError):
    """Erro no parsing de mensagens ou respostas."""
    pass

class StateError(AgenteError):
    """Erro no estado do agente."""
    pass

class CallbackError(AgenteError):
    """Erro em callbacks."""
    pass

class LoggingError(AgenteError):
    """Erro no sistema de logging."""
    pass 