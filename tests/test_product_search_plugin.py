"""
Testes para o ProductSearchPlugin.

Este arquivo contém testes para verificar as funcionalidades do plugin
de busca semântica de produtos, incluindo:
- Inicialização do plugin
- Busca de produtos
- Busca de produtos por categoria
- Tratamento de erros
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
from functools import wraps

# Adicionar diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.plugins.product_search_plugin import ProductSearchPlugin
from src.services.product_search_service import ProductSearchService

# Classe de teste para facilitar os testes sem requerer domain_config
class TestableProductSearchPlugin(ProductSearchPlugin):
    def initialize(self, domain_config=None):
        """Versão simplificada do método initialize para testes."""
        if domain_config:
            self.domain_config = domain_config
        else:
            self.domain_config = {
                'name': 'Teste',
                'description': 'Domínio de teste'
            }


class TestProductSearchPlugin(unittest.TestCase):
    """Testes para o ProductSearchPlugin."""

    def setUp(self):
        """Configuração inicial para os testes."""
        # Mock para o ProductSearchService
        self.mock_search_service = MagicMock()
        
        # Configuração para o plugin
        self.plugin_config = {
            'connection_string': 'mock_connection',
            'collection_name': 'products',
            'vector_size': 384
        }
        
        # Configuração de domínio para teste
        self.domain_config = {
            'name': 'Cosméticos',
            'description': 'Domínio para produtos cosméticos'
        }
        
        # Usar a classe de teste que não requer domain_config no initialize
        self.plugin = TestableProductSearchPlugin(config=self.plugin_config)
        
        # Substituir o serviço de busca pelo mock
        self.plugin._search_service = self.mock_search_service
        
        # Inicializar o plugin manualmente com a configuração de domínio
        self.plugin.initialize(self.domain_config)

    def test_initialization(self):
        """Testa a inicialização do plugin."""
        # Verificar se o plugin foi inicializado corretamente
        self.assertEqual(self.plugin.__class__.__name__, 'TestableProductSearchPlugin')
        
        # Verificar se o serviço de busca foi configurado
        self.assertIsNotNone(self.plugin._search_service)
        self.assertIsNotNone(self.plugin.description)

    def test_search_products(self):
        """Testa a busca de produtos."""
        # Configurar o mock para retornar resultados simulados
        mock_results = [
            {
                'id': 1,
                'name': 'Hidratante Facial',
                'description': 'Hidratante para pele oleosa',
                'price': 39.90,
                'score': 0.92
            },
            {
                'id': 2,
                'name': 'Sabonete Facial',
                'description': 'Sabonete para pele oleosa',
                'price': 25.50,
                'score': 0.85
            }
        ]
        self.mock_search_service.search_products.return_value = mock_results
        
        # Testar a busca
        results = self.plugin.search_products("pele oleosa")
        
        # Verificar se o método correto foi chamado
        self.mock_search_service.search_products.assert_called_once_with(
            "pele oleosa", 5, 0.7, None
        )
        
        # Verificar os resultados
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], 'Hidratante Facial')

    def test_search_products_by_category(self):
        """Testa a busca de produtos por categoria."""
        # Configurar o mock
        mock_results = [
            {
                'id': 1,
                'name': 'Hidratante Facial',
                'description': 'Hidratante para pele oleosa',
                'price': 39.90,
                'category_id': 10,
                'score': 0.92
            }
        ]
        self.mock_search_service.search_products.return_value = mock_results
        
        # Testar a busca por categoria
        results = self.plugin.search_products_by_category("hidratante", 10, limit=10)
        
        # Verificar se o método correto foi chamado com os parâmetros certos
        self.mock_search_service.search_products.assert_called_once_with(
            "hidratante", 10, min_score=0.7, category_id=10
        )
        
        # Verificar os resultados
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['category_id'], 10)

    def test_get_product_details(self):
        """Testa a obtenção de detalhes de um produto."""
        # Configurar o mock
        mock_product = {
            'id': 1,
            'name': 'Hidratante Facial',
            'description': 'Hidratante para pele oleosa',
            'price': 39.90,
            'stock': 15,
            'category_id': 10,
            'attributes': {
                'volume': '50ml',
                'tipo_pele': 'oleosa'
            }
        }
        self.mock_search_service.get_product_details.return_value = mock_product
        
        # Testar a obtenção de detalhes
        product = self.plugin.get_product_details(1)
        
        # Verificar se o método correto foi chamado
        self.mock_search_service.get_product_details.assert_called_once_with(1)
        
        # Verificar os resultados
        self.assertEqual(product['id'], 1)
        self.assertEqual(product['name'], 'Hidratante Facial')
        self.assertEqual(product['attributes']['volume'], '50ml')

    def test_get_recommended_products(self):
        """Testa a obtenção de produtos recomendados."""
        # Configurar o mock
        mock_recommendations = [
            {
                'id': 2,
                'name': 'Sabonete Facial',
                'price': 25.50,
                'score': 0.85
            },
            {
                'id': 3,
                'name': 'Tônico Facial',
                'price': 35.90,
                'score': 0.82
            }
        ]
        self.mock_search_service.get_recommended_products.return_value = mock_recommendations
        
        # Testar a obtenção de recomendações
        recommendations = self.plugin.get_recommended_products(1, limit=2)
        
        # Verificar se o método correto foi chamado
        self.mock_search_service.get_recommended_products.assert_called_once_with(1, 2)
        
        # Verificar os resultados
        self.assertEqual(len(recommendations), 2)
        self.assertEqual(recommendations[0]['name'], 'Sabonete Facial')

    def test_error_handling(self):
        """Testa o tratamento de erros."""
        # Configurar o mock para lançar uma exceção
        self.mock_search_service.search_products.side_effect = Exception("Erro simulado")
        
        # Testar o tratamento de erros
        results = self.plugin.search_products("pele oleosa")
        
        # Verificar que o plugin captura a exceção e retorna uma lista vazia
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
