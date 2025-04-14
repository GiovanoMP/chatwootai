# -*- coding: utf-8 -*-

"""
Exceções personalizadas para a API Odoo.
"""

class OdooAPIError(Exception):
    """Classe base para exceções da API Odoo."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or "ODOO_API_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class OdooConnectionError(OdooAPIError):
    """Exceção para erros de conexão com o Odoo."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "ODOO_CONNECTION_ERROR", details)


class OdooAuthenticationError(OdooAPIError):
    """Exceção para erros de autenticação com o Odoo."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "ODOO_AUTHENTICATION_ERROR", details)


class OdooOperationError(OdooAPIError):
    """Exceção para erros de operação no Odoo."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "ODOO_OPERATION_ERROR", details)


class ValidationError(OdooAPIError):
    """Exceção para erros de validação."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class NotFoundError(OdooAPIError):
    """Exceção para recursos não encontrados."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "NOT_FOUND_ERROR", details)


class DatabaseError(OdooAPIError):
    """Exceção para erros de banco de dados."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "DATABASE_ERROR", details)


class CacheError(OdooAPIError):
    """Exceção para erros de cache."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "CACHE_ERROR", details)


class VectorDBError(OdooAPIError):
    """Exceção para erros de banco de dados vetorial."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VECTOR_DB_ERROR", details)


class ConfigurationError(OdooAPIError):
    """Exceção para erros de configuração."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class AuthorizationError(OdooAPIError):
    """Exceção para erros de autorização."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class RateLimitError(OdooAPIError):
    """Exceção para erros de limite de taxa."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class ServiceUnavailableError(OdooAPIError):
    """Exceção para serviços indisponíveis."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "SERVICE_UNAVAILABLE_ERROR", details)
