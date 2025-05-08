from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

# Definir o cabeçalho de autenticação
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    """
    Valida a chave de API fornecida no cabeçalho.
    
    Args:
        api_key_header: Chave de API fornecida no cabeçalho
        
    Returns:
        A chave de API se for válida
        
    Raises:
        HTTPException: Se a chave de API for inválida ou não fornecida
    """
    if api_key_header == settings.API_KEY:
        return api_key_header
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Chave de API inválida ou não fornecida",
        headers={"WWW-Authenticate": "ApiKey"},
    )
