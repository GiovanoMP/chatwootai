#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para configurar o sistema de logs do servidor unificado.

Este script configura o sistema de logs para o servidor unificado,
criando os arquivos de log necessários e configurando os handlers
para registrar mensagens detalhadas.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

# Configurações
LOG_DIR = "logs"
SERVER_LOG = "server.log"
WEBHOOK_LOG = "webhook.log"
HUB_LOG = "hub.log"
ODOO_API_LOG = "odoo_api.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

def setup_logging():
    """Configura o sistema de logs."""
    # Criar diretório de logs se não existir
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"✅ Diretório de logs criado: {LOG_DIR}")
    
    # Configurar formato de log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configurar handler para o console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    
    # Configurar handler para o log do servidor
    server_log_path = os.path.join(LOG_DIR, SERVER_LOG)
    server_handler = logging.handlers.RotatingFileHandler(
        server_log_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT
    )
    server_handler.setFormatter(log_format)
    server_handler.setLevel(logging.DEBUG)
    
    # Configurar handler para o log do webhook
    webhook_log_path = os.path.join(LOG_DIR, WEBHOOK_LOG)
    webhook_handler = logging.handlers.RotatingFileHandler(
        webhook_log_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT
    )
    webhook_handler.setFormatter(log_format)
    webhook_handler.setLevel(logging.DEBUG)
    
    # Configurar handler para o log do hub
    hub_log_path = os.path.join(LOG_DIR, HUB_LOG)
    hub_handler = logging.handlers.RotatingFileHandler(
        hub_log_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT
    )
    hub_handler.setFormatter(log_format)
    hub_handler.setLevel(logging.DEBUG)
    
    # Configurar handler para o log da API Odoo
    odoo_api_log_path = os.path.join(LOG_DIR, ODOO_API_LOG)
    odoo_api_handler = logging.handlers.RotatingFileHandler(
        odoo_api_log_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT
    )
    odoo_api_handler.setFormatter(log_format)
    odoo_api_handler.setLevel(logging.DEBUG)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(server_handler)
    
    # Configurar logger para o webhook
    webhook_logger = logging.getLogger('src.webhook')
    webhook_logger.setLevel(logging.DEBUG)
    webhook_logger.addHandler(webhook_handler)
    
    # Configurar logger para o hub
    hub_logger = logging.getLogger('src.core.hub')
    hub_logger.setLevel(logging.DEBUG)
    hub_logger.addHandler(hub_handler)
    
    # Configurar logger para a API Odoo
    odoo_api_logger = logging.getLogger('odoo_api')
    odoo_api_logger.setLevel(logging.DEBUG)
    odoo_api_logger.addHandler(odoo_api_handler)
    
    # Registrar início da configuração
    root_logger.info("🔧 Sistema de logs configurado")
    webhook_logger.info("🔧 Logger do webhook configurado")
    hub_logger.info("🔧 Logger do hub configurado")
    odoo_api_logger.info("🔧 Logger da API Odoo configurado")
    
    print(f"✅ Sistema de logs configurado com sucesso")
    print(f"📝 Log do servidor: {server_log_path}")
    print(f"📝 Log do webhook: {webhook_log_path}")
    print(f"📝 Log do hub: {hub_log_path}")
    print(f"📝 Log da API Odoo: {odoo_api_log_path}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔧 CONFIGURANDO SISTEMA DE LOGS")
    print("="*70)
    
    setup_logging()
    
    print("\n" + "="*70)
    print("✅ SISTEMA DE LOGS CONFIGURADO COM SUCESSO")
    print("="*70)
