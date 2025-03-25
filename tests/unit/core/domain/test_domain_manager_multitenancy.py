"""
Testes unitários para os recursos de multi-tenancy do DomainManager.

Este módulo contém testes para validar o funcionamento dos métodos de multi-tenancy
do DomainManager, verificando a associação de conversas e clientes a domínios.
"""
import pytest
import json
from unittest.mock import Mock, patch

from src.core.domain.domain_manager import DomainManager


class TestDomainManagerMultitenancy:
    """Testes para os recursos de multi-tenancy do DomainManager."""

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
    def mock_redis_client(self):
        """Fixture que cria um mock do cliente Redis."""
        redis_client = Mock()
        
        # Configurar comportamentos padrão para os métodos do Redis
        redis_client.set.return_value = True
        redis_client.get.return_value = None
        redis_client.expire.return_value = True
        
        return redis_client
    
    @pytest.fixture
    def domain_manager_with_redis(self, mock_domain_loader, mock_redis_client):
        """Fixture que cria uma instância do DomainManager com Redis."""
        with patch("src.core.domain.domain_manager.DomainLoader", return_value=mock_domain_loader), \
             patch("src.core.domain.domain_manager.get_redis_client", return_value=mock_redis_client), \
             patch("src.core.domain.domain_manager.RedisCache") as mock_redis_cache, \
             patch("src.core.domain.domain_manager.get_domain_registry") as mock_registry:
            
            # Configurar o mock do RedisCache
            mock_redis_cache_instance = Mock()
            mock_redis_cache_instance.get_current_timestamp.return_value = 1234567890
            mock_redis_cache.return_value = mock_redis_cache_instance
            
            # Configurar o mock do DomainRegistry
            mock_registry_instance = Mock()
            mock_registry_instance.domain_exists.return_value = True
            mock_registry.return_value = mock_registry_instance
            
            manager = DomainManager(domains_dir="/fake/config/path", redis_client=mock_redis_client)
            manager.redis_cache = mock_redis_cache_instance
            return manager
    
    def test_set_conversation_domain(self, domain_manager_with_redis, mock_redis_client):
        """Testa a associação de uma conversa a um domínio."""
        # Configurar o teste
        conversation_id = "conv123"
        domain_name = "cosmetics"
        client_id = "client456"
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.set_conversation_domain(conversation_id, domain_name, client_id)
        
        # Verificar o resultado
        assert result is True
        
        # Verificar se o Redis foi chamado corretamente
        mock_redis_client.set.assert_called_once()
        call_args = mock_redis_client.set.call_args[0]
        assert call_args[0] == f"conversation:domain:{conversation_id}"
        # Não podemos verificar o JSON exato, mas podemos verificar se é uma string
        assert isinstance(call_args[1], str)
        
        # Verificar se o TTL foi definido
        mock_redis_client.expire.assert_called_once_with(
            f"conversation:domain:{conversation_id}", 60 * 60 * 24 * 30
        )
    
    def test_get_conversation_domain(self, domain_manager_with_redis, mock_redis_client):
        """Testa a obtenção do domínio associado a uma conversa."""
        # Configurar o teste
        conversation_id = "conv123"
        domain_name = "cosmetics"
        client_id = "client456"
        
        # Configurar o mock do Redis para retornar dados
        mock_redis_client.get.return_value = json.dumps({
            "domain": domain_name,
            "timestamp": 1234567890,
            "client_id": client_id
        })
        
        # Chamar o método que estamos testando
        result_domain, result_client = domain_manager_with_redis.get_conversation_domain(conversation_id)
        
        # Verificar o resultado
        assert result_domain == domain_name
        assert result_client == client_id
        
        # Verificar se o Redis foi chamado corretamente
        mock_redis_client.get.assert_called_once_with(f"conversation:domain:{conversation_id}")
    
    def test_get_conversation_domain_not_found(self, domain_manager_with_redis, mock_redis_client):
        """Testa o comportamento quando o domínio da conversa não é encontrado."""
        # Configurar o teste
        conversation_id = "conv123"
        mock_redis_client.get.return_value = None
        
        # Chamar o método que estamos testando
        result_domain, result_client = domain_manager_with_redis.get_conversation_domain(conversation_id)
        
        # Verificar se retorna o domínio padrão quando não encontra
        assert result_domain == domain_manager_with_redis.default_domain
        assert result_client is None
    
    def test_set_client_domain(self, domain_manager_with_redis, mock_redis_client):
        """Testa a associação de um cliente a um domínio."""
        # Configurar o teste
        client_id = "client456"
        domain_name = "cosmetics"
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.set_client_domain(client_id, domain_name)
        
        # Verificar o resultado
        assert result is True
        
        # Verificar se o Redis foi chamado corretamente
        mock_redis_client.set.assert_called_once_with(f"client:domain:{client_id}", domain_name)
        
        # Verificar se o TTL foi definido
        mock_redis_client.expire.assert_called_once_with(
            f"client:domain:{client_id}", 60 * 60 * 24 * 90
        )
    
    def test_get_client_domain(self, domain_manager_with_redis, mock_redis_client):
        """Testa a obtenção do domínio associado a um cliente."""
        # Configurar o teste
        client_id = "client456"
        domain_name = "cosmetics"
        
        # Configurar o mock do Redis para retornar dados
        mock_redis_client.get.return_value = domain_name.encode('utf-8')
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.get_client_domain(client_id)
        
        # Verificar o resultado
        assert result == domain_name
        
        # Verificar se o Redis foi chamado corretamente
        mock_redis_client.get.assert_called_once_with(f"client:domain:{client_id}")
    
    def test_get_client_domain_not_found(self, domain_manager_with_redis, mock_redis_client):
        """Testa o comportamento quando o domínio do cliente não é encontrado."""
        # Configurar o teste
        client_id = "client456"
        mock_redis_client.get.return_value = None
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.get_client_domain(client_id)
        
        # Verificar se retorna o domínio padrão quando não encontra
        assert result == domain_manager_with_redis.default_domain
    
    def test_set_chatwoot_client_id(self, domain_manager_with_redis, mock_redis_client):
        """Testa a associação de uma conta Chatwoot a um cliente."""
        # Configurar o teste
        chatwoot_account_id = "chatwoot789"
        client_id = "client456"
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.set_chatwoot_client_id(chatwoot_account_id, client_id)
        
        # Verificar o resultado
        assert result is True
        
        # Verificar se o Redis foi chamado corretamente
        mock_redis_client.set.assert_called_once_with(f"client:chatwoot:{chatwoot_account_id}", client_id)
        
        # Verificar se o TTL foi definido
        mock_redis_client.expire.assert_called_once_with(
            f"client:chatwoot:{chatwoot_account_id}", 60 * 60 * 24 * 365
        )
    
    def test_get_chatwoot_client_id(self, domain_manager_with_redis, mock_redis_client):
        """Testa a obtenção do cliente associado a uma conta Chatwoot."""
        # Configurar o teste
        chatwoot_account_id = "chatwoot789"
        client_id = "client456"
        
        # Configurar o mock do Redis para retornar dados
        mock_redis_client.get.return_value = client_id.encode('utf-8')
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.get_chatwoot_client_id(chatwoot_account_id)
        
        # Verificar o resultado
        assert result == client_id
        
        # Verificar se o Redis foi chamado corretamente
        mock_redis_client.get.assert_called_once_with(f"client:chatwoot:{chatwoot_account_id}")
    
    def test_get_chatwoot_client_id_not_found(self, domain_manager_with_redis, mock_redis_client):
        """Testa o comportamento quando o cliente da conta Chatwoot não é encontrado."""
        # Configurar o teste
        chatwoot_account_id = "chatwoot789"
        mock_redis_client.get.return_value = None
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.get_chatwoot_client_id(chatwoot_account_id)
        
        # Verificar se retorna None quando não encontra
        assert result is None
    
    def test_get_domain_for_chatwoot_conversation(self, domain_manager_with_redis, mock_redis_client):
        """Testa a determinação do domínio para uma conversa do Chatwoot."""
        # Configurar o teste
        chatwoot_account_id = "chatwoot789"
        conversation_id = "conv123"
        domain_name = "cosmetics"
        client_id = "client456"
        
        # Configurar os mocks para o fluxo completo
        # Primeiro, simular que a conversa já tem um domínio associado
        mock_redis_client.get.side_effect = [
            json.dumps({"domain": domain_name, "client_id": client_id}),  # get_conversation_domain
            None  # Para qualquer chamada adicional
        ]
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.get_domain_for_chatwoot_conversation(
            chatwoot_account_id, conversation_id
        )
        
        # Verificar o resultado
        assert result == domain_name
        
        # Verificar se o Redis foi chamado com o parâmetro correto para a primeira chamada
        mock_redis_client.get.assert_any_call(f"conversation:domain:{conversation_id}")
        
        # Verificar o número total de chamadas
        assert mock_redis_client.get.call_count == 2
    
    def test_get_domain_for_chatwoot_conversation_fallback_to_client(self, domain_manager_with_redis, mock_redis_client):
        """Testa o fallback para o domínio do cliente quando a conversa não tem domínio associado."""
        # Configurar o teste
        chatwoot_account_id = "chatwoot789"
        conversation_id = "conv123"
        domain_name = "cosmetics"
        client_id = "client456"
        
        # Configurar os mocks para o fluxo de fallback
        # Primeiro, simular que a conversa não tem domínio associado
        # Depois, simular que encontrou o cliente associado à conta Chatwoot
        # Por fim, simular que encontrou o domínio associado ao cliente
        mock_redis_client.get.side_effect = [
            None,  # get_conversation_domain
            client_id.encode('utf-8'),  # get_chatwoot_client_id
            domain_name.encode('utf-8')  # get_client_domain
        ]
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.get_domain_for_chatwoot_conversation(
            chatwoot_account_id, conversation_id
        )
        
        # Verificar o resultado
        assert result == domain_name
        
        # Verificar se o Redis foi chamado corretamente
        assert mock_redis_client.get.call_count == 3
        mock_redis_client.get.assert_any_call(f"conversation:domain:{conversation_id}")
        mock_redis_client.get.assert_any_call(f"client:chatwoot:{chatwoot_account_id}")
        mock_redis_client.get.assert_any_call(f"client:domain:{client_id}")
        
        # Verificar se a conversa foi associada ao domínio do cliente
        mock_redis_client.set.assert_called_once()
        mock_redis_client.expire.assert_called_once()
    
    def test_get_domain_for_chatwoot_conversation_fallback_to_default(self, domain_manager_with_redis, mock_redis_client):
        """Testa o fallback para o domínio padrão quando não encontra cliente ou domínio."""
        # Configurar o teste
        chatwoot_account_id = "chatwoot789"
        conversation_id = "conv123"
        
        # Configurar os mocks para o fluxo de fallback para o padrão
        # Simular que não encontrou nem conversa nem cliente
        mock_redis_client.get.return_value = None
        
        # Chamar o método que estamos testando
        result = domain_manager_with_redis.get_domain_for_chatwoot_conversation(
            chatwoot_account_id, conversation_id
        )
        
        # Verificar o resultado
        assert result == domain_manager_with_redis.default_domain
        
        # Verificar se o Redis foi chamado corretamente
        assert mock_redis_client.get.call_count >= 2
        mock_redis_client.get.assert_any_call(f"conversation:domain:{conversation_id}")
        mock_redis_client.get.assert_any_call(f"client:chatwoot:{chatwoot_account_id}")
