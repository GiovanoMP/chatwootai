#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste para verificar a integração dos conectores MCP com o MCP-Crew.
Este script testa se o MCP-Crew consegue descobrir ferramentas dos MCPs usando os conectores.
"""

import os
import sys
import logging
import json
import importlib.util
from typing import Dict, List, Any
from dataclasses import asdict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_connector_integration")

# Cores para saída no terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Adicionar os diretórios necessários ao PYTHONPATH
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Definir funções de impressão antes de usá-las nas importações
def print_info(message):
    """Imprime mensagem informativa"""
    print(f"{YELLOW}ℹ️ {message}{RESET}")

def print_success(message):
    """Imprime mensagem de sucesso"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    """Imprime mensagem de erro"""
    print(f"{RED}❌ {message}{RESET}")

# Importar módulos do MCP-Crew
try:
    # Adicionar o diretório mcp_crew_system_v2 ao path
    sys.path.append(os.path.join(project_dir, 'mcp_crew_system_v2'))
    
    # Importar os módulos do MCP-Crew
    from src.core.mcp_tool_discovery import MCPToolDiscovery
    from src.config.config import Config
    from src.core.mcp_connector_factory import MCPConnectorFactory
    from src.core.tool_metadata import ToolMetadata
    print_info("Módulos importados com sucesso do diretório mcp_crew_system_v2")
except ImportError as e:
    logger.error(f"{RED}Erro ao importar módulos do MCP-Crew: {e}{RESET}")
    logger.error(f"{YELLOW}Certifique-se de que o MCP-Crew está instalado e que você está executando este script do diretório raiz do projeto.{RESET}")
    sys.exit(1)

def print_info(message):
    """Imprime mensagem informativa"""
    print(f"{YELLOW}ℹ️ {message}{RESET}")

def print_success(message):
    """Imprime mensagem de sucesso"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    """Imprime mensagem de erro"""
    print(f"{RED}❌ {message}{RESET}")

def print_section(title):
    """Imprime título de seção"""
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}== {title}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

def test_connector_availability():
    """Testa a disponibilidade dos conectores"""
    print_section("VERIFICANDO DISPONIBILIDADE DOS CONECTORES")
    
    # Lista de conectores a verificar
    connectors = [
        ('mongodb', 'mcp_crew_system_v2.src.connectors.mongodb_adapter'),
        ('chatwoot', 'mcp_crew_system_v2.src.connectors.chatwoot_dynamic_adapter'),
        ('redis', 'mcpadapt.core'),
        ('qdrant', 'mcpadapt.core')
    ]
    
    available_connectors = []
    
    for mcp_name, module_name in connectors:
        try:
            # Verificar se o módulo está disponível
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                print_success(f"Conector para {mcp_name} está disponível ({module_name})")
                available_connectors.append(mcp_name)
            else:
                print_error(f"Conector para {mcp_name} não está disponível ({module_name})")
        except Exception as e:
            print_error(f"Erro ao verificar conector para {mcp_name}: {e}")
    
    return available_connectors

def create_test_config():
    """Cria uma configuração de teste para o MCP-Crew"""
    print_section("CRIANDO CONFIGURAÇÃO DE TESTE")
    
    # Usar a configuração padrão do Config
    config = Config()
    
    # Atualizar as URLs dos MCPs para os valores de teste
    # Nota: Não podemos passar diretamente os parâmetros para o construtor
    # então modificamos os atributos da classe diretamente
    
    # Adicionar tenant_id para MongoDB
    if hasattr(config, 'MCP_REGISTRY') and 'mcp-mongodb' in config.MCP_REGISTRY:
        config.MCP_REGISTRY['mcp-mongodb'].tenant_id = 'account_1'
    
    print_info("Configuração de teste criada")
    return config

def test_tool_discovery(config, available_connectors):
    """Testa a descoberta de ferramentas usando os conectores"""
    print_section("TESTANDO DESCOBERTA DE FERRAMENTAS")
    
    try:
        # Criar instância do MCPToolDiscovery
        tool_discovery = MCPToolDiscovery()
        
        # Descobrir ferramentas de todos os MCPs disponíveis
        all_tools = []
        
        for mcp_name in available_connectors:
            print_info(f"Descobrindo ferramentas do {mcp_name}...")
            
            # Obter configuração do MCP
            mcp_key = f"mcp-{mcp_name}"
            if mcp_key in config.MCP_REGISTRY:
                mcp_config = config.MCP_REGISTRY[mcp_key]
                
                # Descobrir ferramentas
                tools = tool_discovery._fetch_tools_from_mcp(mcp_key, mcp_config)
            
                if tools:
                    print_success(f"Descobertas {len(tools)} ferramentas do {mcp_name}")
                    all_tools.extend(tools)
                    
                    # Mostrar detalhes das ferramentas
                    for i, tool in enumerate(tools, 1):
                        tool_dict = asdict(tool)
                        print(f"  {i}. {tool_dict['name']}")
                        print(f"     Descrição: {tool_dict['description']}")
                        print(f"     MCP: {tool_dict['mcp_source']}")
                        
                        # Mostrar parâmetros
                        if tool_dict['parameters']:
                            print(f"     Parâmetros:")
                            for param_name, param_info in tool_dict['parameters'].items():
                                param_type = param_info.get('type', 'any')
                                param_desc = param_info.get('description', 'Sem descrição')
                                print(f"       - {param_name} ({param_type}): {param_desc}")
                        print("")
                else:
                    print_error(f"Nenhuma ferramenta descoberta do {mcp_name}")
            else:
                print_error(f"Configuração para {mcp_key} não encontrada")
        
        return all_tools
    except Exception as e:
        print_error(f"Erro ao testar descoberta de ferramentas: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Função principal"""
    print_section("TESTE DE INTEGRAÇÃO DOS CONECTORES MCP COM MCP-CREW")
    
    # Verificar disponibilidade dos conectores
    available_connectors = test_connector_availability()
    
    if not available_connectors:
        print_error("Nenhum conector disponível. Verifique se os módulos estão instalados.")
        print_info("Você pode instalar os conectores com:")
        print("  pip install -e /caminho/para/mcp-conectors")
        return False
    
    # Criar configuração de teste
    config = create_test_config()
    
    # Testar descoberta de ferramentas
    tools = test_tool_discovery(config, available_connectors)
    
    # Resumo
    print_section("RESUMO DO TESTE")
    if tools:
        print_success(f"Integração bem-sucedida! Descobertas {len(tools)} ferramentas no total.")
        print_info("O MCP-Crew está pronto para usar os conectores para descobrir ferramentas.")
        print_info("Próximos passos:")
        print("  1. Integrar os conectores com os agentes do MCP-Crew")
        print("  2. Testar a execução de ferramentas pelos agentes")
        print("  3. Implementar cache e TTL para as ferramentas descobertas")
        return True
    else:
        print_error("Falha na integração. Nenhuma ferramenta descoberta.")
        print_info("Verifique se os servidores MCP estão em execução e acessíveis.")
        print_info("Certifique-se de que os conectores estão instalados corretamente.")
        return False

if __name__ == "__main__":
    main()
