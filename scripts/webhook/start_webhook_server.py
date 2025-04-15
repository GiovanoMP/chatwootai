#!/usr/bin/env python3
"""
Script para iniciar o servidor webhook com todas as dependências corretamente inicializadas.
Este script garante que o DomainManager seja inicializado corretamente antes de ser usado.
"""

import os
import sys
import logging
import redis
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Carrega variáveis de ambiente
load_dotenv()

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/webhook.log')
    ]
)
logger = logging.getLogger('webhook_starter')

# Importa os componentes necessários
from src.webhook.server import main as start_webhook_server
from src.core.domain.domain_manager import DomainManager
# Removido a importação de MemorySystem pois o módulo foi descontinuado

def initialize_domain_manager():
    """
    Inicializa o DomainManager explicitamente antes de iniciar o servidor webhook.
    Isso garante que o DomainManager esteja disponível para o DataProxyAgent.
    """
    logger.info("🔄 Inicializando DomainManager explicitamente...")

    # Diretório de configurações
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
    domains_dir = os.path.join(config_dir, 'domains')

    # Determinação do domínio padrão para fallback
    default_domain = os.getenv('DEFAULT_DOMAIN', 'cosmetics')

    # Inicializa o cliente Redis para o DomainManager
    try:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        redis_client.ping()  # Verifica a conexão
        logger.info(f"✅ Conexão com Redis estabelecida: {redis_host}:{redis_port}")
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível conectar ao Redis: {str(e)}")
        logger.warning("⚠️ Usando DomainManager sem Redis (sem cache)")
        redis_client = None

    # Inicialização do DomainManager com o diretório de domínios
    domain_manager = DomainManager(
        domains_dir=domains_dir,
        default_domain=default_domain,
        redis_client=redis_client
    )

    # IMPORTANTE: Explicitamente inicializar o DomainManager para carregar configurações
    try:
        domain_manager.initialize()
        logger.info("✅ DomainManager inicializado com sucesso")

        # Carrega todos os domínios disponíveis no sistema e seus clientes
        available_domains = domain_manager.loader.list_available_domains()
        logger.info(f"✅ Domínios disponíveis carregados: {available_domains}")

        # Para cada domínio, listar os clientes disponíveis
        for domain in available_domains:
            clients = domain_manager.loader.list_available_clients(domain)
            if clients:
                logger.info(f"✅ Clientes para o domínio {domain}: {clients}")

                # Pré-carrega as configurações de cada cliente
                for client in clients:
                    try:
                        # Carrega a configuração do cliente para o cache
                        client_config = domain_manager.loader.load_client_config(domain, client)
                        if client_config:
                            logger.info(f"✅ Configuração pré-carregada para account {client} do domínio {domain}")
                    except Exception as e:
                        logger.warning(f"⚠️ Não foi possível pré-carregar account {client}: {str(e)}")

        return domain_manager
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar DomainManager: {str(e)}")
        # Garantimos que pelo menos o domínio padrão será carregado
        try:
            domain_manager.set_active_domain(default_domain)
            logger.info(f"✅ Domínio padrão {default_domain} configurado manualmente")
            return domain_manager
        except Exception as e2:
            logger.critical(f"❌ ERRO CRÍTICO: Não foi possível configurar domínio padrão: {str(e2)}")
            return None

def main():
    """
    Função principal para iniciar o servidor webhook com todas as dependências.
    """
    logger.info("🚀 Iniciando sistema ChatwootAI...")

    # Inicializa o DomainManager explicitamente
    domain_manager = initialize_domain_manager()
    if not domain_manager:
        logger.critical("❌ ERRO CRÍTICO: Não foi possível inicializar o DomainManager!")
        sys.exit(1)

    # Define uma variável de ambiente para indicar que o DomainManager foi inicializado
    os.environ['DOMAIN_MANAGER_INITIALIZED'] = 'true'

    # Inicia o servidor webhook
    logger.info("🚀 Iniciando servidor webhook...")
    start_webhook_server()

if __name__ == "__main__":
    main()
