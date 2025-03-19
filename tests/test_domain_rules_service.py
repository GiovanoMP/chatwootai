"""
Testes para o DomainRulesService.

Este arquivo contém testes para verificar as funcionalidades do serviço
de regras de domínio, incluindo:
- Carregamento de domínios a partir de arquivos YAML
- Definição de domínio ativo
- Consulta de regras de negócio
- Busca semântica de regras
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import yaml
import json
import tempfile

# Adicionar diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.data.domain_rules_service import DomainRulesService
from src.services.data.data_service_hub import DataServiceHub


class TestDomainRulesService(unittest.TestCase):
    """Testes para o DomainRulesService."""

    def setUp(self):
        """Configuração inicial para os testes."""
        # Criar um diretório temporário para os arquivos de domínio
        self.temp_dir = tempfile.TemporaryDirectory()
        self.domains_dir = self.temp_dir.name
        
        # Criar arquivos YAML de teste
        self.create_test_domain_files()
        
        # Mock para o DataServiceHub
        self.mock_hub = MagicMock(spec=DataServiceHub)
        
        # Configuração para o serviço
        self.config = {
            'domains_dir': self.domains_dir,
            'default_domain': 'cosmeticos'
        }
        
        # Criar instância do serviço
        self.domain_rules_service = DomainRulesService(self.mock_hub, self.config)

    def tearDown(self):
        """Limpeza após os testes."""
        self.temp_dir.cleanup()

    def create_test_domain_files(self):
        """Cria arquivos YAML de domínio para teste."""
        # Dados de teste para o domínio "cosmeticos"
        cosmeticos_data = {
            'name': 'Cosméticos',
            'description': 'Domínio para produtos cosméticos',
            'plugins': ['business_rules', 'product_search'],
            'business_rules': [
                {
                    'id': 'rule1',
                    'type': 'product',
                    'title': 'Regra de produtos de maquiagem',
                    'content': 'Produtos de maquiagem têm 10% de desconto para compras acima de R$100.'
                },
                {
                    'id': 'rule2',
                    'type': 'sales',
                    'title': 'Promoção de verão',
                    'content': 'Durante o verão, hidratantes têm 15% de desconto.'
                },
                {
                    'id': 'rule3',
                    'type': 'support',
                    'title': 'FAQ: Como aplicar base?',
                    'content': 'Para aplicar base corretamente, use uma esponja ou pincel e espalhe uniformemente.'
                }
            ]
        }
        
        # Dados de teste para o domínio "saude"
        saude_data = {
            'name': 'Saúde',
            'description': 'Domínio para produtos de saúde',
            'plugins': ['business_rules'],
            'business_rules': [
                {
                    'id': 'rule4',
                    'type': 'product',
                    'title': 'Regra de suplementos',
                    'content': 'Suplementos vitamínicos têm 5% de desconto na primeira compra.'
                },
                {
                    'id': 'rule5',
                    'type': 'support',
                    'title': 'FAQ: Como tomar vitamina C?',
                    'content': 'Vitamina C deve ser tomada junto com as refeições para melhor absorção.'
                }
            ]
        }
        
        # Escrever os arquivos YAML
        with open(os.path.join(self.domains_dir, 'cosmeticos.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(cosmeticos_data, f, allow_unicode=True)
            
        with open(os.path.join(self.domains_dir, 'saude.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(saude_data, f, allow_unicode=True)

    def test_initialize_domains(self):
        """Testa se os domínios são carregados corretamente."""
        # Verificar se todos os domínios foram carregados
        self.assertIn('cosmeticos', self.domain_rules_service.domain_config)
        self.assertIn('saude', self.domain_rules_service.domain_config)
        
        # Verificar se o domínio ativo é o configurado como padrão
        self.assertEqual('cosmeticos', self.domain_rules_service.get_active_domain())
        
        # Verificar se as regras foram carregadas corretamente
        cosmeticos_config = self.domain_rules_service.get_domain_config('cosmeticos')
        self.assertEqual('Cosméticos', cosmeticos_config.get('name'))
        self.assertEqual(3, len(cosmeticos_config.get('business_rules', [])))

    def test_set_active_domain(self):
        """Testa a mudança de domínio ativo."""
        # Mudar para o domínio de saúde
        result = self.domain_rules_service.set_active_domain('saude')
        self.assertTrue(result)
        self.assertEqual('saude', self.domain_rules_service.get_active_domain())
        
        # Tentar mudar para um domínio inexistente
        result = self.domain_rules_service.set_active_domain('inexistente')
        self.assertFalse(result)
        self.assertEqual('saude', self.domain_rules_service.get_active_domain())  # Mantém o anterior

    def test_get_business_rules(self):
        """Testa a obtenção de regras de negócio."""
        # Obter todas as regras do domínio cosméticos
        rules = self.domain_rules_service.get_business_rules(domain_id='cosmeticos')
        self.assertEqual(3, len(rules))
        
        # Obter apenas regras do tipo "product"
        product_rules = self.domain_rules_service.get_business_rules('product', 'cosmeticos')
        self.assertEqual(1, len(product_rules))
        self.assertEqual('rule1', product_rules[0]['id'])
        
        # Obter regras do domínio ativo (definido como "cosmeticos" no setUp)
        active_rules = self.domain_rules_service.get_business_rules()
        self.assertEqual(3, len(active_rules))
        
        # Mudar domínio ativo e verificar
        self.domain_rules_service.set_active_domain('saude')
        active_rules = self.domain_rules_service.get_business_rules()
        self.assertEqual(2, len(active_rules))

    def test_query_rules(self):
        """Testa a busca semântica de regras."""
        # Buscar por "maquiagem"
        results = self.domain_rules_service.query_rules("maquiagem", domain_id='cosmeticos')
        self.assertEqual(1, len(results))
        self.assertEqual('rule1', results[0]['id'])
        
        # Buscar por "desconto" (deve encontrar duas regras)
        results = self.domain_rules_service.query_rules("desconto", domain_id='cosmeticos')
        self.assertEqual(2, len(results))
        
        # Buscar por "como" no domínio saúde
        results = self.domain_rules_service.query_rules("como", domain_id='saude')
        self.assertEqual(1, len(results))
        self.assertEqual('rule5', results[0]['id'])
        
        # Busca com limite
        results = self.domain_rules_service.query_rules("desconto", domain_id='cosmeticos', limit=1)
        self.assertEqual(1, len(results))

    def test_get_specialized_rules(self):
        """Testa as funções especializadas para tipos específicos de regras."""
        # Testar FAQs de suporte
        faqs = self.domain_rules_service.get_support_faqs('cosmeticos')
        self.assertEqual(1, len(faqs))
        self.assertEqual('rule3', faqs[0]['id'])
        
        # Testar regras de produtos
        product_rules = self.domain_rules_service.get_product_rules('cosmeticos')
        self.assertEqual(1, len(product_rules))
        self.assertEqual('rule1', product_rules[0]['id'])
        
        # Testar regras de vendas
        sales_rules = self.domain_rules_service.get_sales_rules('cosmeticos')
        self.assertEqual(1, len(sales_rules))
        self.assertEqual('rule2', sales_rules[0]['id'])


if __name__ == '__main__':
    unittest.main()
