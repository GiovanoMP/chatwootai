#!/usr/bin/env python3
"""
Script para testar apenas o SalesAgent com base na configuração YAML.
Este script simplificado foca apenas no componente essencial.

Uso:
    python test_sales_agent_only.py "Você tem protetor solar fator 50?"
"""

import sys
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO,
                 format='%(asctime)s %(name)s [%(levelname)s] %(message)s')

logger = logging.getLogger("TESTE-SALES")

# Importações apenas dos componentes necessários
from src.agents.specialized.sales_agent import SalesAgent
from src.core.data_proxy_agent import DataProxyAgent
from src.core.data_service_hub import DataServiceHub
from src.core.memory import MemorySystem
from src.core.domain.domain_manager import DomainManager
from src.plugins.core.plugin_manager import PluginManager

class MockDataServiceHub:
    """Simulação simplificada do DataServiceHub."""
    
    def get_product_data(self, query, domain=None):
        """Simula busca de produtos."""
        logger.info(f"📊 Consultando produtos para: '{query}' (domínio: {domain})")
        
        # Dados mockados para teste
        if "protetor solar" in query.lower() or "fator" in query.lower():
            return {
                "products": [
                    {
                        "name": "Protetor Solar FPS 50+",
                        "brand": "SunProtect",
                        "price": 89.90,
                        "in_stock": True,
                        "description": "Proteção UVA/UVB, resistente à água"
                    }
                ]
            }
        elif "creme" in query.lower() and "mão" in query.lower():
            return {
                "products": [
                    {
                        "name": "Creme para Mãos Hidratante",
                        "brand": "Nivea",
                        "price": 25.90,
                        "in_stock": True,
                        "description": "Hidratação profunda para mãos ressecadas"
                    }
                ]
            }
        else:
            return {"products": []}

async def setup_components():
    """Configura apenas os componentes essenciais."""
    logger.info("🚀 Inicializando componentes essenciais...")
    
    # 1. Inicializar sistema de memória
    memory_system = MemorySystem()
    logger.info("✅ Sistema de memória inicializado")
    
    # 2. Inicializar gerenciador de domínio
    domain_manager = DomainManager()
    domain_manager.set_active_domain("cosmetics")
    logger.info(f"✅ Gerenciador de domínio inicializado com domínio ativo: {domain_manager.active_domain}")
    
    # 3. Inicializar gerenciador de plugins
    plugin_manager = PluginManager(config={})
    logger.info("✅ Gerenciador de plugins inicializado")
    
    # 4. Inicializar mock do hub de serviços de dados
    data_service_hub = MockDataServiceHub()
    logger.info("✅ Mock do hub de serviços de dados inicializado")
    
    # 5. Inicializar o DataProxyAgent
    data_proxy_agent = DataProxyAgent(data_service_hub=data_service_hub)
    logger.info("✅ DataProxyAgent inicializado")
    
    # 6. Configuração básica do SalesAgent
    agent_config = {
        "role": "Especialista em Vendas",
        "goal": "Ajudar clientes a encontrar os produtos ideais para suas necessidades",
        "backstory": "Você é um especialista em produtos cosméticos com anos de experiência",
        "verbose": True,
        "allow_delegation": False
    }
    
    # 7. Inicializar o SalesAgent
    sales_agent = SalesAgent(
        agent_config=agent_config,
        memory_system=memory_system,
        data_proxy_agent=data_proxy_agent,
        domain_manager=domain_manager,
        plugin_manager=plugin_manager
    )
    logger.info("✅ SalesAgent inicializado")
    
    return sales_agent, data_proxy_agent

async def test_query(sales_agent, query):
    """Testa uma consulta no SalesAgent."""
    logger.info(f"📝 Testando consulta: '{query}'")
    
    # Simular contexto básico
    context = {
        "conversation_id": 12345,
        "customer_id": "cliente-teste",
        "previous_messages": []
    }
    
    # Processar a mensagem
    response = await sales_agent.process_message(query, context)
    
    logger.info(f"✅ Resposta gerada: {response}")
    return response

async def main():
    """Função principal."""
    print("\n" + "="*70)
    print("🤖 TESTE SIMPLIFICADO DO SALES AGENT")
    print("="*70 + "\n")
    
    # Obter consulta dos argumentos ou usar padrão
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Você tem creme para as mãos?"
    
    # Configurar componentes
    sales_agent, data_proxy = await setup_components()
    
    # Testar consulta
    print("\n" + "-"*70)
    print(f"📱 CLIENTE pergunta: '{query}'")
    print("-"*70 + "\n")
    
    response = await test_query(sales_agent, query)
    
    print("\n" + "-"*70)
    print(f"🤖 RESPOSTA: {response}")
    print("-"*70 + "\n")
    
    print("✅ TESTE CONCLUÍDO")
    print("="*70 + "\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
