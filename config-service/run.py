#!/usr/bin/env python3
"""
Script para iniciar o microserviço de configuração.
"""

import uvicorn
import logging
import os

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "config_service.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("config-service")
logger.info("Iniciando serviço de configuração...")

if __name__ == "__main__":
    logger.info("Conectando ao banco de dados: postgresql://postgres:postgres@localhost:5433/config_service")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True, log_config=None)
