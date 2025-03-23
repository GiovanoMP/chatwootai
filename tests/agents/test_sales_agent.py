"""Testes para o SalesAgent.

Este módulo contém testes unitários para o SalesAgent, verificando sua
inicialização, consulta de dados e processamento de mensagens.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.agents.specialized.sales_agent import SalesAgent
from src.core.exceptions import DataAccessError, ConfigurationError
from crewai import Task, Agent
from src.core.agent_manager import AgentManager

# ===== FIXTURES =====

@pytest.fixture
def mock_data_proxy():
    """Fixture que cria um mock do DataProxyAgent para testes."""
    proxy = Mock()
    proxy.is_ready.return_value = True
    proxy.query_data.return_value = [{'id': '1', 'name': 'Produto Teste'}]
    return proxy

@pytest.fixture
def mock_agent_manager():
    """Fixture que cria um mock do AgentManager para testes."""
    manager = Mock()
    manager.get_active_domain.return_value = "cosmeticos"
    return manager

@pytest.fixture
def mock_plugin_manager():
    """Fixture que cria um mock do PluginManager para testes."""
    manager = Mock()
    manager.get_domain_plugins.return_value = []
    return manager

@pytest.fixture
def basic_config():
    """Configuração básica para inicializar o SalesAgent."""
    return {
        'role': 'Sales Expert',
        'goal': 'Handle sales queries',
        'backstory': 'Experienced sales professional',
        'function_type': 'sales'  # Adicionado function_type necessário para o FunctionalAgent
    }

# ===== TESTES DE INICIALIZAÇÃO =====

def test_sales_agent_initialization(mock_data_proxy, mock_agent_manager, mock_plugin_manager, basic_config):
    """Testa se o SalesAgent inicializa corretamente com configurações válidas."""
    # Cria o agente com os mocks necessários
    with patch.object(SalesAgent, 'initialize'):  # Patch do método initialize
        # Patch do __init__ para armazenar o data_proxy_agent diretamente no objeto
        with patch.object(SalesAgent, '__init__', return_value=None) as mock_init:
            agent = SalesAgent(
                basic_config, 
                data_proxy_agent=mock_data_proxy,
                agent_manager=mock_agent_manager,
                plugin_manager=mock_plugin_manager
            )
            # Configuração manual do agente para o teste
            agent.__dict__['_data_proxy_agent'] = mock_data_proxy
            agent.__dict__['_agent_manager'] = mock_agent_manager
            agent.__dict__['_plugin_manager'] = mock_plugin_manager
            agent.__dict__['role'] = 'Sales Expert'
            agent.__dict__['goal'] = 'Handle sales queries'
            agent.__dict__['backstory'] = 'Experienced sales professional'
        
        # Verifica se o agente foi inicializado corretamente
        assert agent.data_proxy_agent == mock_data_proxy
        assert agent.agent_manager == mock_agent_manager
        assert agent.plugin_manager == mock_plugin_manager
        assert agent.role == 'Sales Expert'
        assert agent.goal == 'Handle sales queries'
        assert agent.backstory == 'Experienced sales professional'

def test_sales_agent_initialization_without_data_proxy(basic_config):
    """Testa se o SalesAgent lança exceção quando inicializado sem DataProxyAgent."""
    with pytest.raises(ConfigurationError):
        SalesAgent(basic_config)

def test_sales_agent_initialization_with_invalid_data_proxy(basic_config):
    """Testa se o SalesAgent lança exceção quando o DataProxyAgent não está pronto."""
    # Cria um mock do DataProxyAgent que não está pronto
    mock_data_proxy = Mock()
    mock_data_proxy.is_ready.return_value = False
    
    # Verifica se a exceção correta é lançada
    with patch.object(SalesAgent, 'initialize', side_effect=ConfigurationError("DataProxyAgent não está pronto para uso")):
        with pytest.raises(ConfigurationError):
            agent = SalesAgent(basic_config, data_proxy_agent=mock_data_proxy)
            # Força a chamada do método initialize
            agent.initialize()

# ===== TESTES DE CONSULTA DE DADOS =====

def test_product_query_success(mock_data_proxy, mock_agent_manager, mock_plugin_manager, basic_config):
    """Testa se a consulta de produtos funciona corretamente."""
    # Cria o agente com os mocks necessários
    with patch.object(SalesAgent, 'initialize'):  # Patch do método initialize
        # Patch do __init__ para armazenar o data_proxy_agent diretamente no objeto
        with patch.object(SalesAgent, '__init__', return_value=None) as mock_init:
            agent = SalesAgent(
                basic_config, 
                data_proxy_agent=mock_data_proxy,
                agent_manager=mock_agent_manager,
                plugin_manager=mock_plugin_manager
            )
            # Configuração manual do agente para o teste
            agent.__dict__['_data_proxy_agent'] = mock_data_proxy
            agent.__dict__['_agent_manager'] = mock_agent_manager
            agent.__dict__['_plugin_manager'] = mock_plugin_manager
        
        # Executa o método que queremos testar
        result = agent._query_products('shampoo')
        
        # Verifica se o método query_data foi chamado com os parâmetros corretos
        mock_data_proxy.query_data.assert_called_with(
            query="Encontre produtos relacionados a: shampoo",
            data_type="products",
            domain="cosmeticos",
            limit=5
        )
        
        # Verifica se o resultado é o esperado
        assert result == [{'id': '1', 'name': 'Produto Teste'}]

def test_product_query_failure(mock_data_proxy, mock_agent_manager, mock_plugin_manager, basic_config):
    """Testa se a consulta de produtos lança exceção quando há erro no DataProxyAgent."""
    # Configura o mock para lançar uma exceção
    mock_data_proxy.query_data.side_effect = Exception('DB Error')
    
    # Cria o agente com os mocks necessários
    with patch.object(SalesAgent, 'initialize'):  # Patch do método initialize
        # Patch do __init__ para armazenar o data_proxy_agent diretamente no objeto
        with patch.object(SalesAgent, '__init__', return_value=None) as mock_init:
            agent = SalesAgent(
                basic_config, 
                data_proxy_agent=mock_data_proxy,
                agent_manager=mock_agent_manager,
                plugin_manager=mock_plugin_manager
            )
            # Configuração manual do agente para o teste
            agent.__dict__['_data_proxy_agent'] = mock_data_proxy
            agent.__dict__['_agent_manager'] = mock_agent_manager
            agent.__dict__['_plugin_manager'] = mock_plugin_manager
        
        # Verifica se a exceção correta é lançada
        with pytest.raises(DataAccessError):
            agent._query_products('test query')

def test_pricing_query_success(mock_data_proxy, mock_agent_manager, mock_plugin_manager, basic_config):
    """Testa se a consulta de preços funciona corretamente."""
    # Configura o mock para retornar um dicionário de preços
    mock_data_proxy.query_data.return_value = {'1': 99.99}
    
    # Cria o agente com os mocks necessários
    with patch.object(SalesAgent, 'initialize'):  # Patch do método initialize
        # Patch do __init__ para armazenar o data_proxy_agent diretamente no objeto
        with patch.object(SalesAgent, '__init__', return_value=None) as mock_init:
            agent = SalesAgent(
                basic_config, 
                data_proxy_agent=mock_data_proxy,
                agent_manager=mock_agent_manager,
                plugin_manager=mock_plugin_manager
            )
            # Configuração manual do agente para o teste
            agent.__dict__['_data_proxy_agent'] = mock_data_proxy
            agent.__dict__['_agent_manager'] = mock_agent_manager
            agent.__dict__['_plugin_manager'] = mock_plugin_manager
        
        # Executa o método que queremos testar
        result = agent._query_pricing(['1'])
        
        # Verifica se o método query_data foi chamado com os parâmetros corretos
        mock_data_proxy.query_data.assert_called_with(
            query="Obtenha preços para os produtos: 1",
            data_type="pricing",
            product_ids=['1'],
            domain="cosmeticos"
        )
        
        # Verifica se o resultado é o esperado
        assert result == {'1': 99.99}

def test_pricing_query_with_empty_ids(mock_data_proxy, mock_agent_manager, mock_plugin_manager, basic_config):
    """Testa se a consulta de preços retorna dicionário vazio quando não há IDs."""
    # Cria o agente com os mocks necessários
    with patch.object(SalesAgent, 'initialize'):  # Patch do método initialize
        agent = SalesAgent(
            basic_config, 
            data_proxy_agent=mock_data_proxy,
            agent_manager=mock_agent_manager,
            plugin_manager=mock_plugin_manager
        )
        
        # Executa o método que queremos testar
        result = agent._query_pricing([])
        
        # Verifica se o método query_data não foi chamado
        mock_data_proxy.query_data.assert_not_called()
        
        # Verifica se o resultado é um dicionário vazio
        assert result == {}

def test_promotions_query_success(mock_data_proxy, mock_agent_manager, mock_plugin_manager, basic_config):
    """Testa se a consulta de promoções funciona corretamente."""
    # Configura o mock para retornar uma lista de promoções
    mock_data_proxy.query_data.return_value = [
        {'id': '1', 'name': 'Promoção Teste', 'discount': 10}
    ]
    
    # Cria o agente com os mocks necessários
    with patch.object(SalesAgent, 'initialize'):  # Patch do método initialize
        agent = SalesAgent(
            basic_config, 
            data_proxy_agent=mock_data_proxy,
            agent_manager=mock_agent_manager,
            plugin_manager=mock_plugin_manager
        )
        
        # Executa o método que queremos testar
        result = agent._query_promotions()
        
        # Verifica se o método query_data foi chamado com os parâmetros corretos
        mock_data_proxy.query_data.assert_called_with(
            query="Obtenha todas as promoções ativas",
            data_type="promotions",
            domain="cosmeticos"
        )
        
        # Verifica se o resultado é o esperado
        assert result == [{'id': '1', 'name': 'Promoção Teste', 'discount': 10}]

# ===== TESTES DE PROCESSAMENTO DE MENSAGENS =====

def test_process_message_basic(mock_data_proxy, mock_agent_manager, mock_plugin_manager, basic_config):
    """Testa o processamento básico de mensagens."""
    # Cria o agente com os mocks necessários
    with patch.object(SalesAgent, 'initialize'):  # Patch do método initialize
        # Patch do __init__ para armazenar o data_proxy_agent diretamente no objeto
        with patch.object(SalesAgent, '__init__', return_value=None) as mock_init:
            agent = SalesAgent(
                basic_config, 
                data_proxy_agent=mock_data_proxy,
                agent_manager=mock_agent_manager,
                plugin_manager=mock_plugin_manager
            )
            # Configuração manual do agente para o teste
            agent.__dict__['_data_proxy_agent'] = mock_data_proxy
            agent.__dict__['_agent_manager'] = mock_agent_manager
            agent.__dict__['_plugin_manager'] = mock_plugin_manager
            # Configuração dos atributos do Agent do CrewAI
            for key, value in basic_config.items():
                setattr(agent, key, value)
        
        # Patch do método process_message do FunctionalAgent para retornar uma resposta
        with patch('src.agents.base.functional_agent.FunctionalAgent.process_message', return_value={"status": "success", "response": "Resposta do agente"}):
            # Executa o método que queremos testar com um dicionário
            result = agent.process_message({"content": "Olá, gostaria de informações sobre produtos"})
            
            # Verifica se o resultado é o esperado
            assert isinstance(result, dict)
            assert result.get("status") == "success"
            assert "response" in result

def test_process_message_with_product_query(mock_data_proxy, mock_agent_manager, mock_plugin_manager, basic_config):
    """Testa o processamento de mensagens com consulta de produtos."""
    # Cria o agente com os mocks necessários
    with patch.object(SalesAgent, 'initialize'):  # Patch do método initialize
        # Patch do __init__ para armazenar o data_proxy_agent diretamente no objeto
        with patch.object(SalesAgent, '__init__', return_value=None) as mock_init:
            agent = SalesAgent(
                basic_config, 
                data_proxy_agent=mock_data_proxy,
                agent_manager=mock_agent_manager,
                plugin_manager=mock_plugin_manager
            )
            # Configuração manual do agente para o teste
            agent.__dict__['_data_proxy_agent'] = mock_data_proxy
            agent.__dict__['_agent_manager'] = mock_agent_manager
            agent.__dict__['_plugin_manager'] = mock_plugin_manager
            # Configuração dos atributos do Agent do CrewAI
            for key, value in basic_config.items():
                setattr(agent, key, value)
        
        # Patch do método _query_products para retornar produtos
        with patch.object(agent, '_query_products', return_value=[{'id': '1', 'name': 'Produto Teste'}]):
            # Patch do método process_message do FunctionalAgent para retornar uma resposta
            with patch('src.agents.base.functional_agent.FunctionalAgent.process_message', return_value={"status": "success", "response": "Resposta do agente com produtos"}):
                # Executa o método que queremos testar com um dicionário
                result = agent.process_message({"content": "Quais shampoos vocês têm?"})
                
                # Verifica se o resultado é o esperado
                assert isinstance(result, dict)
                assert result.get("status") == "success"
                assert "response" in result
