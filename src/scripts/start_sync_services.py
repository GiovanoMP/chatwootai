#!/usr/bin/env python
"""
Script para iniciar os serviços de sincronização entre PostgreSQL e Qdrant.

Este script inicializa e executa os serviços de sincronização que mantêm
os dados consistentes entre o PostgreSQL e o Qdrant, garantindo que os
embeddings estejam sempre atualizados.

Uso:
    python start_sync_services.py [--no-listener] [--no-periodic] [--sync-interval=3600]

Argumentos:
    --no-listener: Não inicia o serviço de escuta de alterações no banco de dados
    --no-periodic: Não inicia o serviço de sincronização periódica
    --sync-interval: Intervalo em segundos para sincronização periódica (padrão: 3600)
"""
import os
import sys
import logging
import asyncio
import argparse
import signal
from typing import Optional, List, Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync_services.log')
    ]
)

# Adicionar diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar serviços
from src.services.data_sync_service import DataSyncService
from src.services.database_change_listener import DatabaseChangeListener
from src.services.periodic_sync_service import PeriodicSyncService
from src.services.embedding_service import EmbeddingService

# Variáveis para controle dos serviços
listener_service = None
periodic_service = None
running = True

async def start_services(args):
    """
    Inicia os serviços de sincronização.
    
    Args:
        args: Argumentos da linha de comando.
    """
    global listener_service, periodic_service
    
    logger = logging.getLogger(__name__)
    logger.info("Iniciando serviços de sincronização...")
    
    try:
        # Verificar variáveis de ambiente necessárias
        required_env_vars = ["DATABASE_URL", "QDRANT_URL", "OPENAI_API_KEY"]
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Variáveis de ambiente necessárias não encontradas: {', '.join(missing_vars)}")
            logger.error("Por favor, defina as variáveis de ambiente necessárias e tente novamente.")
            return
            
        # Inicializar serviços
        logger.info("Inicializando serviços...")
        
        # Criar serviço de embeddings
        embedding_service = EmbeddingService()
        
        # Criar serviço de sincronização de dados
        data_sync_service = DataSyncService(embedding_service=embedding_service)
        
        # Iniciar tarefas assíncronas para os serviços
        tasks = []
        
        # Iniciar listener de alterações no banco de dados
        if not args.no_listener:
            logger.info("Iniciando serviço de escuta de alterações no banco de dados...")
            listener_service = DatabaseChangeListener(data_sync_service)
            tasks.append(asyncio.create_task(listener_service.start()))
        else:
            logger.info("Serviço de escuta de alterações no banco de dados desativado")
            
        # Iniciar serviço de sincronização periódica
        if not args.no_periodic:
            logger.info(f"Iniciando serviço de sincronização periódica (intervalo: {args.sync_interval} segundos)...")
            periodic_service = PeriodicSyncService(data_sync_service, sync_interval=args.sync_interval)
            tasks.append(asyncio.create_task(periodic_service.start()))
        else:
            logger.info("Serviço de sincronização periódica desativado")
            
        # Aguardar até que o sinal de parada seja recebido
        if tasks:
            logger.info("Todos os serviços iniciados com sucesso!")
            await asyncio.gather(*tasks)
        else:
            logger.warning("Nenhum serviço foi iniciado. Verifique os argumentos.")
            
    except Exception as e:
        logger.error(f"Erro ao iniciar serviços: {e}")
        
def handle_stop_signal(signum, frame):
    """
    Manipulador de sinais para parar os serviços graciosamente.
    """
    global running, listener_service, periodic_service
    
    logger = logging.getLogger(__name__)
    logger.info("Sinal de parada recebido. Parando serviços...")
    
    running = False
    
    # Parar serviços
    if listener_service:
        listener_service.stop()
        
    if periodic_service:
        periodic_service.stop()
        
def parse_arguments():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        Argumentos analisados.
    """
    parser = argparse.ArgumentParser(description="Inicia os serviços de sincronização entre PostgreSQL e Qdrant")
    
    parser.add_argument("--no-listener", action="store_true", help="Não inicia o serviço de escuta de alterações no banco de dados")
    parser.add_argument("--no-periodic", action="store_true", help="Não inicia o serviço de sincronização periódica")
    parser.add_argument("--sync-interval", type=int, default=3600, help="Intervalo em segundos para sincronização periódica (padrão: 3600)")
    
    return parser.parse_args()
    
async def main():
    """
    Função principal.
    """
    # Analisar argumentos
    args = parse_arguments()
    
    # Registrar manipuladores de sinais
    signal.signal(signal.SIGINT, handle_stop_signal)
    signal.signal(signal.SIGTERM, handle_stop_signal)
    
    # Iniciar serviços
    await start_services(args)
    
if __name__ == "__main__":
    asyncio.run(main())
