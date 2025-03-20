#!/usr/bin/env python3
"""
Teste básico de conexão com Redis

Este teste verifica a conexão com o Redis rodando no Docker
e executa operações básicas para verificar o funcionamento.
"""

import os
import sys
import logging
import unittest
import time
import socket
from pathlib import Path

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


class TestRedisConnection(unittest.TestCase):
    """Testes básicos de conexão com Redis"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para os testes"""
        # Configurações do Redis - priorizando localhost para os testes
        cls.redis_config = {
            'host': os.environ.get('REDIS_HOST', 'localhost'),
            'port': int(os.environ.get('REDIS_PORT', '6379')),
            'db': int(os.environ.get('REDIS_DB', '0')),
            'password': os.environ.get('REDIS_PASSWORD', None)
        }
        
        cls.redis_url = os.environ.get('REDIS_URL', f"redis://{cls.redis_config['host']}:{cls.redis_config['port']}/{cls.redis_config['db']}")
        
        logger.info(f"Configuração Redis: {cls.redis_config}")
        logger.info(f"Redis URL: {cls.redis_url}")
        
        # Verificar se o serviço Redis está acessível (socket check)
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
            import redis
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
            
        except ImportError:
            logger.error("Módulo redis não está instalado")
            cls.client = None
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
    
    def test_expiration(self):
        """Teste de expiração de chave no Redis"""
        if not self.client:
            self.skipTest("Conexão com Redis não disponível")
        
        # Definir uma chave para o teste
        test_key = "test_expiration_" + str(int(time.time()))
        test_value = "Temporary Value"
        
        try:
            # Definir um valor com expiração de 1 segundo
            self.client.set(test_key, test_value, ex=1)
            
            # Verificar se o valor existe
            result = self.client.get(test_key)
            self.assertEqual(result, test_value, "O valor inicial não foi armazenado corretamente")
            
            # Esperar pela expiração
            time.sleep(1.5)
            
            # Verificar se o valor expirou
            result = self.client.get(test_key)
            self.assertIsNone(result, "A chave não expirou como esperado")
            
            logger.info(f"Teste de expiração bem-sucedido para a chave: {test_key}")
        finally:
            # Garantir que a chave seja removida
            self.client.delete(test_key)


if __name__ == "__main__":
    unittest.main()
