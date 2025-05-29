"""
Utilitários para logging.
Configura e fornece loggers para o sistema.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Diretório de logs
LOG_DIR = os.environ.get('LOG_DIR', 'logs')

# Formato do log
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Nível de log padrão
DEFAULT_LOG_LEVEL = logging.INFO

def setup_logger():
    """
    Configura o logger principal do sistema.
    
    Returns:
        Logger configurado
    """
    # Cria o diretório de logs se não existir
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Configura o logger raiz
    logger = logging.getLogger()
    logger.setLevel(DEFAULT_LOG_LEVEL)
    
    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Adiciona handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # Adiciona handler para arquivo
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'chatwoot_mcp_connector.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name=None):
    """
    Obtém um logger para um módulo específico.
    
    Args:
        name: Nome do módulo
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
