"""
Teste básico de conexão com Qdrant

Este teste verifica a conexão com o Qdrant rodando no Docker
e executa operações básicas para verificar o funcionamento.
"""

import os
import sys
import logging
import unittest
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import VectorParams, Distance

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar caminho raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestQdrantConnection(unittest.TestCase):
    """Testes básicos de conexão com Qdrant"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para os testes"""
        # Configurações do Qdrant - usando a porta mapeada 6335
        cls.qdrant_url = "http://localhost:6335"
        
        logger.info(f"Configurando conexão com Qdrant: {cls.qdrant_url}")
        
        # Verificar se o serviço está acessível antes de tentar conectar
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
        
        # Verificar se a porta do Qdrant está acessível
        qdrant_available = check_port("localhost", 6335)
        
        if not qdrant_available:
            logger.warning(f"Qdrant não está acessível em localhost:6335")
            logger.warning("Pulando testes Qdrant - serviço não disponível")
            cls.qdrant_client = None
            return
        
        # Tentar conexão com Qdrant
        try:
            cls.qdrant_client = QdrantClient(url=cls.qdrant_url)
            # Fazer uma chamada simples para verificar a conexão
            collections_response = cls.qdrant_client.get_collections()
            # Extrair nomes das coleções (formato pode variar dependendo da versão da API)
            if hasattr(collections_response, 'collections'):
                # Novo formato da API
                collection_names = [c.name for c in collections_response.collections]
            else:
                # Formato mais antigo ou personalizado
                collection_names = [c[0] if isinstance(c, tuple) else c.get('name', str(c)) 
                                  for c in collections_response]
            
            logger.info(f"Conexão com Qdrant estabelecida. Coleções disponíveis: {collection_names}")
            
            # Nome da coleção para testes
            cls.test_collection = "test_collection"
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao Qdrant: {str(e)}")
            cls.qdrant_client = None
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        # Limpar a coleção de teste, se existir
        if cls.qdrant_client and hasattr(cls, 'test_collection'):
            try:
                collections_response = cls.qdrant_client.get_collections()
                
                # Extrair nomes das coleções (compatível com diferentes formatos de API)
                if hasattr(collections_response, 'collections'):
                    collection_names = [c.name for c in collections_response.collections]
                else:
                    collection_names = [c[0] if isinstance(c, tuple) else 
                                      (c.get('name', str(c)) if isinstance(c, dict) else str(c)) 
                                      for c in collections_response]
                
                if cls.test_collection in collection_names:
                    cls.qdrant_client.delete_collection(cls.test_collection)
                    logger.info(f"Coleção de teste {cls.test_collection} removida")
            except Exception as e:
                logger.warning(f"Erro ao limpar a coleção de teste: {str(e)}")
    
    def setUp(self):
        """Preparação antes de cada teste"""
        if not self.qdrant_client:
            self.skipTest("Conexão com Qdrant não disponível")
    
    def test_create_collection(self):
        """Testa a criação de uma coleção"""
        logger.info("Testando criação de coleção")
        
        # Verificar se a coleção já existe e removê-la
        collections_response = self.qdrant_client.get_collections()
        
        # Extrair nomes das coleções (compatível com diferentes formatos de API)
        if hasattr(collections_response, 'collections'):
            collection_names = [c.name for c in collections_response.collections]
        else:
            collection_names = [c[0] if isinstance(c, tuple) else 
                              (c.get('name', str(c)) if isinstance(c, dict) else str(c)) 
                              for c in collections_response]
        
        if self.test_collection in collection_names:
            self.qdrant_client.delete_collection(self.test_collection)
            logger.info(f"Coleção existente {self.test_collection} removida")
        
        # Criar uma nova coleção
        self.qdrant_client.create_collection(
            collection_name=self.test_collection,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        
        # Verificar se a coleção foi criada
        collections_response = self.qdrant_client.get_collections()
        
        # Extrair nomes das coleções (compatível com diferentes formatos de API)
        if hasattr(collections_response, 'collections'):
            collection_names = [c.name for c in collections_response.collections]
        else:
            collection_names = [c[0] if isinstance(c, tuple) else 
                              (c.get('name', str(c)) if isinstance(c, dict) else str(c)) 
                              for c in collections_response]
        
        self.assertIn(
            self.test_collection, 
            collection_names,
            f"A coleção {self.test_collection} não foi criada corretamente"
        )
        
        logger.info(f"Coleção {self.test_collection} criada com sucesso")
    
    def test_insert_search(self):
        """Testa inserção e busca de vetores"""
        logger.info("Testando inserção e busca de vetores")
        
        # Garantir que a coleção de teste existe
        try:
            collections_response = self.qdrant_client.get_collections()
            
            # Extrair nomes das coleções (compatível com diferentes formatos de API)
            if hasattr(collections_response, 'collections'):
                collection_names = [c.name for c in collections_response.collections]
            else:
                collection_names = [c[0] if isinstance(c, tuple) else 
                                  (c.get('name', str(c)) if isinstance(c, dict) else str(c)) 
                                  for c in collections_response]
            
            if self.test_collection not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.test_collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Coleção {self.test_collection} criada para o teste")
        except Exception as e:
            self.fail(f"Falha ao preparar coleção para o teste: {str(e)}")
        
        # Inserir alguns pontos de teste
        import numpy as np
        
        # Criar vetores de teste (3 vetores de dimensão 384)
        test_vectors = [
            np.random.rand(384).tolist(),
            np.random.rand(384).tolist(),
            np.random.rand(384).tolist()
        ]
        
        # Metadados para os pontos
        payloads = [
            {"name": "item1", "category": "test"},
            {"name": "item2", "category": "test"},
            {"name": "item3", "category": "other"}
        ]
        
        # IDs para os pontos
        ids = [1, 2, 3]
        
        # Inserir os pontos
        try:
            operation_info = self.qdrant_client.upsert(
                collection_name=self.test_collection,
                points=[
                    {"id": id, "vector": vector, "payload": payload}
                    for id, vector, payload in zip(ids, test_vectors, payloads)
                ]
            )
            logger.info(f"Pontos inseridos: {operation_info}")
            
            # Buscar pontos por ID
            points = self.qdrant_client.retrieve(
                collection_name=self.test_collection,
                ids=ids
            )
            
            # Verificar se todos os pontos foram recuperados
            self.assertEqual(len(points), 3, "Nem todos os pontos foram recuperados")
            
            # Fazer uma busca por similaridade usando o primeiro vetor
            search_results = self.qdrant_client.search(
                collection_name=self.test_collection,
                query_vector=test_vectors[0],
                limit=3
            )
            
            # Verificar se temos resultados de busca
            self.assertTrue(len(search_results) > 0, "A busca não retornou resultados")
            
            logger.info(f"Busca retornou {len(search_results)} resultados")
            for i, result in enumerate(search_results):
                logger.info(f"Resultado {i+1}: ID={result.id}, Score={result.score}, Payload={result.payload}")
            
        except Exception as e:
            self.fail(f"Falha no teste de inserção/busca: {str(e)}")


if __name__ == "__main__":
    unittest.main()
