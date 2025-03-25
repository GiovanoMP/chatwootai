"""
Testes unitários para o novo DomainManager.

Este módulo contém testes para validar o funcionamento do DomainManager,
verificando a gestão de domínios ativos e acesso às configurações.
"""
import pytest
import os
from unittest.mock import Mock, patch
from pathlib import Path

from src.core.domain.domain_manager import DomainManager
from src.core.domain.domain_loader import ConfigurationError


class TestDomainManager:
    """Testes para o DomainManager."""

    @pytest.fixture
    def mock_domain_loader(self):
        """Fixture que cria um mock do DomainLoader."""
        loader = Mock()
        
        # Configura o mock para retornar configurações de domínio
        sample_domains = {
            "_base": {
                "version": "2.1",
                "name": "_base",
                "description": "Configuração base",
                "settings": {"default_setting": "value"}
            },
            "cosmetics": {
                "version": "2.1",
                "name": "cosmetics",
                "description": "Domínio de cosméticos",
                "settings": {"product_categories": ["skincare", "makeup"]}
            },
            "retail": {
                "version": "2.1",
                "name": "retail",
                "description": "Domínio de varejo",
                "settings": {"product_categories": ["electronics", "home"]}
            }
        }
        
        # Configura o comportamento de load_domain
        loader.load_domain.side_effect = lambda name: sample_domains.get(name)
        
        return loader

    @pytest.fixture
    def domain_manager(self, mock_domain_loader):
        """Fixture que cria uma instância do DomainManager com um mock do DomainLoader."""
        with patch("src.core.domain.domain_manager.DomainLoader", return_value=mock_domain_loader):
            return DomainManager(domains_dir="/fake/config/path")

    def test_initialization(self, domain_manager, mock_domain_loader):
        """Testa se o DomainManager inicializa corretamente."""
        assert domain_manager.domain_loader == mock_domain_loader
        assert domain_manager.active_domain == "default"
        assert domain_manager.domains_cache == {}

    def test_set_active_domain_valid(self, domain_manager, mock_domain_loader):
        """Testa a definição de um domínio ativo válido."""
        # Configura o mock para retornar True ao verificar se o domínio existe
        mock_domain_loader.load_domain.return_value = {"name": "cosmetics"}
        
        # Define o domínio ativo
        domain_manager.set_active_domain("cosmetics")
        
        # Verifica se o domínio ativo foi atualizado
        assert domain_manager.active_domain == "cosmetics"
        
        # Verifica se o mock foi chamado corretamente
        mock_domain_loader.load_domain.assert_called_with("cosmetics")

    def test_set_active_domain_invalid(self, domain_manager, mock_domain_loader):
        """Testa o comportamento ao definir um domínio inválido."""
        # Configura o mock para retornar None, simulando um domínio que não existe
        mock_domain_loader.load_domain.return_value = None
        
        # Tenta definir um domínio inválido
        try:
            domain_manager.set_active_domain("nonexistent")
            pytest.fail("Deveria ter lançado ConfigurationError")
        except ConfigurationError as e:
            assert str(e) == "Domínio 'nonexistent' não encontrado"
        
        # Verifica se o domínio ativo permanece inalterado
        assert domain_manager.active_domain == "default"

    def test_get_active_domain(self, domain_manager):
        """Testa a obtenção do domínio ativo."""
        # Define um domínio ativo para o teste
        domain_manager.active_domain = "cosmetics"
        
        # Obtém o domínio ativo
        active_domain = domain_manager.get_active_domain()
        
        # Verifica se o resultado é o esperado
        assert active_domain == "cosmetics"

    def test_get_domain_config_valid(self, domain_manager, mock_domain_loader):
        """Testa a obtenção da configuração de um domínio válido."""
        # Configuração esperada para o domínio
        expected_config = {
            "version": "2.1",
            "name": "cosmetics",
            "description": "Domínio de cosméticos",
            "settings": {"product_categories": ["skincare", "makeup"]}
        }
        
        # Configura o mock para retornar a configuração esperada
        mock_domain_loader.load_domain.return_value = expected_config
        
        # Obtém a configuração do domínio
        config = domain_manager.get_domain_config("cosmetics")
        
        # Verifica se o resultado é o esperado
        assert config == expected_config
        
        # Verifica se o mock foi chamado corretamente
        mock_domain_loader.load_domain.assert_called_with("cosmetics")
        
        # Verifica se a configuração foi armazenada em cache
        assert domain_manager.domains_cache["cosmetics"] == expected_config

    def test_get_domain_config_cached(self, domain_manager, mock_domain_loader):
        """Testa se a configuração em cache é usada quando disponível."""
        # Configuração esperada para o domínio
        expected_config = {
            "version": "2.1",
            "name": "retail",
            "description": "Domínio de varejo",
            "settings": {"product_categories": ["electronics", "home"]}
        }
        
        # Coloca a configuração no cache
        domain_manager.domains_cache["retail"] = expected_config
        
        # Obtém a configuração do domínio
        config = domain_manager.get_domain_config("retail")
        
        # Verifica se o resultado é o esperado
        assert config == expected_config
        
        # Verifica se o mock NÃO foi chamado (pois a configuração estava em cache)
        mock_domain_loader.load_domain.assert_not_called()

    def test_get_domain_config_invalid(self, domain_manager, mock_domain_loader):
        """Testa o comportamento ao obter a configuração de um domínio inválido."""
        # Configura o mock para retornar None, simulando um domínio que não existe
        mock_domain_loader.load_domain.return_value = None
        
        # Tenta obter a configuração de um domínio inválido
        try:
            domain_manager.get_domain_config("nonexistent")
            pytest.fail("Deveria ter lançado ConfigurationError")
        except ConfigurationError as e:
            assert str(e) == "Domínio 'nonexistent' não encontrado"

    def test_get_active_domain_config(self, domain_manager):
        """Testa a obtenção da configuração do domínio ativo."""
        # Define um domínio ativo para o teste
        domain_manager.active_domain = "cosmetics"
        
        # Configuração esperada para o domínio
        expected_config = {
            "version": "2.1",
            "name": "cosmetics",
            "description": "Domínio de cosméticos",
            "settings": {"product_categories": ["skincare", "makeup"]}
        }
        
        # Coloca a configuração no cache
        domain_manager.domains_cache["cosmetics"] = expected_config
        
        # Obtém a configuração do domínio ativo
        config = domain_manager.get_active_domain_config()
        
        # Verifica se o resultado é o esperado
        assert config == expected_config

    def test_get_setting_from_domain(self, domain_manager):
        """Testa a obtenção de uma configuração específica de um domínio."""
        # Configuração para o domínio
        domain_config = {
            "version": "2.1",
            "name": "cosmetics",
            "description": "Domínio de cosméticos",
            "settings": {
                "product_categories": ["skincare", "makeup"],
                "nested": {
                    "value": "test"
                }
            }
        }
        
        # Coloca a configuração no cache
        domain_manager.domains_cache["cosmetics"] = domain_config
        
        # Obtém uma configuração simples
        categories = domain_manager.get_setting("cosmetics", "settings.product_categories")
        assert categories == ["skincare", "makeup"]
        
        # Obtém uma configuração aninhada
        nested_value = domain_manager.get_setting("cosmetics", "settings.nested.value")
        assert nested_value == "test"
        
        # Obtém uma configuração que não existe
        non_existent = domain_manager.get_setting("cosmetics", "settings.non_existent", default="default_value")
        assert non_existent == "default_value"

    def test_get_setting_from_active_domain(self, domain_manager):
        """Testa a obtenção de uma configuração específica do domínio ativo."""
        # Define um domínio ativo para o teste
        domain_manager.active_domain = "retail"
        
        # Configuração para o domínio
        domain_config = {
            "version": "2.1",
            "name": "retail",
            "description": "Domínio de varejo",
            "settings": {
                "product_categories": ["electronics", "home"]
            }
        }
        
        # Coloca a configuração no cache
        domain_manager.domains_cache["retail"] = domain_config
        
        # Obtém uma configuração do domínio ativo
        categories = domain_manager.get_active_domain_setting("settings.product_categories")
        assert categories == ["electronics", "home"]
