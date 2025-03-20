#!/usr/bin/env python3
"""
Teste básico de conexão com Qdrant

Este teste verifica a conexão com o Qdrant rodando no Docker
e executa operações básicas para verificar o funcionamento.
"""

import os
import sys
import logging
import unittest
import socket
import numpy as np
from pathlib import Path
import urllib.parse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar caminho raiz ao path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    load_dotenv(env_path)
    logger.info(f"Variáveis de ambiente carregadas de: {env_path}")
except ImportError:
    logger.warning("python-dotenv não encontrado. Usando variáveis de ambiente do sistema.")


class TestQdrantConnection(unittest.TestCase):
    """Testes básicos de conexão com Qdrant"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para os testes"""
        # Configurações do Qdrant - usar a porta mapeada 6335
        cls.qdrant_url = os.environ.get('QDRANT_URL', 'http://localhost:6335')
        
        # Extrair host e porta do URL
        parsed_url = urllib.parse.urlparse(cls.qdrant_url)
        cls.host = parsed_url.hostname or 'localhost'
        cls.port = parsed_url.port or 6335
        
        logger.info(f"Configurando conexão com Qdrant: {cls.qdrant_url} ({cls.host}:{cls.port})")
        
        # Verificar se o serviço está acessível antes de tentar conectar
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
        qdrant_available = check_port(cls.host, cls.port)
        
        if not qdrant_available:
            logger.warning(f"Qdrant não está acessível em {cls.host}:{cls.port}")
            logger.warning("Pulando testes Qdrant - serviço não disponível")
            cls.qdrant_client = None
            return
        
        # Tentar conexão com Qdrant
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import VectorParams, Distance
            
            cls.qdrant_client = QdrantClient(url=cls.qdrant_url)
            
            # Fazer uma chamada simples para verificar a conexão
            collections_response = cls.qdrant_client.get_collections()
            
            # Extrair nomes das coleções (formato pode variar dependendo da versão da API)
            if hasattr(collections_response, 'collections'):
                # Novo formato da API
                collection_names = [c.name for c in collections_response.collections]
            else:
                # Formato mais antigo ou personalizado
                collection_names = [c.get('name', str(c)) for c in collections_response]
            
            logger.info(f"Conexão com Qdrant estabelecida. Coleções disponíveis: {collection_names}")
            
            # Nome da coleção para testes
            cls.test_collection = "test_collection"
            
        except ImportError:
            logger.error("Módulo qdrant_client não está instalado")
            cls.qdrant_client = None
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
                    collection_names = [c.get('name', str(c)) for c in collections_response]
                
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
        
        try:
            from qdrant_client.http.models import VectorParams, Distance
            
            # Verificar se a coleção já existe e removê-la
            collections_response = self.qdrant_client.get_collections()
            
            # Extrair nomes das coleções (compatível com diferentes formatos de API)
            if hasattr(collections_response, 'collections'):
                collection_names = [c.name for c in collections_response.collections]
            else:
                collection_names = [c.get('name', str(c)) for c in collections_response]
            
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
                collection_names = [c.get('name', str(c)) for c in collections_response]
            
            self.assertIn(
                self.test_collection, 
                collection_names,
                f"A coleção {self.test_collection} não foi criada corretamente"
            )
            
            logger.info(f"Coleção {self.test_collection} criada com sucesso")
        except Exception as e:
            self.fail(f"Erro ao testar criação de coleção: {str(e)}")
    
    def test_insert_search(self):
        """Testa inserção e busca de vetores"""
        logger.info("Testando inserção e busca de vetores")
        
        try:
            from qdrant_client.http.models import VectorParams, Distance
            
            # Garantir que a coleção de teste existe
            collections_response = self.qdrant_client.get_collections()
            
            # Extrair nomes das coleções (compatível com diferentes formatos de API)
            if hasattr(collections_response, 'collections'):
                collection_names = [c.name for c in collections_response.collections]
            else:
                collection_names = [c.get('name', str(c)) for c in collections_response]
            
            if self.test_collection not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.test_collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Coleção {self.test_collection} criada para o teste")
            
            # Inserir alguns pontos de teste
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
            self.qdrant_client.upsert(
                collection_name=self.test_collection,
                points=[
                    {"id": ids[0], "vector": test_vectors[0], "payload": payloads[0]},
                    {"id": ids[1], "vector": test_vectors[1], "payload": payloads[1]},
                    {"id": ids[2], "vector": test_vectors[2], "payload": payloads[2]},
                ]
            )
            
            logger.info("Pontos inseridos com sucesso")
            
            # Buscar pontos por similaridade
            query_vector = test_vectors[0]  # Usar o primeiro vetor como consulta
            search_result = self.qdrant_client.search(
                collection_name=self.test_collection,
                query_vector=query_vector,
                limit=3
            )
            
            # Verificar se os resultados foram encontrados
            self.assertGreater(len(search_result), 0, "A busca não retornou resultados")
            
            # O primeiro resultado deve ter o ID 1 (o vetor de consulta é o próprio vetor 1)
            first_result_id = search_result[0].id
            self.assertEqual(first_result_id, 1, f"O primeiro resultado deveria ter ID 1, mas tem ID {first_result_id}")
            
            logger.info("Busca vetorial executada com sucesso")
            
            # Testar filtragem por payload
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            
            filter_payload = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value="test")
                    )
                ]
            )
            
            filter_results = self.qdrant_client.search(
                collection_name=self.test_collection,
                query_vector=query_vector,
                query_filter=filter_payload,
                limit=3
            )
            
            # Deve encontrar apenas 2 resultados (item1 e item2)
            self.assertEqual(len(filter_results), 2, f"A busca filtrada deveria retornar 2 resultados, mas retornou {len(filter_results)}")
            
            logger.info("Filtragem por payload executada com sucesso")
            
        except Exception as e:
            self.fail(f"Erro ao testar inserção e busca de vetores: {str(e)}")


if __name__ == "__main__":
    unittest.main()
