"""
Testes unitários para o DataProxyAgent refatorado.

Este módulo contém testes para validar o funcionamento do DataProxyAgent,
verificando o acesso centralizado a dados através do ToolRegistry.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.core.data_proxy_agent import DataProxyAgent
from src.core.tools.tool_registry import ToolRegistry
from src.core.domain.domain_manager import DomainManager
from src.core.exceptions import DataAccessError, ConfigurationError


class TestDataProxyAgent:
    """Testes para o DataProxyAgent refatorado."""

    @pytest.fixture
    def mock_tool_registry(self):
        """Fixture que cria um mock do ToolRegistry."""
        registry = Mock(spec=ToolRegistry)
        
        # Mock para simular ferramentas
        mock_product_search = Mock()
        mock_product_search.name = "product_search"
        mock_product_search._run.return_value = [{"id": "1", "name": "Produto Teste"}]
        
        mock_customer_search = Mock()
        mock_customer_search.name = "customer_search"
        mock_customer_search._run.return_value = [{"id": "1", "name": "Cliente Teste"}]
        
        mock_vector_search = Mock()
        mock_vector_search.name = "vector_search"
        mock_vector_search._run.return_value = [{"id": "1", "text": "Documento relevante", "score": 0.95}]
        
        # Configura o mock para retornar as ferramentas
        registry.get_tool_instance.side_effect = lambda tool_id: {
            "product_search": mock_product_search,
            "customer_search": mock_customer_search,
            "vector_search": mock_vector_search
        }.get(tool_id)
        
        registry.get_tools_by_type.return_value = ["product_search", "customer_search"]
        registry.get_tool_instances_by_type.return_value = [mock_product_search, mock_customer_search]
        
        return registry

    @pytest.fixture
    def mock_domain_manager(self):
        """Fixture que cria um mock do DomainManager."""
        manager = Mock(spec=DomainManager)
        
        # Configura o mock para retornar um domínio e configurações
        manager.get_active_domain.return_value = "cosmetics"
        manager.get_active_domain_config.return_value = {
            "name": "cosmetics",
            "tools": {
                "enabled": ["product_search", "customer_search", "vector_search"]
            }
        }
        
        return manager

    @pytest.fixture
    def data_proxy_agent(self, mock_tool_registry, mock_domain_manager):
        """Fixture que cria uma instância do DataProxyAgent com mocks."""
        return DataProxyAgent(
            tool_registry=mock_tool_registry,
            domain_manager=mock_domain_manager
        )

    def test_initialization(self, data_proxy_agent, mock_tool_registry, mock_domain_manager):
        """Testa se o DataProxyAgent inicializa corretamente."""
        assert data_proxy_agent.tool_registry == mock_tool_registry
        assert data_proxy_agent.domain_manager == mock_domain_manager
        assert data_proxy_agent.stats == {"queries": 0, "successful_queries": 0, "failed_queries": 0}

    def test_is_ready(self, data_proxy_agent, mock_tool_registry, mock_domain_manager):
        """Testa o método is_ready do DataProxyAgent."""
        # Verifica se o agente está pronto
        assert data_proxy_agent.is_ready() is True
        
        # Verifica o comportamento quando o domain_manager não está disponível
        data_proxy_agent.domain_manager = None
        assert data_proxy_agent.is_ready() is False
        
        # Restaura o domain_manager e verifica o comportamento quando o tool_registry não está disponível
        data_proxy_agent.domain_manager = mock_domain_manager
        data_proxy_agent.tool_registry = None
        assert data_proxy_agent.is_ready() is False

    def test_get_tools_for_agent(self, data_proxy_agent, mock_tool_registry):
        """Testa a obtenção de ferramentas para um agente."""
        # Mock de ferramentas
        mock_tools = [Mock(), Mock()]
        mock_tool_registry.get_tool_instances_by_type.return_value = mock_tools
        
        # Obtém as ferramentas
        tools = data_proxy_agent.get_tools_for_agent("search")
        
        # Verifica se as ferramentas corretas foram retornadas
        assert tools == mock_tools
        
        # Verifica se o mock foi chamado corretamente
        mock_tool_registry.get_tool_instances_by_type.assert_called_once_with("search")

    def test_get_tools_for_domain(self, data_proxy_agent, mock_domain_manager, mock_tool_registry):
        """Testa a obtenção de ferramentas para um domínio."""
        # Mock de ferramentas
        mock_product_tool = Mock()
        mock_customer_tool = Mock()
        
        # Configura o mock do tool_registry
        mock_tool_registry.get_tool_instance.side_effect = lambda tool_id: {
            "product_search": mock_product_tool,
            "customer_search": mock_customer_tool
        }.get(tool_id)
        
        # Obtém as ferramentas para o domínio
        tools = data_proxy_agent.get_tools_for_domain("cosmetics")
        
        # Verifica se as ferramentas corretas foram retornadas
        assert len(tools) == 3  # Assumindo 3 ferramentas habilitadas no domínio
        
        # Verifica se o mock foi chamado corretamente
        mock_domain_manager.get_domain_config.assert_called_once_with("cosmetics")

    def test_query_product_data(self, data_proxy_agent, mock_tool_registry):
        """Testa a consulta de dados de produtos."""
        # Consulta os dados
        result = data_proxy_agent.query_product_data("produto teste", domain="cosmetics")
        
        # Verifica se o resultado é o esperado
        assert result == [{"id": "1", "name": "Produto Teste"}]
        
        # Verifica se as estatísticas foram atualizadas
        assert data_proxy_agent.stats["queries"] == 1
        assert data_proxy_agent.stats["successful_queries"] == 1
        
        # Verifica se o mock foi chamado corretamente
        product_search_tool = mock_tool_registry.get_tool_instance("product_search")
        product_search_tool._run.assert_called_once()
        # Verifica se os parâmetros incluem o texto da consulta e o domínio
        args, kwargs = product_search_tool._run.call_args
        assert "produto teste" in args or "produto teste" in kwargs.values()
        assert "cosmetics" in str(args) or "cosmetics" in str(kwargs.values())

    def test_query_customer_data(self, data_proxy_agent, mock_tool_registry):
        """Testa a consulta de dados de clientes."""
        # Consulta os dados
        result = data_proxy_agent.query_customer_data("cliente teste", domain="cosmetics")
        
        # Verifica se o resultado é o esperado
        assert result == [{"id": "1", "name": "Cliente Teste"}]
        
        # Verifica se as estatísticas foram atualizadas
        assert data_proxy_agent.stats["queries"] == 1
        assert data_proxy_agent.stats["successful_queries"] == 1
        
        # Verifica se o mock foi chamado corretamente
        customer_search_tool = mock_tool_registry.get_tool_instance("customer_search")
        customer_search_tool._run.assert_called_once()

    def test_query_vector_search(self, data_proxy_agent, mock_tool_registry):
        """Testa a consulta de busca vetorial."""
        # Consulta os dados
        result = data_proxy_agent.query_vector_search("consulta teste", collection="products", domain="cosmetics")
        
        # Verifica se o resultado é o esperado
        assert result == [{"id": "1", "text": "Documento relevante", "score": 0.95}]
        
        # Verifica se as estatísticas foram atualizadas
        assert data_proxy_agent.stats["queries"] == 1
        assert data_proxy_agent.stats["successful_queries"] == 1
        
        # Verifica se o mock foi chamado corretamente
        vector_search_tool = mock_tool_registry.get_tool_instance("vector_search")
        vector_search_tool._run.assert_called_once()
        # Verifica se os parâmetros incluem o texto da consulta, a coleção e o domínio
        args, kwargs = vector_search_tool._run.call_args
        assert "consulta teste" in str(args) or "consulta teste" in str(kwargs.values())
        assert "products" in str(args) or "products" in str(kwargs.values())
        assert "cosmetics" in str(args) or "cosmetics" in str(kwargs.values())

    def test_query_data_error(self, data_proxy_agent, mock_tool_registry):
        """Testa o comportamento quando ocorre um erro na consulta."""
        # Configura o mock para lançar uma exceção
        product_search_tool = mock_tool_registry.get_tool_instance("product_search")
        product_search_tool._run.side_effect = Exception("Erro de teste")
        
        # Tenta consultar os dados e verifica se lança exceção
        with pytest.raises(DataAccessError, match="Erro ao consultar dados de produto: Erro de teste"):
            data_proxy_agent.query_product_data("produto teste")
        
        # Verifica se as estatísticas foram atualizadas
        assert data_proxy_agent.stats["queries"] == 1
        assert data_proxy_agent.stats["failed_queries"] == 1
        assert data_proxy_agent.stats["successful_queries"] == 0

    def test_get_stats(self, data_proxy_agent):
        """Testa a obtenção de estatísticas."""
        # Simula algumas consultas
        data_proxy_agent.stats = {
            "queries": 10,
            "successful_queries": 8,
            "failed_queries": 2
        }
        
        # Obtém as estatísticas
        stats = data_proxy_agent.get_stats()
        
        # Verifica se as estatísticas são as esperadas
        assert stats == {
            "queries": 10,
            "successful_queries": 8,
            "failed_queries": 2,
            "success_rate": 80.0
        }

    def test_reset_stats(self, data_proxy_agent):
        """Testa o reset de estatísticas."""
        # Simula algumas consultas
        data_proxy_agent.stats = {
            "queries": 10,
            "successful_queries": 8,
            "failed_queries": 2
        }
        
        # Reseta as estatísticas
        data_proxy_agent.reset_stats()
        
        # Verifica se as estatísticas foram resetadas
        assert data_proxy_agent.stats == {
            "queries": 0,
            "successful_queries": 0,
            "failed_queries": 0
        }
