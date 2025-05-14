"""
Funções de autenticação para o serviço de vetorização.
"""

import logging
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

def verify_api_key(api_key: str) -> bool:
    """
    Verifica se a API key é válida.
    
    Args:
        api_key: API key a ser verificada
        
    Returns:
        True se a API key for válida
        
    Raises:
        HTTPException: Se a API key for inválida
    """
    if api_key != settings.API_KEY:
        logger.warning(f"Tentativa de acesso com API key inválida: {api_key[:5]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida"
        )
    return True
