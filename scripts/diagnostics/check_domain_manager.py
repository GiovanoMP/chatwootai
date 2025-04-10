#!/usr/bin/env python3
"""
Script de diagnóstico para verificar o estado do DomainManager.

Este script verifica se o DomainManager está sendo corretamente inicializado
e se está disponível para o DataProxyAgent.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('domain_manager_check')

# Carrega variáveis de ambiente
load_dotenv()

# Importa os componentes necessários
from src.core.domain.domain_manager import DomainManager
from src.core.data_proxy_agent import DataProxyAgent
from src.core.data_service_hub import DataServiceHub
from src.core.memory import MemorySystem
from src.core.hub import HubCrew

def check_domain_manager():
    """
    Verifica se o DomainManager está sendo corretamente inicializado.
    """
    logger.info("🔍 Verificando inicialização do DomainManager...")
    
    # Diretório de configurações
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
    domains_dir = os.path.join(config_dir, 'domains')
    
    # Determinação do domínio padrão para fallback
    default_domain = os.getenv('DEFAULT_DOMAIN', 'cosmetics')
    
    # Inicialização do DomainManager com o diretório de domínios
    domain_manager = DomainManager(domains_dir=domains_dir, default_domain=default_domain)
    
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
        
        # Teste de acesso a configurações do domínio
        try:
            domain_manager.set_active_domain(default_domain)
            logger.info(f"✅ Domínio ativo definido como: {default_domain}")
            
            # Tenta obter as configurações de ferramentas do domínio ativo
            tools_config = domain_manager.get_tools_config()
            if tools_config:
                logger.info(f"✅ Configurações de ferramentas obtidas para o domínio {default_domain}")
                logger.info(f"✅ Número de ferramentas configuradas: {len(tools_config)}")
            else:
                logger.warning(f"⚠️ Nenhuma configuração de ferramentas encontrada para o domínio {default_domain}")
        except Exception as e:
            logger.error(f"❌ Erro ao acessar configurações do domínio ativo: {str(e)}")
        
        # Teste de integração com DataProxyAgent
        try:
            logger.info("🔍 Verificando integração com DataProxyAgent...")
            
            # Inicializa os componentes necessários
            memory_system = MemorySystem()
            data_service_hub = DataServiceHub()
            
            # Inicializa o DataProxyAgent com o DomainManager
            data_proxy = DataProxyAgent(
                data_service_hub=data_service_hub,
                memory_system=memory_system,
                domain_manager=domain_manager
            )
            
            # Verifica se o DomainManager está disponível no DataProxyAgent
            if hasattr(data_proxy, '_domain_manager') and data_proxy._domain_manager:
                logger.info("✅ DomainManager disponível no DataProxyAgent")
                
                # Tenta inicializar as ferramentas
                try:
                    # Chama o método que verifica o DomainManager
                    data_proxy._initialize_tools()
                    logger.info("✅ Ferramentas inicializadas com sucesso no DataProxyAgent")
                except Exception as e:
                    logger.error(f"❌ Erro ao inicializar ferramentas no DataProxyAgent: {str(e)}")
            else:
                logger.error("❌ DomainManager NÃO está disponível no DataProxyAgent")
            
            # Teste de integração com HubCrew
            logger.info("🔍 Verificando integração com HubCrew...")
            
            # Inicializa o HubCrew com o DomainManager
            hub_crew = HubCrew(
                memory_system=memory_system,
                data_service_hub=data_service_hub,
                domain_manager=domain_manager
            )
            
            # Verifica se o DomainManager está disponível no HubCrew
            if hasattr(hub_crew, '_domain_manager') and hub_crew._domain_manager:
                logger.info("✅ DomainManager disponível no HubCrew")
            else:
                logger.error("❌ DomainManager NÃO está disponível no HubCrew")
                
            # Verifica se o DataProxyAgent do HubCrew tem acesso ao DomainManager
            data_proxy_agent = getattr(hub_crew, '_data_proxy_agent', None)
            if data_proxy_agent and hasattr(data_proxy_agent, '_domain_manager') and data_proxy_agent._domain_manager:
                logger.info("✅ DomainManager disponível no DataProxyAgent do HubCrew")
            else:
                logger.error("❌ DomainManager NÃO está disponível no DataProxyAgent do HubCrew")
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar integração com DataProxyAgent: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar DomainManager: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando verificação do DomainManager...")
    result = check_domain_manager()
    
    if result:
        logger.info("✅ Verificação concluída com sucesso!")
        sys.exit(0)
    else:
        logger.error("❌ Verificação falhou!")
        sys.exit(1)
