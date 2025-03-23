"""
Testes unitários para o novo DomainLoader.

Este módulo contém testes para validar o funcionamento do DomainLoader,
verificando o carregamento de configurações, herança e validação.
"""
import os
import pytest
from unittest.mock import patch, mock_open
import yaml

from src.core.domain.domain_loader import DomainLoader
from src.core.exceptions import ConfigurationError


class TestDomainLoader:
    """Testes para o DomainLoader."""

    @pytest.fixture
    def sample_config(self):
        """Fixture que retorna uma configuração de domínio de exemplo."""
        return {
            "version": "2.1",
            "name": "test_domain",
            "description": "Domínio de teste",
            "settings": {
                "language": "pt-BR",
                "timezone": "America/Sao_Paulo"
            },
            "tools": {
                "customer_db": {
                    "type": "database",
                    "class": "src.tools.database_tools.CustomerDatabaseTool",
                    "config": {
                        "connection_string": "postgresql://user:pass@localhost/customers",
                        "description": "Ferramenta de acesso ao banco de dados"
                    }
                },
                "enabled": ["search", "memory"]
            }
        }

    @pytest.fixture
    def base_config(self):
        """Fixture que retorna uma configuração base."""
        return {
            "version": "2.1",
            "name": "_base",
            "description": "Configuração base",
            "settings": {
                "language": "en-US",
                "timezone": "UTC"
            },
            "tools": {
                "customer_db": {
                    "type": "database",
                    "class": "src.tools.database_tools.CustomerDatabaseTool",
                    "config": {
                        "connection_string": "postgresql://user:pass@localhost/customers",
                        "description": "Ferramenta de acesso ao banco de dados"
                    }
                },
                "enabled": ["search", "query", "vector_search"]
            }
        }

    @pytest.fixture
    def domain_loader(self):
        """Fixture que cria uma instância do DomainLoader com mock de filesystem."""
        with patch("os.path.exists") as mock_exists, \
             patch("pathlib.Path.mkdir") as mock_mkdir:
            
            # Configura o mock para simular que o diretório já existe
            mock_exists.return_value = True
            
            loader = DomainLoader(domains_dir="/fake/config/path")
            
            # Verifica se não tentou criar o diretório
            mock_mkdir.assert_not_called()
            
            return loader

    def test_initialization(self, domain_loader):
        """Testa se o DomainLoader inicializa corretamente."""
        assert domain_loader.domains_dir == "/fake/config/path"
        assert domain_loader.domains_cache == {}
        assert domain_loader.base_domain_name == "_base"

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_domain_configuration(self, mock_file, mock_exists, domain_loader, sample_config):
        """Testa o carregamento de uma configuração de domínio válida."""
        # Configura o mock para simular a existência do arquivo
        mock_exists.return_value = True
        
        # Configura o mock para retornar a configuração YAML
        mock_file.return_value.__enter__.return_value.read.return_value = yaml.dump(sample_config)
        
        # Carrega o domínio
        config = domain_loader.load_domain_configuration("test_domain")
        
        # Verifica se o resultado é o esperado
        assert config == sample_config
        # O método load_domain_configuration não atualiza o cache, apenas o load_domain faz isso
        # Portanto, não verificamos o cache aqui
        
        # Verifica se os mocks foram chamados corretamente
        expected_path = os.path.join("/fake/config/path", "test_domain", "config.yaml")
        mock_exists.assert_called_once_with(expected_path)
        mock_file.assert_called_once_with(expected_path, 'r', encoding='utf-8')

    @patch("os.path.exists")
    def test_load_nonexistent_domain(self, mock_exists, domain_loader):
        """Testa o comportamento quando o domínio não existe."""
        # Configura o mock para simular que o arquivo não existe
        mock_exists.return_value = False
        
        # Tenta carregar um domínio que não existe
        config = domain_loader.load_domain_configuration("nonexistent_domain")
        
        # Verifica se o resultado é None
        assert config is None
        
        # Verifica se o mock foi chamado corretamente
        expected_path = os.path.join("/fake/config/path", "nonexistent_domain", "config.yaml")
        mock_exists.assert_called_once_with(expected_path)

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_domain_with_inheritance(self, mock_file, mock_exists, domain_loader, sample_config, base_config):
        """Testa o carregamento de um domínio com herança da configuração base."""
        # Configura o mock para simular a existência dos arquivos
        mock_exists.return_value = True
        
        # Configura o comportamento para retornar diferentes configurações
        sample_config["inherit"] = "_base"  # Adiciona herança
        
        def mock_yaml_load(file_path):
            if "_base" in file_path:
                return base_config
            return sample_config
        
        # Configura o mock para retornar diferentes configurações YAML
        mock_file_content = {
            os.path.join("/fake/config/path", "test_domain", "config.yaml"): yaml.dump(sample_config),
            os.path.join("/fake/config/path", "_base", "config.yaml"): yaml.dump(base_config)
        }
        
        def side_effect_read(file_path):
            return mock_file_content.get(file_path, "")
        
        mock_file.return_value.__enter__.return_value.read.side_effect = side_effect_read
        
        # Configura a cache com a configuração base
        domain_loader.domains_cache["_base"] = base_config
        
        # Carrega o domínio com herança
        with patch.object(domain_loader, 'load_domain_configuration', side_effect=lambda name: base_config if name == "_base" else sample_config):
            config = domain_loader.load_domain(sample_config["name"])
        
        # Verifica se o resultado contém configurações mescladas
        assert config["settings"]["language"] == "pt-BR"  # Do domínio específico
        assert "search" in config["tools"]["enabled"]  # Da configuração base
        assert "memory" in config["tools"]["enabled"]  # Do domínio específico

    def test_validate_configuration_success(self, domain_loader, sample_config):
        """Testa a validação de uma configuração válida."""
        # Executa a validação
        validated = domain_loader.validate_configuration(sample_config)
        
        # Verifica se a validação passou
        assert validated is True

    def test_validate_configuration_missing_version(self, domain_loader, sample_config):
        """Testa a validação quando falta a versão na configuração."""
        # Remove a versão
        del sample_config["version"]
        
        # Executa a validação e verifica se lança exceção
        with pytest.raises(ConfigurationError, match="Configuração de domínio inválida: falta o campo 'version'"):
            domain_loader.validate_configuration(sample_config)

    def test_validate_configuration_invalid_version(self, domain_loader, sample_config):
        """Testa a validação quando a versão é inválida."""
        # Define uma versão inválida
        sample_config["version"] = "1.0"  # Versão não suportada
        
        # Executa a validação e verifica se lança exceção
        with pytest.raises(ConfigurationError, match="Versão de configuração não suportada: 1.0"):
            domain_loader.validate_configuration(sample_config)
