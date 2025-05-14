"""
Configuração de logging para o serviço de vetorização.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

from app.core.config import settings

# Criar diretório de logs se não existir
logs_dir = Path("./logs")
logs_dir.mkdir(exist_ok=True)

# Nome do arquivo de log baseado na data
log_filename = logs_dir / f"vectorization_service_{datetime.now().strftime('%Y%m%d')}.log"

# Formatos de log
CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

def setup_logging():
    """Configura o sistema de logging."""
    # Obter nível de log das configurações
    log_level_str = settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else "INFO"
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remover handlers existentes para evitar duplicação
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para arquivo com rotação por tamanho
    file_handler = RotatingFileHandler(
        filename=log_filename,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(FILE_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Handler para arquivo com rotação diária
    daily_handler = TimedRotatingFileHandler(
        filename=logs_dir / "vectorization_service.log",
        when="midnight",
        interval=1,
        backupCount=30,  # Manter logs por 30 dias
        encoding="utf-8"
    )
    daily_handler.setLevel(log_level)
    daily_handler.setFormatter(file_formatter)
    root_logger.addHandler(daily_handler)
    
    # Configurar loggers específicos
    # Reduzir verbosidade de bibliotecas externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Logger para operações críticas
    critical_logger = logging.getLogger("vectorization.critical")
    critical_handler = RotatingFileHandler(
        filename=logs_dir / "critical.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=10,
        encoding="utf-8"
    )
    critical_handler.setLevel(logging.ERROR)
    critical_handler.setFormatter(file_formatter)
    critical_logger.addHandler(critical_handler)
    
    # Logger para operações de sincronização
    sync_logger = logging.getLogger("vectorization.sync")
    sync_handler = RotatingFileHandler(
        filename=logs_dir / "sync_operations.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    sync_handler.setLevel(logging.INFO)
    sync_handler.setFormatter(file_formatter)
    sync_logger.addHandler(sync_handler)
    
    # Logger para operações de embedding
    embedding_logger = logging.getLogger("vectorization.embedding")
    embedding_handler = RotatingFileHandler(
        filename=logs_dir / "embedding_operations.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    embedding_handler.setLevel(logging.INFO)
    embedding_handler.setFormatter(file_formatter)
    embedding_logger.addHandler(embedding_handler)
    
    logging.info("Sistema de logging configurado")
    return root_logger
