"""
Teste básico de conexão com Redis

Este teste verifica a conexão com o Redis rodando no Docker
e executa operações básicas para verificar o funcionamento.
"""

import os
import sys
import logging
import redis
import unittest
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar caminho raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestRedisConnection(unittest.TestCase):
    """Testes básicos de conexão com Redis"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para os testes"""
        # Forçar uso de localhost para testes, ignorando variáveis de ambiente que podem apontar para IPs internos do Docker
        cls.redis_config = {
            'host': 'localhost',  # Forçar localhost
            'port': 6379,          # Porta padrão
            'db': 0,
            'password': None       # Sem senha para teste local
        }
        
        logger.info(f"Configuração Redis: {cls.redis_config}")
        
        # Verificar se o serviço Redis está acessível (socket check)
        import socket
        import time
        
        # Função para verificar se a porta está aberta
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
        
        # Verificar se a porta do Redis está acessível
        redis_available = check_port(cls.redis_config['host'], cls.redis_config['port'])
        
        if not redis_available:
            logger.warning(f"Redis não está acessível em {cls.redis_config['host']}:{cls.redis_config['port']}")
            logger.warning("Pulando testes Redis - serviço não disponível")
            cls.client = None
            return
        
        # Testar conexão com Redis
        try:
            # Conectar usando parâmetros básicos
            cls.client = redis.Redis(
                host=cls.redis_config['host'],
                port=cls.redis_config['port'],
                db=cls.redis_config['db'],
                password=cls.redis_config['password'],
                decode_responses=True,
                socket_timeout=2.0  # Timeout curto para evitar esperas longas
            )
            
            # Verificar conexão com ping
            cls.client.ping()
            logger.info(f"Conexão com Redis estabelecida: {cls.redis_config['host']}:{cls.redis_config['port']}")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            cls.client = None
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        if cls.client:
            cls.client.close()
            logger.info("Conexão com Redis encerrada")
    
    def test_set_get(self):
        """Teste básico de set/get no Redis"""
        if not self.client:
            self.skipTest("Conexão com Redis não disponível")
        
        # Definir uma chave para o teste
        test_key = "test_connection_" + str(int(time.time()))
        test_value = "Hello Redis!"
        
        try:
            # Definir um valor
            self.client.set(test_key, test_value)
            
            # Obter o valor
            result = self.client.get(test_key)
            
            # Verificar o resultado
            self.assertEqual(result, test_value, "O valor recuperado não corresponde ao valor definido")
            
            logger.info(f"Teste SET/GET bem-sucedido para a chave: {test_key}")
        finally:
            # Limpar a chave de teste
            self.client.delete(test_key)
    
    def test_hash_operations(self):
        """Teste de operações com hash no Redis"""
        if not self.client:
            self.skipTest("Conexão com Redis não disponível")
        
        # Definir uma chave para o teste
        hash_key = "test_hash_" + str(int(time.time()))
        
        try:
            # Definir campos no hash
            self.client.hset(hash_key, "field1", "value1")
            self.client.hset(hash_key, "field2", "value2")
            
            # Obter todos os campos
            hash_data = self.client.hgetall(hash_key)
            
            # Verificar resultados
            self.assertEqual(len(hash_data), 2, "O hash deve ter 2 campos")
            self.assertEqual(hash_data["field1"], "value1", "O valor do campo1 não corresponde")
            self.assertEqual(hash_data["field2"], "value2", "O valor do campo2 não corresponde")
            
            logger.info(f"Teste de operações HASH bem-sucedido para a chave: {hash_key}")
        finally:
            # Limpar a chave de teste
            self.client.delete(hash_key)


if __name__ == "__main__":
    unittest.main()
