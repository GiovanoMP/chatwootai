"""
Cliente Qdrant

Este módulo contém funções para criar e gerenciar o cliente Qdrant.
"""

import os
from qdrant_client import QdrantClient
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis globais
_qdrant_client = None

def get_qdrant_client():
    """
    Obtém uma instância do cliente Qdrant.
    
    Returns:
        QdrantClient: Cliente Qdrant configurado
    """
    global _qdrant_client
    
    if _qdrant_client is not None:
        return _qdrant_client
    
    # Obter configurações do ambiente
    qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
    qdrant_port = int(os.environ.get("QDRANT_PORT", 6333))
    qdrant_grpc_port = int(os.environ.get("QDRANT_GRPC_PORT", 6334))
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    qdrant_https = os.environ.get("QDRANT_HTTPS", "false").lower() == "true"
    
    # Configurar cliente
    try:
        if qdrant_api_key:
            logger.info(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port} with API key")
            _qdrant_client = QdrantClient(
                host=qdrant_host,
                port=qdrant_port,
                grpc_port=qdrant_grpc_port,
                api_key=qdrant_api_key,
                https=qdrant_https
            )
        else:
            logger.info(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port} without API key")
            _qdrant_client = QdrantClient(
                host=qdrant_host,
                port=qdrant_port,
                grpc_port=qdrant_grpc_port,
                https=qdrant_https
            )
        
        # Verificar conexão
        _qdrant_client.get_collections()
        logger.info("Successfully connected to Qdrant")
        
        return _qdrant_client
    except Exception as e:
        logger.error(f"Error connecting to Qdrant: {str(e)}")
        raise
