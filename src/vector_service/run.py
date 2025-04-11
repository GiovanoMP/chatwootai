#!/usr/bin/env python
"""
Script para iniciar o serviço de vetorização.
"""

import os
import uvicorn
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Função principal para iniciar o serviço de vetorização.
    """
    # Verificar variáveis de ambiente necessárias
    required_vars = ["OPENAI_API_KEY", "QDRANT_HOST"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before starting the service")
        return 1
    
    # Obter configurações do ambiente
    host = os.environ.get("VECTOR_SERVICE_HOST", "0.0.0.0")
    port = int(os.environ.get("VECTOR_SERVICE_PORT", 8001))
    reload = os.environ.get("VECTOR_SERVICE_RELOAD", "false").lower() == "true"
    
    # Exibir informações de configuração
    logger.info(f"Starting Vector Service on {host}:{port}")
    logger.info(f"OpenAI API Key: {'Configured' if os.environ.get('OPENAI_API_KEY') else 'Not Configured'}")
    logger.info(f"Qdrant Host: {os.environ.get('QDRANT_HOST', 'localhost')}")
    logger.info(f"Redis Enabled: {os.environ.get('REDIS_ENABLED', 'true')}")
    
    # Iniciar servidor
    uvicorn.run(
        "src.vector_service.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
    
    return 0

if __name__ == "__main__":
    exit(main())
