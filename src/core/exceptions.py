"""
Módulo de exceções personalizadas para o sistema ChatwootAI.

Este módulo define exceções específicas que são usadas em todo o sistema para
sinalizar diferentes tipos de erros de forma clara e tratável.

Benefícios de usar exceções personalizadas:
1. Maior clareza sobre o tipo de erro que ocorreu
2. Capacidade de tratar diferentes tipos de erros de forma específica
3. Melhor documentação do comportamento esperado do sistema
4. Facilita a depuração e o logging estruturado
"""

class ChatwootAIBaseException(Exception):
    """Exceção base para todas as exceções do sistema ChatwootAI."""
    pass


class ConfigurationError(ChatwootAIBaseException):
    """
    Exceção lançada quando há um problema de configuração no sistema.
    
    Exemplos:
    - Parâmetros de configuração ausentes ou inválidos
    - Dependências não configuradas corretamente
    - Arquivos de configuração corrompidos ou inacessíveis
    """
    pass


class DataAccessError(ChatwootAIBaseException):
    """
    Exceção lançada quando ocorre um erro ao acessar dados.
    
    Exemplos:
    - Falha na conexão com banco de dados
    - Erro ao consultar API externa
    - Timeout em requisições de dados
    - Dados corrompidos ou em formato inesperado
    """
    pass


class SecurityViolationError(ChatwootAIBaseException):
    """
    Exceção lançada quando ocorre uma violação de segurança.
    
    Exemplos:
    - Tentativa de acesso não autorizado
    - Falha na validação de assinatura de webhook
    - Token de autenticação inválido ou expirado
    """
    pass


class BusinessRuleViolationError(ChatwootAIBaseException):
    """
    Exceção lançada quando uma regra de negócio é violada.
    
    Exemplos:
    - Tentativa de criar um registro duplicado
    - Operação em um estado inválido
    - Violação de restrições de domínio
    """
    pass


class IntegrationError(ChatwootAIBaseException):
    """
    Exceção lançada quando ocorre um erro na integração com sistemas externos.
    
    Exemplos:
    - Falha na comunicação com Chatwoot
    - Erro na integração com WhatsApp
    - Resposta inesperada de API externa
    """
    pass
