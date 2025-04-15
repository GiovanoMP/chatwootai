"""
Testes unitários para o gerenciador de domínios.

Estes testes verificam se o gerenciador de domínios está funcionando corretamente,
incluindo o carregamento de domínios, a troca entre domínios e o acesso às configurações.
"""

import pytest
import os
import yaml
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Importar o módulo a ser testado
from src.core.domain.domain_manager import DomainManager
from src.core.domain.domain_loader import ConfigurationError

class TestDomainManager:
    """Testes para o gerenciador de domínios."""

    @pytest.fixture
    def test_domains_dir(self):
        """Cria um diretório temporário com domínios de teste."""
        # Criar diretório temporário
        temp_dir = tempfile.mkdtemp()
        
        # Criar estrutura de diretórios para domínios
        os.makedirs(os.path.join(temp_dir, "cosmetics"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "retail"), exist_ok=True)
        
        # Criar arquivos de configuração para os domínios
        cosmetics_config = {
            "name": "Cosmetics",
            "description": "Domínio de cosméticos",
            "agents": {
                "customer_service": {
                    "name": "Customer Service Agent",
                    "description": "Agente de atendimento ao cliente"
                }
            },
            "tools": {
                "product_search": {
                    "name": "Product Search",
                    "description": "Ferramenta de busca de produtos"
                }
            },
            "integrations": {
                "mcp": {
                    "type": "odoo-mcp",
                    "config": {
                        "url": "http://localhost:8069",
                        "db": "odoo",
                        "username": "admin"
                    }
                }
            }
        }
        
        retail_config = {
            "name": "Retail",
            "description": "Domínio de varejo",
            "agents": {
                "sales": {
                    "name": "Sales Agent",
                    "description": "Agente de vendas"
                }
            },
            "tools": {
                "inventory_check": {
                    "name": "Inventory Check",
                    "description": "Ferramenta de verificação de estoque"
                }
            },
            "integrations": {
                "mcp": {
                    "type": "odoo-mcp",
                    "config": {
                        "url": "http://localhost:8069",
                        "db": "retail",
                        "username": "admin"
                    }
                }
            }
        }
        
        # Criar arquivo de configuração para account_id específico
        account_config = {
            "account_id": "account_1",
            "name": "Account 1",
            "description": "Configuração específica para account_1",
            "integrations": {
                "mcp": {
                    "type": "odoo-mcp",
                    "config": {
                        "url": "http://localhost:8069",
                        "db": "account_1",
                        "username": "account_1"
                    }
                }
            }
        }
        
        # Escrever configurações nos arquivos
        with open(os.path.join(temp_dir, "cosmetics", "config.yaml"), "w") as f:
            yaml.dump(cosmetics_config, f)
        
        with open(os.path.join(temp_dir, "retail", "config.yaml"), "w") as f:
            yaml.dump(retail_config, f)
        
        with open(os.path.join(temp_dir, "cosmetics", "account_1.yaml"), "w") as f:
            yaml.dump(account_config, f)
        
        # Retornar o diretório temporário
        yield temp_dir
        
        # Limpar o diretório temporário
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def domain_manager(self, test_domains_dir, mock_redis_client):
        """Cria uma instância do gerenciador de domínios para testes."""
        # Criar um patch para o domain_registry
        with patch('src.core.domain.domain_manager.get_domain_registry') as mock_registry:
            # Configurar o mock do registry
            mock_registry_instance = MagicMock()
            mock_registry.return_value = mock_registry_instance
            
            # Configurar o comportamento do registry
            mock_registry_instance.get_domain_config.side_effect = lambda domain_name: {
                "cosmetics": {
                    "name": "Cosmetics",
                    "description": "Domínio de cosméticos",
                    "agents": {
                        "customer_service": {
                            "name": "Customer Service Agent",
                            "description": "Agente de atendimento ao cliente"
                        }
                    }
                },
                "retail": {
                    "name": "Retail",
                    "description": "Domínio de varejo",
                    "agents": {
                        "sales": {
                            "name": "Sales Agent",
                            "description": "Agente de vendas"
                        }
                    }
                }
            }.get(domain_name)
            
            mock_registry_instance.list_domains.return_value = ["cosmetics", "retail"]
            
            mock_registry_instance.get_account_domain_mapping.return_value = {
                "1": {"domain": "cosmetics", "account_id": "account_1"},
                "2": {"domain": "retail", "account_id": "account_2"}
            }
            
            # Criar o gerenciador de domínios
            manager = DomainManager(
                domains_dir=test_domains_dir,
                default_domain="cosmetics",
                redis_client=mock_redis_client
            )
            
            yield manager

    def test_init(self, domain_manager):
        """Testa se o gerenciador de domínios é inicializado corretamente."""
        assert domain_manager.default_domain == "cosmetics"
        assert domain_manager.active_domain_name == "cosmetics"
        assert domain_manager.redis_client is not None
        assert domain_manager.redis_cache is not None

    def test_initialize(self, domain_manager):
        """Testa se o método initialize carrega o domínio padrão corretamente."""
        # Inicializar o gerenciador
        domain_manager.initialize()
        
        # Verificar se o domínio padrão foi carregado
        assert domain_manager.active_domain_name == "cosmetics"
        assert domain_manager.active_domain_config is not None
        assert domain_manager.active_domain_config["name"] == "Cosmetics"

    def test_get_domain_by_account_id(self, domain_manager):
        """Testa se o método get_domain_by_account_id retorna o domínio correto."""
        # Obter o domínio para um account_id existente
        domain = domain_manager.get_domain_by_account_id("1")
        
        # Verificar se o domínio correto foi retornado
        assert domain == "cosmetics"
        
        # Obter o domínio para um account_id inexistente
        domain = domain_manager.get_domain_by_account_id("999")
        
        # Verificar se None foi retornado
        assert domain is None

    def test_get_internal_account_id(self, domain_manager):
        """Testa se o método get_internal_account_id retorna o account_id interno correto."""
        # Obter o account_id interno para um account_id do Chatwoot existente
        account_id = domain_manager.get_internal_account_id("1")
        
        # Verificar se o account_id interno correto foi retornado
        assert account_id == "account_1"
        
        # Obter o account_id interno para um account_id do Chatwoot inexistente
        account_id = domain_manager.get_internal_account_id("999")
        
        # Verificar se None foi retornado
        assert account_id is None

    def test_switch_domain(self, domain_manager):
        """Testa se o método switch_domain altera o domínio ativo corretamente."""
        # Inicializar o gerenciador
        domain_manager.initialize()
        
        # Verificar o domínio ativo inicial
        assert domain_manager.active_domain_name == "cosmetics"
        
        # Alterar para o domínio "retail"
        result = domain_manager.switch_domain("retail")
        
        # Verificar se a alteração foi bem-sucedida
        assert result is True
        assert domain_manager.active_domain_name == "retail"
        assert domain_manager.active_domain_config["name"] == "Retail"
        
        # Tentar alterar para um domínio inexistente
        result = domain_manager.switch_domain("nonexistent")
        
        # Verificar se a alteração falhou
        assert result is False
        assert domain_manager.active_domain_name == "retail"

    def test_get_agents_config(self, domain_manager):
        """Testa se o método get_agents_config retorna as configurações de agentes corretamente."""
        # Inicializar o gerenciador
        domain_manager.initialize()
        
        # Obter as configurações de agentes do domínio ativo
        agents_config = domain_manager.get_agents_config()
        
        # Verificar se as configurações corretas foram retornadas
        assert "customer_service" in agents_config
        assert agents_config["customer_service"]["name"] == "Customer Service Agent"
        
        # Alterar para o domínio "retail"
        domain_manager.switch_domain("retail")
        
        # Obter as configurações de agentes do novo domínio ativo
        agents_config = domain_manager.get_agents_config()
        
        # Verificar se as configurações corretas foram retornadas
        assert "sales" in agents_config
        assert agents_config["sales"]["name"] == "Sales Agent"

    def test_get_agent_config(self, domain_manager):
        """Testa se o método get_agent_config retorna a configuração de um agente específico corretamente."""
        # Inicializar o gerenciador
        domain_manager.initialize()
        
        # Obter a configuração de um agente específico
        agent_config = domain_manager.get_agent_config("customer_service")
        
        # Verificar se a configuração correta foi retornada
        assert agent_config["name"] == "Customer Service Agent"
        assert agent_config["description"] == "Agente de atendimento ao cliente"
        
        # Obter a configuração de um agente inexistente
        agent_config = domain_manager.get_agent_config("nonexistent")
        
        # Verificar se um dicionário vazio foi retornado
        assert agent_config == {}
