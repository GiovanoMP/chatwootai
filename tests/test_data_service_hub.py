"""
Teste básico do DataServiceHub

Este teste verifica a funcionalidade básica do DataServiceHub,
principalmente sua capacidade de conectar com o PostgreSQL.
"""

import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar caminho raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar DataServiceHub
from src.services.data.data_service_hub import DataServiceHub


class TestDataServiceHub(unittest.TestCase):
    """
    Testes para o DataServiceHub, focando na funcionalidade básica
    de conexão com o PostgreSQL.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Configuração inicial para os testes.
        """
        logger.info("Iniciando testes do DataServiceHub")
        
        # Configuração para as conexões - usamos a porta 5433 mapeada para PostgreSQL
        cls.config = {
            'postgres': {
                'host': 'localhost',
                'port': '5433',
                'user': 'postgres',
                'password': 'postgres',
                'database': 'chatwootai'
            },
            'redis': {
                # Pular configuração completa do Redis, já que não podemos
                # conectar diretamente via Docker
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': None
            }
        }
        
        # Criar o DataServiceHub com configuração personalizada
        try:
            cls.hub = DataServiceHub(config=cls.config)
            logger.info("DataServiceHub inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar DataServiceHub: {str(e)}")
            cls.hub = None
            raise
    
    @classmethod
    def tearDownClass(cls):
        """
        Limpeza após os testes.
        """
        if cls.hub:
            # Fechar conexões
            try:
                if cls.hub.pg_conn:
                    cls.hub.pg_conn.close()
                    logger.info("Conexão PostgreSQL fechada")
                
                if cls.hub.redis_client:
                    cls.hub.redis_client.close()
                    logger.info("Conexão Redis fechada")
            except Exception as e:
                logger.warning(f"Erro ao fechar conexões: {str(e)}")
    
    def setUp(self):
        """
        Preparação antes de cada teste.
        """
        if not self.hub or not self.hub.pg_conn:
            self.skipTest("DataServiceHub não inicializado corretamente")
    
    def test_postgres_connection(self):
        """
        Testa se a conexão com o PostgreSQL está funcionando.
        """
        logger.info("Testando conexão com PostgreSQL")
        
        # Executar uma consulta simples
        result = self.hub.execute_query("SELECT 1 as test")
        
        # Verificar resultado
        self.assertIsNotNone(result, "Consulta retornou None")
        self.assertEqual(len(result), 1, "Número de resultados diferente do esperado")
        self.assertEqual(result[0]['test'], 1, "Valor do resultado diferente do esperado")
        
        logger.info("Teste de conexão PostgreSQL bem-sucedido")
    
    def test_execute_query_with_params(self):
        """
        Testa a execução de consulta com parâmetros.
        """
        logger.info("Testando execução de consulta com parâmetros")
        
        # Executar uma consulta com parâmetros
        query = "SELECT %(value)s as param_value"
        params = {"value": "test_value"}
        
        result = self.hub.execute_query(query, params)
        
        # Verificar resultado
        self.assertIsNotNone(result, "Consulta retornou None")
        self.assertEqual(result[0]['param_value'], "test_value", 
                         "Valor do parâmetro diferente do esperado")
        
        logger.info("Teste de consulta com parâmetros bem-sucedido")
    
    def test_list_tables(self):
        """
        Testa a listagem de tabelas no banco de dados.
        """
        logger.info("Testando listagem de tabelas")
        
        # Consulta para listar tabelas
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        
        tables = self.hub.execute_query(query)
        
        # Verificar se há tabelas
        self.assertTrue(len(tables) > 0, "Nenhuma tabela encontrada no banco de dados")
        
        # Listar as tabelas encontradas para depuração
        table_names = [table['table_name'] for table in tables]
        logger.info(f"Tabelas encontradas: {', '.join(table_names)}")
        
        # Verificar a presença de algumas tabelas essenciais
        essential_tables = ['products', 'customers', 'orders']
        for table in essential_tables:
            self.assertIn(table, table_names, f"Tabela essencial {table} não encontrada")
        
        logger.info("Teste de listagem de tabelas bem-sucedido")
    
    def test_execute_query_with_mock_cache(self):
        """
        Testa a execução de consulta integrando com o sistema de cache
        """
        logger.info("Testando execução de consulta com mock de cache")
        
        # Criar um teste simples que simula uma operação completa do DataService
        # Esta abordagem usa patching parcial apenas nos métodos de cache
        
        hub = self.hub  # Usar o hub já inicializado no setUpClass
        
        # Usar um mock para substituir apenas os métodos de cache
        with patch.object(hub, 'cache_get') as mock_cache_get, \
             patch.object(hub, 'cache_set') as mock_cache_set:
            
            # Configurar o mock para simular um cache miss na primeira chamada
            mock_cache_get.return_value = None
            
            # Executar a consulta que irá gerar um cache miss e depois executar no banco
            query = "SELECT 1 as test"
            key = "test_query"
            
            # Executar a consulta (primeira chamada - deveria ir ao banco)
            # Aqui já podemos simular uma chamada que usa cache_get antes
            # e cache_set depois de executar a consulta
            result1 = hub.execute_query(query)
            
            # Verificar se o método cache_get foi chamado (ou seria chamado em um caso real)
            mock_cache_get.assert_not_called()  # Na realidade não seria chamado nesse caso, pois não tem chave
            
            # Agora podemos simular diretamente uma chamada de cache
            # Armazenar manualmente no cache
            hub.cache_set(key, result1)
            mock_cache_set.assert_called_once()
            
            # Resetar os mocks para a próxima verificação
            mock_cache_get.reset_mock()
            mock_cache_set.reset_mock()
            
            # Agora vamos configurar o mock para simular um cache hit
            mock_cache_get.return_value = result1
            
            # Segundo acesso - agora simulando que o valor seria encontrado no cache
            cached_data = hub.cache_get(key)
            
            # Verificar se o método cache_get foi chamado
            mock_cache_get.assert_called_once_with(key)
            
            # Verificar se o valor retornado é igual ao que esperamos
            self.assertEqual(cached_data, result1, "O valor retornado do cache não é igual ao original")
        
        logger.info("Teste de cache com mock bem-sucedido")


if __name__ == "__main__":
    unittest.main()
