"""
Testes unitários para o ToolRegistry.

Este módulo contém testes para validar o funcionamento do ToolRegistry,
verificando registro, instanciação e gerenciamento de ferramentas.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel

from src.core.tools.tool_registry import ToolRegistry
from src.core.exceptions import ConfigurationError


# Classe simples para simular uma ferramenta CrewAI
class MockInputSchema(BaseModel):
    param1: str
    param2: int = 10

class MockTool(BaseTool):
    name: str = "mock_tool"
    description: str = "Uma ferramenta de teste"
    args_schema: type[BaseModel] = MockInputSchema
    
    def _run(self, param1: str, param2: int = 10) -> str:
        return f"Mock result with {param1} and {param2}"


class TestToolRegistry:
    """Testes para o ToolRegistry."""

    @pytest.fixture
    def tool_registry(self):
        """Fixture que cria uma instância do ToolRegistry."""
        registry = ToolRegistry()
        # Limpa o registro para evitar interferência entre testes
        registry.reset()
        return registry

    def test_initialization(self, tool_registry):
        """Testa se o ToolRegistry inicializa corretamente."""
        assert tool_registry.tools == {}
        assert tool_registry.tool_instances == {}

    def test_register_tool_valid(self, tool_registry):
        """Testa o registro de uma ferramenta válida."""
        # Configuração da ferramenta
        tool_config = {
            "type": "mock_tool",
            "class": "tests.unit.core.tools.test_tool_registry.MockTool",
            "config": {
                "name": "custom_mock_tool",
                "description": "Uma ferramenta personalizada"
            }
        }
        
        # Registra a ferramenta
        tool_registry.register_tool("test_tool", tool_config)
        
        # Verifica se a ferramenta foi registrada corretamente
        assert "test_tool" in tool_registry.tools
        assert tool_registry.tools["test_tool"] == tool_config

    def test_register_tool_invalid_config(self, tool_registry):
        """Testa o registro de uma ferramenta com configuração inválida."""
        # Configuração inválida (falta o campo 'type')
        invalid_config = {
            "class": "tests.unit.core.tools.test_tool_registry.MockTool",
            "config": {
                "name": "invalid_tool"
            }
        }
        
        # Tenta registrar a ferramenta e verifica se lança exceção
        with pytest.raises(ConfigurationError, match="Configuração de ferramenta inválida: falta o campo 'type'"):
            tool_registry.register_tool("invalid_tool", invalid_config)

    def test_get_tool_config_valid(self, tool_registry):
        """Testa a obtenção da configuração de uma ferramenta válida."""
        # Configuração da ferramenta
        tool_config = {
            "type": "mock_tool",
            "class": "tests.unit.core.tools.test_tool_registry.MockTool",
            "config": {
                "name": "custom_mock_tool",
                "description": "Uma ferramenta personalizada"
            }
        }
        
        # Registra a ferramenta
        tool_registry.tools["test_tool"] = tool_config
        
        # Obtém a configuração da ferramenta
        config = tool_registry.get_tool_config("test_tool")
        
        # Verifica se a configuração é a esperada
        assert config == tool_config

    def test_get_tool_config_invalid(self, tool_registry):
        """Testa a obtenção da configuração de uma ferramenta que não existe."""
        # Tenta obter a configuração de uma ferramenta que não existe
        with pytest.raises(ConfigurationError, match="Ferramenta 'nonexistent_tool' não encontrada no registro"):
            tool_registry.get_tool_config("nonexistent_tool")

    @patch("importlib.import_module")
    def test_get_tool_class(self, mock_import_module, tool_registry):
        """Testa a obtenção da classe de uma ferramenta."""
        # Configura o mock para retornar um módulo com a classe da ferramenta
        mock_module = Mock()
        mock_module.MockTool = MockTool
        mock_import_module.return_value = mock_module
        
        # Obtém a classe da ferramenta
        tool_class = tool_registry.get_tool_class("tests.unit.core.tools.test_tool_registry.MockTool")
        
        # Verifica se a classe é a esperada
        assert tool_class == MockTool
        
        # Verifica se o mock foi chamado corretamente
        mock_import_module.assert_called_once_with("tests.unit.core.tools.test_tool_registry")

    @patch("importlib.import_module")
    def test_get_tool_class_invalid(self, mock_import_module, tool_registry):
        """Testa a obtenção de uma classe de ferramenta que não existe."""
        # Configura o mock para lançar uma exceção ao tentar importar o módulo
        mock_import_module.side_effect = ImportError("Módulo não encontrado")
        
        # Tenta obter a classe da ferramenta e verifica se lança exceção
        with pytest.raises(ConfigurationError, match="Não foi possível carregar a classe da ferramenta"):
            tool_registry.get_tool_class("nonexistent.module.ToolClass")

    def test_get_tool_instance_from_cache(self, tool_registry):
        """Testa a obtenção de uma instância de ferramenta do cache."""
        # Cria uma instância da ferramenta
        tool_instance = MockTool()
        
        # Coloca a instância no cache
        tool_registry.tool_instances["test_tool"] = tool_instance
        
        # Obtém a instância do cache
        instance = tool_registry.get_tool_instance("test_tool")
        
        # Verifica se a instância é a mesma
        assert instance is tool_instance

    @patch.object(ToolRegistry, "get_tool_config")
    @patch.object(ToolRegistry, "get_tool_class")
    def test_get_tool_instance_new(self, mock_get_tool_class, mock_get_tool_config, tool_registry):
        """Testa a criação de uma nova instância de ferramenta."""
        # Configuração da ferramenta
        tool_config = {
            "type": "mock_tool",
            "class": "tests.unit.core.tools.test_tool_registry.MockTool",
            "config": {
                "name": "custom_mock_tool",
                "description": "Uma ferramenta personalizada"
            }
        }
        
        # Configura os mocks
        mock_get_tool_config.return_value = tool_config
        mock_get_tool_class.return_value = MockTool
        
        # Obtém a instância da ferramenta
        instance = tool_registry.get_tool_instance("test_tool")
        
        # Verifica se a instância é do tipo correto
        assert isinstance(instance, MockTool)
        
        # Verifica se a instância foi configurada corretamente
        assert instance.name == "custom_mock_tool"
        assert instance.description == "Uma ferramenta personalizada"
        
        # Verifica se a instância foi armazenada no cache
        assert "test_tool" in tool_registry.tool_instances
        assert tool_registry.tool_instances["test_tool"] is instance

    def test_reset(self, tool_registry):
        """Testa o reset do registro de ferramentas."""
        # Registra algumas ferramentas
        tool_registry.tools = {"tool1": {}, "tool2": {}}
        tool_registry.tool_instances = {"tool1": Mock(), "tool2": Mock()}
        
        # Reseta o registro
        tool_registry.reset()
        
        # Verifica se o registro foi limpo
        assert tool_registry.tools == {}
        assert tool_registry.tool_instances == {}

    def test_get_tools_by_type(self, tool_registry):
        """Testa a obtenção de ferramentas por tipo."""
        # Registra algumas ferramentas
        tool_registry.tools = {
            "tool1": {"type": "search", "class": "module.SearchTool"},
            "tool2": {"type": "query", "class": "module.QueryTool"},
            "tool3": {"type": "search", "class": "module.AdvancedSearchTool"}
        }
        
        # Obtém as ferramentas do tipo "search"
        search_tools = tool_registry.get_tools_by_type("search")
        
        # Verifica se as ferramentas corretas foram retornadas
        assert len(search_tools) == 2
        assert "tool1" in search_tools
        assert "tool3" in search_tools

    def test_get_all_tool_instances(self, tool_registry):
        """Testa a obtenção de todas as instâncias de ferramentas."""
        # Cria algumas instâncias de ferramenta
        tool1 = MockTool(name="tool1")
        tool2 = MockTool(name="tool2")
        
        # Configura as ferramentas e instâncias
        tool_registry.tools = {
            "tool1": {"type": "mock", "class": "tests.unit.core.tools.test_tool_registry.MockTool"},
            "tool2": {"type": "mock", "class": "tests.unit.core.tools.test_tool_registry.MockTool"},
        }
        tool_registry.tool_instances = {
            "tool1": tool1,
            "tool2": tool2
        }
        
        # Obtém todas as instâncias
        instances = tool_registry.get_all_tool_instances()
        
        # Verifica se todas as instâncias foram retornadas
        assert len(instances) == 2
        assert tool1 in instances
        assert tool2 in instances

    @patch.object(ToolRegistry, "get_tool_instance")
    def test_get_tool_instances_by_type(self, mock_get_tool_instance, tool_registry):
        """Testa a obtenção de instâncias de ferramentas por tipo."""
        # Configura as ferramentas
        tool_registry.tools = {
            "tool1": {"type": "search", "class": "module.SearchTool"},
            "tool2": {"type": "query", "class": "module.QueryTool"},
            "tool3": {"type": "search", "class": "module.AdvancedSearchTool"}
        }
        
        # Configura o mock para retornar instâncias
        mock_get_tool_instance.side_effect = lambda tool_id: MockTool(name=f"instance_{tool_id}")
        
        # Obtém as instâncias do tipo "search"
        search_instances = tool_registry.get_tool_instances_by_type("search")
        
        # Verifica se as instâncias corretas foram retornadas
        assert len(search_instances) == 2
        # Verifica os nomes das instâncias
        assert all(instance.name.startswith("instance_tool") for instance in search_instances)
        # Verifica se o mock foi chamado com os IDs corretos
        assert mock_get_tool_instance.call_count == 2
        mock_get_tool_instance.assert_any_call("tool1")
        mock_get_tool_instance.assert_any_call("tool3")
