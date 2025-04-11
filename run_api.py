#!/usr/bin/env python3
"""
Script para iniciar a API REST.

Este script inicia a aplicação FastAPI usando uvicorn.

Autor: Augment Agent
Data: 26/03/2025
"""

import uvicorn
import argparse
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Função principal para iniciar a API."""
    parser = argparse.ArgumentParser(description="Iniciar a API REST do ChatwootAI")
    parser.add_argument("--host", default="0.0.0.0", help="Host para bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Porta para bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Ativar reload automático")
    parser.add_argument("--workers", type=int, default=1, help="Número de workers (default: 1)")
    parser.add_argument("--log-level", default="info", help="Nível de log (default: info)")
    
    args = parser.parse_args()
    
    logger.info(f"Iniciando API REST em {args.host}:{args.port}")
    logger.info(f"Configurações: reload={args.reload}, workers={args.workers}, log-level={args.log_level}")
    
    uvicorn.run(
        "src.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()
