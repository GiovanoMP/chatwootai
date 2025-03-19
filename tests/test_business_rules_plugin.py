"""
Testes para o BusinessRulesPlugin.

Este arquivo contém testes para verificar as funcionalidades do plugin
de regras de negócio, incluindo:
- Inicialização do plugin
- Consulta de regras
- Obtenção de FAQs
- Interação com o DomainRulesService
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile

# Adicionar diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.plugins.business_rules_plugin import BusinessRulesPlugin
from src.services.data.domain_rules_service import DomainRulesService


class TestBusinessRulesPlugin(unittest.TestCase):
    """Testes para o BusinessRulesPlugin."""

    def setUp(self):
        """Configuração inicial para os testes."""
        # Mock para o DomainRulesService
        self.mock_rules_service = MagicMock(spec=DomainRulesService)
        
        # Configuração para o plugin
        self.config = {
            'enabled': True,
            'max_results': 10
        }
        
        # Criar instância do plugin
        self.plugin = BusinessRulesPlugin(self.config)
        
        # Substituir o serviço de regras pelo mock
        self.plugin._rules_service = self.mock_rules_service

    def test_initialization(self):
        """Testa a inicialização do plugin."""
        # Verificar se o plugin é instanciado corretamente
        self.assertEqual(self.plugin.name, 'BusinessRulesPlugin')
        self.assertTrue(self.plugin.enabled)
        self.assertEqual(self.plugin.get_config_value('max_results'), 10)

    def test_query_rules(self):
        """Testa a consulta de regras de negócio."""
        # Configurar o mock para retornar resultados simulados
        mock_results = [
            {
                'id': 'rule1',
                'type': 'product',
                'title': 'Regra de produtos',
                'content': 'Conteúdo da regra'
            },
            {
                'id': 'rule2',
                'type': 'sales',
                'title': 'Regra de vendas',
                'content': 'Conteúdo da regra de vendas'
            }
        ]
        self.mock_rules_service.query_rules.return_value = mock_results
        
        # Testar a consulta
        results = self.plugin.query_rules("produtos")
        
        # Verificar se o método correto foi chamado
        self.mock_rules_service.query_rules.assert_called_once_with("produtos", None, limit=5)
        
        # Verificar os resultados
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], 'rule1')

    def test_query_rules_with_type(self):
        """Testa a consulta de regras com tipo específico."""
        # Configurar o mock
        mock_results = [
            {
                'id': 'rule1',
                'type': 'product',
                'title': 'Regra de produtos',
                'content': 'Conteúdo da regra'
            }
        ]
        self.mock_rules_service.query_rules.return_value = mock_results
        
        # Testar a consulta com tipo específico
        results = self.plugin.query_rules("produtos", rule_type="product", limit=10)
        
        # Verificar se o método correto foi chamado com os parâmetros certos
        self.mock_rules_service.query_rules.assert_called_once_with("produtos", "product", limit=10)
        
        # Verificar os resultados
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'product')

    def test_get_faqs(self):
        """Testa a obtenção de FAQs."""
        # Configurar o mock
        mock_faqs = [
            {
                'id': 'faq1',
                'type': 'support',
                'title': 'FAQ 1',
                'content': 'Resposta para a FAQ 1'
            },
            {
                'id': 'faq2',
                'type': 'support',
                'title': 'FAQ 2',
                'content': 'Resposta para a FAQ 2'
            }
        ]
        self.mock_rules_service.query_rules.return_value = mock_faqs
        
        # Testar a obtenção de FAQs
        faqs = self.plugin.get_faqs(query="dúvida")
        
        # Verificar se o método correto foi chamado
        self.mock_rules_service.query_rules.assert_called_once_with("dúvida", "support", limit=10)
        
        # Verificar os resultados
        self.assertEqual(len(faqs), 2)
        self.assertEqual(faqs[0]['type'], 'support')

    def test_get_product_rules(self):
        """Testa a obtenção de regras de produtos."""
        # Configurar o mock
        mock_rules = [
            {
                'id': 'rule1',
                'type': 'product',
                'title': 'Regra de produtos',
                'content': 'Conteúdo da regra'
            }
        ]
        self.mock_rules_service.get_product_rules.return_value = mock_rules
        
        # Testar a obtenção de regras de produtos
        rules = self.plugin.get_product_rules()
        
        # Verificar se o método correto foi chamado
        self.mock_rules_service.get_product_rules.assert_called_once_with(None)
        
        # Verificar os resultados
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['type'], 'product')

    def test_error_handling(self):
        """Testa o tratamento de erros."""
        # Configurar o mock para lançar uma exceção
        self.mock_rules_service.query_rules.side_effect = Exception("Erro simulado")
        
        # Testar o tratamento de erros
        results = self.plugin.query_rules("produtos")
        
        # Verificar que o plugin captura a exceção e retorna uma lista vazia
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
