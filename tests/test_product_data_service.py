"""
Testes de integração para o ProductDataService.

Este módulo contém testes que verificam a comunicação entre o 
ProductDataService e as respectivas bases de dados (PostgreSQL e Qdrant).
"""

import unittest
import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Adicionar o diretório raiz ao sys.path para facilitar importações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar logging para depuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.services.data.data_service_hub import DataServiceHub
# Importações condicionais para evitar erros
try:
    from src.services.data.product_data_service import ProductDataService
except ImportError as e:
    logger.warning(f"Não foi possível importar ProductDataService: {str(e)}")
    ProductDataService = None
from src.tools.vector_tools import QdrantVectorSearchTool

class TestProductDataService(unittest.TestCase):
    """
    Testes para o ProductDataService, verificando a integração com PostgreSQL e Qdrant.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Configuração inicial executada uma vez para a classe de teste.
        Inicializa conexões com bancos de dados.
        """
        logger.info("Iniciando testes do ProductDataService")
        
        # Configuração para conexões via Docker
        config = {
            "postgres": {
                "host": "localhost",
                "port": 5433,  # Porta mapeada no Docker
                "user": "postgres",
                "password": "postgres",
                "database": "chatwootai"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None  # Adicionada senha nula para evitar o erro
            },
            "qdrant": {
                "host": "localhost",
                "port": 6335,  # Porta mapeada no Docker
                "collection_name": "products"
            }
        }
        
        # Inicializar o hub de serviços
        cls.hub = DataServiceHub(config)
        
        # Inicializar vetorial (opcional, depende dos testes)
        try:
            qdrant_url = f"http://{config['qdrant']['host']}:{config['qdrant']['port']}"
            cls.vector_tool = QdrantVectorSearchTool(
                qdrant_url=qdrant_url,
                collection_name=config["qdrant"]["collection_name"]
            )
            logger.info(f"QdrantVectorSearchTool inicializado com sucesso: {qdrant_url}")
        except Exception as e:
            logger.warning(f"Não foi possível inicializar QdrantVectorSearchTool: {str(e)}")
            cls.vector_tool = None
        
        # Inicializar o serviço de produtos
        try:
            cls.product_service = cls.hub.services.get('ProductDataService')
            if not cls.product_service:
                logger.warning("ProductDataService não encontrado no hub, criando instância manualmente")
                # Importar diretamente para evitar problemas de resolução de módulos
                from src.services.data.product_data_service import ProductDataService
                cls.product_service = ProductDataService(cls.hub, cls.vector_tool)
                logger.info("ProductDataService inicializado manualmente")
        except Exception as e:
            logger.error(f"Não foi possível inicializar ProductDataService: {str(e)}")
            raise
    
    @classmethod
    def tearDownClass(cls):
        """
        Limpeza após todos os testes.
        Fecha conexões com bancos de dados.
        """
        if cls.hub:
            cls.hub.close()
        logger.info("Testes do ProductDataService finalizados")
    
    def test_connection_to_postgres(self):
        """
        Testa a conexão com o PostgreSQL.
        """
        logger.info("Testando conexão com PostgreSQL")
        
        # Tentar uma consulta simples
        query = "SELECT 1 as test"
        result = self.hub.execute_query(query)
        
        self.assertIsNotNone(result, "Falha na conexão com PostgreSQL")
        self.assertEqual(result[0]["test"], 1, "Consulta de teste falhou")
        
        logger.info("Conexão com PostgreSQL bem-sucedida")
    
    def test_search_products(self):
        """
        Testa a busca de produtos no PostgreSQL.
        """
        logger.info("Testando busca de produtos")
        
        # Buscar todos os produtos (limite de 5 para o teste)
        products = self.product_service.search_products(limit=5)
        
        self.assertIsNotNone(products, "Falha ao buscar produtos")
        logger.info(f"Encontrados {len(products)} produtos")
        
        # Verificar se retornou uma lista
        self.assertIsInstance(products, list, "Resultado deve ser uma lista")
        
        # Se tiver produtos, verificar a estrutura do primeiro
        if products:
            product = products[0]
            self.assertIn("id", product, "Produto deve ter um ID")
            self.assertIn("name", product, "Produto deve ter um nome")
            
            logger.info(f"Exemplo de produto: {product.get('name')}")
    
    def test_search_by_category(self):
        """
        Testa a busca de produtos por categoria.
        """
        logger.info("Testando busca por categoria")
        
        # Primeiro obter uma categoria válida
        # Vamos usar uma consulta direta para encontrar uma categoria
        query = "SELECT id FROM product_categories LIMIT 1"
        categories = self.hub.execute_query(query)
        
        if not categories:
            logger.warning("Nenhuma categoria encontrada, pulando teste")
            return
        
        category_id = categories[0]["id"]
        logger.info(f"Testando com categoria ID: {category_id}")
        
        # Agora buscar produtos dessa categoria
        products = self.product_service.get_by_category(category_id)
        
        self.assertIsNotNone(products, "Falha ao buscar produtos por categoria")
        logger.info(f"Encontrados {len(products)} produtos na categoria {category_id}")
    
    def test_hybrid_search(self):
        """
        Testa a busca híbrida (vetorial + SQL).
        """
        logger.info("Testando busca híbrida")
        
        # Verificar se temos a integração com Qdrant configurada
        if not hasattr(self.product_service, 'qdrant_client') or not self.product_service.qdrant_client:
            logger.warning("Qdrant não configurado, pulando teste de busca híbrida")
            return
        
        # Busca vetorial + filtros SQL
        search_params = {
            "query": "hidratante facial",
            "filters": {
                "price_min": 10,
                "price_max": 200
            },
            "limit": 5
        }
        
        try:
            results = self.product_service.hybrid_search(**search_params)
            self.assertIsNotNone(results, "Falha na busca híbrida")
            logger.info(f"Busca híbrida retornou {len(results)} resultados")
            
            # Verificar estrutura dos resultados
            if results:
                self.assertIn("id", results[0], "Resultado deve conter ID")
                self.assertIn("name", results[0], "Resultado deve conter nome")
                self.assertIn("score", results[0], "Resultado deve conter pontuação de relevância")
                
                logger.info(f"Exemplo de resultado: {results[0].get('name')} (score: {results[0].get('score')})")
        
        except Exception as e:
            logger.error(f"Erro na busca híbrida: {str(e)}")
            self.fail(f"Busca híbrida falhou com erro: {str(e)}")


if __name__ == "__main__":
    unittest.main()
