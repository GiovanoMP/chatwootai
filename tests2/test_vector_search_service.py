import unittest
from src.services.data.vector_search_service import VectorSearchService
from unittest.mock import MagicMock

class TestVectorSearchService(unittest.TestCase):

    def setUp(self):
        # Configuração do DataServiceHub simulado
        self.data_service_hub = MagicMock()
        self.vector_service = VectorSearchService(self.data_service_hub)

    def test_initialization(self):
        # Testa se a instância é criada corretamente
        self.assertIsNotNone(self.vector_service)

    def test_get_entity_type(self):
        # Testa se o tipo de entidade é retornado corretamente
        self.assertEqual(self.vector_service.get_entity_type(), "vector")

    def test_connect_to_qdrant(self):
        # Testa a conexão com o Qdrant (simulando a configuração)
        self.vector_service.config = {"url": "http://localhost:6333", "api_key": ""}
        self.vector_service._connect_to_qdrant()
        self.assertIsNotNone(self.vector_service.client)

    def test_search_function(self):
        # Testa a função de busca (simulando a busca no Qdrant)
        self.vector_service.client = MagicMock()
        self.vector_service.client.search.return_value = [MagicMock(id='1', score=0.9, payload={})]
        results = self.vector_service.search("test query")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "1")

if __name__ == '__main__':
    unittest.main()
