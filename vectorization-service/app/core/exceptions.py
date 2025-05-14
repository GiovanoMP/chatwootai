"""
Exceções personalizadas para o serviço de vetorização.
"""

class VectorizationServiceError(Exception):
    """Exceção base para erros do serviço de vetorização."""
    
    def __init__(self, message: str, code: str = "VECTORIZATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class VectorDBError(VectorizationServiceError):
    """Exceção para erros relacionados ao banco de dados vetorial."""
    
    def __init__(self, message: str, code: str = "VECTOR_DB_ERROR"):
        super().__init__(message, code)

class EmbeddingError(VectorizationServiceError):
    """Exceção para erros relacionados à geração de embeddings."""
    
    def __init__(self, message: str, code: str = "EMBEDDING_ERROR"):
        super().__init__(message, code)

class ValidationError(VectorizationServiceError):
    """Exceção para erros de validação."""
    
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: dict = None):
        self.details = details
        super().__init__(message, code)

class CacheError(VectorizationServiceError):
    """Exceção para erros relacionados ao cache."""
    
    def __init__(self, message: str, code: str = "CACHE_ERROR"):
        super().__init__(message, code)
