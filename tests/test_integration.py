"""
Teste de integração entre os serviços de dados

Este teste verifica a integração entre os diferentes serviços
de dados na arquitetura, especialmente PostgreSQL e Qdrant.
"""

import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar caminho raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar componentes necessários
try:
    from src.services.data.data_service_hub import DataServiceHub
    from src.tools.vector_tools import QdrantVectorSearchTool
    IMPORTS_OK = True
except ImportError as e:
    logger.error(f"Erro ao importar dependências: {str(e)}")
    IMPORTS_OK = False


class TestIntegration(unittest.TestCase):
    """
    Testes de integração entre os serviços de dados
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Configuração inicial para os testes.
        """
        if not IMPORTS_OK:
            logger.error("Importações falharam, pulando testes")
            return
            
        logger.info("Iniciando testes de integração")
        
        # Verificar se o serviço Qdrant está acessível
        import socket
        
        def check_port(host, port, timeout=1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                sock.connect((host, port))
                sock.close()
                return True
            except:
                sock.close()
                return False
        
        # Verificar se a porta do Qdrant está acessível (6335 -> 6333)
        cls.qdrant_available = check_port("localhost", 6335)
        
        if not cls.qdrant_available:
            logger.warning("Qdrant não está acessível em localhost:6335")
            logger.warning("Alguns testes de integração podem falhar")
        
        # Criar o DataServiceHub com configuração personalizada
        cls.config = {
            'postgres': {
                'host': 'localhost',
                'port': '5433',
                'user': 'postgres',
                'password': 'postgres',
                'database': 'chatwootai'
            },
            'redis': {
                # Usar configuração mínima para Redis
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': None
            }
        }
        
        try:
            cls.hub = DataServiceHub(config=cls.config)
            logger.info("DataServiceHub inicializado com sucesso")
            
            # Inicializar o QdrantVectorSearchTool se o Qdrant estiver disponível
            if cls.qdrant_available:
                cls.vector_tool = QdrantVectorSearchTool(
                    qdrant_url="http://localhost:6335",
                    collection_name="products",
                    top_k=10  # Número de resultados a retornar na busca
                )
                logger.info("QdrantVectorSearchTool inicializado com sucesso")
            else:
                cls.vector_tool = None
            
        except Exception as e:
            logger.error(f"Erro ao inicializar componentes: {str(e)}")
            cls.hub = None
            cls.vector_tool = None
    
    @classmethod
    def tearDownClass(cls):
        """
        Limpeza após os testes.
        """
        if cls.hub:
            # Fechar conexões
            if cls.hub.pg_conn:
                cls.hub.pg_conn.close()
                logger.info("Conexão PostgreSQL fechada")
    
    def setUp(self):
        """
        Preparação antes de cada teste.
        """
        if not IMPORTS_OK or not self.hub or not self.hub.pg_conn:
            self.skipTest("Componentes não inicializados corretamente")
    
    def test_product_search(self):
        """
        Testa a busca de produtos no PostgreSQL.
        """
        logger.info("Testando busca de produtos no PostgreSQL")
        
        # Consulta para buscar todos os produtos
        query = """
            SELECT * FROM products 
            LIMIT 10
        """
        
        products = self.hub.execute_query(query)
        
        # Verificar se há produtos
        self.assertTrue(len(products) > 0, "Nenhum produto encontrado no banco de dados")
        
        # Verificar se os produtos têm os campos esperados
        required_fields = ['id', 'name', 'description', 'price']
        for product in products:
            for field in required_fields:
                self.assertIn(field, product, f"Campo {field} não encontrado no produto")
        
        logger.info(f"Encontrados {len(products)} produtos")
        for i, product in enumerate(products[:3]):  # Mostrar apenas os 3 primeiros
            logger.info(f"Produto {i+1}: {product['name']} - R$ {product['price']}")
        
        logger.info("Teste de busca de produtos bem-sucedido")
    
    def test_category_count(self):
        """
        Testa a contagem de produtos por categoria.
        """
        logger.info("Testando contagem de produtos por categoria")
        
        # Consulta para contar categorias de produtos 
        # Ajustado para o esquema real do banco
        query = """
            SELECT name as category, COUNT(*) as product_count 
            FROM product_categories
            GROUP BY name
            ORDER BY product_count DESC
        """
        
        categories = self.hub.execute_query(query)
        
        # Verificar se há categorias
        self.assertTrue(len(categories) > 0, "Nenhuma categoria encontrada no banco de dados")
        
        logger.info(f"Encontradas {len(categories)} categorias com produtos")
        for i, category in enumerate(categories[:5]):  # Mostrar apenas as 5 primeiras
            logger.info(f"Categoria {i+1}: {category['category']} - {category['product_count']} produtos")
        
        logger.info("Teste de contagem de produtos por categoria bem-sucedido")
    
    def test_vector_search(self):
        """
        Testa a busca vetorial usando Qdrant.
        """
        # Verificar se o Qdrant está disponível antes de executar o teste
        if not hasattr(self.__class__, 'qdrant_available') or not self.__class__.qdrant_available:
            self.skipTest("Qdrant não está disponível")
            
        if not self.vector_tool:
            self.skipTest("QdrantVectorSearchTool não foi inicializado")
        
        logger.info("Testando busca vetorial usando Qdrant")
        
        # Gerar um vetor de consulta aleatório
        # Ada 2 embeddings são 1536-dimensionais
        query_vector = np.random.rand(1536).tolist()
        
        # Temos que lidar com o fato de que a função search espera uma string, não um vetor
        # Vamos criar um método auxiliar para realizar a busca diretamente no cliente Qdrant
        def search_with_vector(client, collection_name, vector, limit=5):
            try:
                # Usar diretamente o cliente Qdrant para buscar com o vetor
                # Usando query_points em vez de search (que está obsoleto)
                # O parâmetro correto é 'query' em vez de 'query_vector'
                results = client.qdrant_client.query_points(
                    collection_name=collection_name,
                    query=vector,
                    limit=limit
                )
                
                # query_points retorna um objeto QueryResponse que tem um campo 'points'
                # Cada ponto tem os campos 'id', 'payload' e 'score'
                formatted_results = []
                # Verificar se temos resultados
                if hasattr(results, 'points') and results.points:
                    for point in results.points:
                        formatted_results.append({
                            "score": point.score,
                            "payload": point.payload,
                            "id": point.id
                        })
                return formatted_results
            except Exception as e:
                logger.error(f"Erro ao buscar no Qdrant: {e}")
                return []
        
        # Realizar uma busca vetorial usando nossa função auxiliar
        try:
            results = search_with_vector(
                client=self.vector_tool,
                collection_name=self.vector_tool.collection_name,
                vector=query_vector,
                limit=5
            )
            
            # Verificar se há resultados
            self.assertTrue(len(results) > 0, "Nenhum resultado encontrado na busca vetorial")
            
            logger.info(f"Encontrados {len(results)} resultados na busca vetorial")
            for i, result in enumerate(results):
                logger.info(f"Resultado {i+1}: ID={result['id']}, Score={result['score']:.4f}")
                
                # Se tivermos product_id, buscar informações no PostgreSQL
                if 'product_id' in result['payload']:
                    product_id = result['payload']['product_id']
                    product_query = "SELECT * FROM products WHERE id = %(id)s"
                    product = self.hub.execute_query(product_query, {"id": product_id}, fetch_all=False)
                    
                    if product:
                        logger.info(f"   Produto: {product['name']} - R$ {product['price']}")
            
            logger.info("Teste de busca vetorial bem-sucedido")
        except Exception as e:
            self.fail(f"Erro ao realizar busca vetorial: {str(e)}")
    
    def test_hybrid_search_mock(self):
        """
        Testa a busca híbrida (SQL + vetorial) usando um mock para o Qdrant.
        """
        logger.info("Testando busca híbrida (SQL + vetor) com mock")
        
        # Criar um mock para o QdrantVectorSearchTool
        mock_vector_tool = MagicMock()
        mock_vector_tool.search.return_value = [
            {
                'id': 1, 
                'score': 0.95, 
                'payload': {'product_id': 1, 'name': 'Produto 1'}
            },
            {
                'id': 2, 
                'score': 0.85, 
                'payload': {'product_id': 2, 'name': 'Produto 2'}
            },
            {
                'id': 3, 
                'score': 0.75, 
                'payload': {'product_id': 3, 'name': 'Produto 3'}
            }
        ]
        
        # Função que simula uma busca híbrida real
        def hybrid_search(query_text, limit=5):
            # 1. Busca semântica/vetorial
            # (Na implementação real, transformaríamos o texto em vetor usando embeddings)
            vector_results = mock_vector_tool.search(
                query_vector=[0.1] * 1536,  # Vetor dummy para o mock (Ada 2 possui 1536 dimensões)
                limit=limit * 2  # Buscamos mais resultados para depois filtrar
            )
            
            # Extrair IDs de produtos dos resultados vetoriais
            product_ids = [item['payload']['product_id'] for item in vector_results if 'product_id' in item['payload']]
            
            if not product_ids:
                return []
            
            # 2. Busca no banco de dados relacional para obter detalhes completos
            # Adaptando para o esquema real do banco
            product_ids_str = ', '.join([str(pid) for pid in product_ids])
            sql_query = f"""
                SELECT p.*, pc.name as category
                FROM products p
                LEFT JOIN product_categories pc ON pc.id IN (
                    SELECT id FROM product_categories WHERE name ~ (
                        SELECT REGEXP_REPLACE(p.name, '^(.*?)\\s.*$', '\\1')
                    ) LIMIT 1
                )
                WHERE p.id IN ({product_ids_str})
                ORDER BY p.id
                LIMIT {limit}
            """
            
            # Sem necessidade de parâmetros, já que incorporamos os IDs na string SQL
            query_params = None
            
            # Executar a consulta
            products = self.hub.execute_query(sql_query)
            
            # 3. Combinar os resultados e calcular pontuação híbrida
            hybrid_results = []
            for product in products:
                # Encontrar o score vetorial correspondente
                vector_score = 0.0
                for vr in vector_results:
                    if vr['payload'].get('product_id') == product['id']:
                        vector_score = vr['score']
                        break
                
                # Adicionar ao resultado híbrido com score combinado
                hybrid_results.append({
                    'id': product['id'],
                    'name': product['name'],
                    'price': product['price'],
                    'category': product.get('category', 'Sem categoria'),
                    'vector_score': vector_score,
                    # Poderíamos adicionar outros scores aqui (popularidade, relevância, etc)
                    'hybrid_score': vector_score  # Na implementação real, seria uma fórmula mais complexa
                })
            
            # Ordenar por pontuação híbrida
            hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            return hybrid_results
        
        # Executar a busca híbrida
        results = hybrid_search("creme facial hidratante", limit=3)
        
        # Verificar se o mock foi chamado
        mock_vector_tool.search.assert_called_once()
        
        # Verificar se há resultados híbridos
        self.assertTrue(len(results) > 0, "Nenhum resultado híbrido encontrado")
        
        logger.info(f"Encontrados {len(results)} resultados na busca híbrida")
        for i, result in enumerate(results):
            logger.info(f"Resultado {i+1}: {result['name']} - Score: {result['hybrid_score']:.4f}")
        
        logger.info("Teste de busca híbrida bem-sucedido")


if __name__ == "__main__":
    unittest.main()
