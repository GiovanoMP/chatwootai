#!/usr/bin/env python3
"""
Script para testar a conexão com o Odoo usando o cliente OdooClient
"""

import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path para importar os módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Importar o cliente Odoo
    logger.info("Importando o cliente Odoo...")
    from src.mcp_odoo import OdooClient, get_odoo_client
    logger.info("Cliente Odoo importado com sucesso!")

    # Criar o cliente Odoo
    logger.info("Criando o cliente Odoo...")
    client = get_odoo_client()
    logger.info(f"Cliente Odoo criado com sucesso! UID: {client.uid}")

    # Testar a conexão
    logger.info("Testando a conexão com o Odoo...")

    # Listar modelos disponíveis
    logger.info("Listando modelos disponíveis...")
    models_info = client.get_models()
    logger.info(f"Número de modelos disponíveis: {len(models_info['model_names'])}")
    logger.info(f"Primeiros 5 modelos: {models_info['model_names'][:5]}")

    # Buscar informações sobre o modelo 'res.partner'
    logger.info("Buscando informações sobre o modelo 'res.partner'...")
    model_info = client.get_model_info('res.partner')
    logger.info(f"Informações do modelo 'res.partner': {model_info}")

    # Buscar parceiros
    logger.info("Buscando parceiros...")
    # Primeiro, buscar os IDs dos parceiros
    partner_ids = client.search(
        model_name='res.partner',
        domain=[],
        limit=5
    )
    logger.info(f"IDs de parceiros encontrados: {partner_ids}")

    # Depois, ler os dados desses parceiros
    if partner_ids:
        partners = client.read_records(
            model_name='res.partner',
            ids=partner_ids,
            fields=['name', 'email', 'phone']
        )
        logger.info(f"Número de parceiros encontrados: {len(partners)}")
        for partner in partners:
            logger.info(f"Parceiro: {partner['id']} - {partner.get('name', 'Sem nome')}")
    else:
        logger.info("Nenhum parceiro encontrado.")

    logger.info("Teste concluído com sucesso!")
except ImportError as e:
    logger.error(f"Erro ao importar o cliente Odoo: {e}")
    logger.error("Verifique se todas as dependências estão instaladas.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Erro ao testar a conexão com o Odoo: {e}")
    sys.exit(1)
