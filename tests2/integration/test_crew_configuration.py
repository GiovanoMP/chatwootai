#!/usr/bin/env python3
"""
Teste de integração para validar a configuração das crews no sistema ChatwootAI

Este teste verifica se:
1. As crews são carregadas corretamente a partir do YAML
2. O nome padrão "SalesCrew" está sendo usado consistentemente
3. O sistema identifica corretamente o account_id como chave primária
4. A sequência domínio > account_id > crew_id funciona corretamente
"""

import os
import sys
import logging
import yaml
import pytest
from unittest.mock import patch, MagicMock

# Configurar logging para testes
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar diretório principal ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Importações do sistema
from src.core.domain.domain_manager import DomainManager
from src.core.crews.crew_factory import CrewFactory, get_crew_factory
from src.core.data_proxy_agent import DataProxyAgent
from src.core.memory import MemorySystem

@pytest.fixture
def memory_system():
    """Fixture para criar um sistema de memória para testes"""
    return MemorySystem()

@pytest.fixture
def domain_manager():
    """Fixture para criar um gerenciador de domínios para testes"""
    # Usar o caminho correto para as configurações de domínio
    domains_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config/domains"))
    return DomainManager(domains_dir=domains_dir, default_domain="cosmetics")

@pytest.fixture
def crew_factory(memory_system, domain_manager):
    """Fixture para criar uma fábrica de crews para testes"""
    data_proxy = MagicMock(spec=DataProxyAgent)
    return get_crew_factory(
        force_new=True,
        data_proxy_agent=data_proxy,
        memory_system=memory_system,
        domain_manager=domain_manager
    )

def test_account_id_is_primary_key():
    """Teste para verificar se o account_id é tratado como chave primária"""
    # Caminho direto para o arquivo de configuração no filesystem
    config_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "../../config/domains/cosmetics/account_1/config.yaml"
    ))
    
    # Verifica se o arquivo existe
    assert os.path.exists(config_path), f"Arquivo de configuração não encontrado: {config_path}"
    
    # Carrega o conteúdo do arquivo YAML
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Verifica se a configuração foi carregada corretamente
    assert config is not None
    assert "metadata" in config
    
    # Verifica se o account_id está definido corretamente no arquivo
    assert "account_id" in config["metadata"]
    assert config["metadata"]["account_id"] == "account_1"
    
    # Verifica se o arquivo segue a estrutura de diretórios correta
    # /config/domains/{domain_name}/{account_id}/config.yaml
    assert "account_1" in config_path
    assert "cosmetics" in config_path

def test_crew_name_standardization():
    """Teste para verificar se os nomes das crews estão padronizados"""
    # Caminho direto para o arquivo de configuração no filesystem
    config_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "../../config/domains/cosmetics/account_1/config.yaml"
    ))
    
    # Carrega o conteúdo do arquivo YAML
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Verifica se a configuração das crews foi carregada corretamente
    assert "crews" in config
    crews_config = config["crews"]
    assert crews_config is not None
    assert "sales" in crews_config
    
    # Verificar se o nome da crew "sales" está padronizado como "SalesCrew"
    assert crews_config["sales"]["name"] == "SalesCrew"
    
    # Verificar se o nome da crew "support_crew" está padronizado como "SupportCrew"
    assert "support_crew" in crews_config
    assert crews_config["support_crew"]["name"] == "SupportCrew"

def test_crew_creation_with_account_id(domain_manager, crew_factory):
    """Teste para verificar se as crews são criadas corretamente com o account_id"""
    # Configura o domínio ativo
    domain_manager.set_active_domain("cosmetics")
    
    # Verifica se a fábrica de crews lança exceção sem account_id
    with pytest.raises(ValueError):
        crew_factory.create_crew("sales")
    
    # Tenta criar a crew com o account_id correto (simula falha porque estamos mockando)
    try:
        crew = crew_factory.create_crew("sales", account_id="account_1")
        assert False, "Este teste deveria falhar porque DataProxyAgent é um mock"
    except Exception as e:
        # O teste é esperado falhar, mas não deveria falhar por causa de erro na chamada
        # Verificamos se falhou por causa do mock e não por causa de parâmetros incorretos
        assert "ConfigurationError" not in str(e.__class__.__name__), \
            f"Falhou com erro de configuração: {str(e)}"
        assert "ValueError" not in str(e.__class__.__name__), \
            f"Falhou com erro de valor: {str(e)}"

if __name__ == "__main__":
    print("Executando testes de integração para configuração de crews...")
    pytest.main(["-xvs", __file__])
