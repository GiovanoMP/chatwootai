#!/usr/bin/env python3
"""
Teste de conexões com serviços Docker para o ChatwootAI

Este script testa as conexões com os serviços essenciais (PostgreSQL, Redis e Qdrant)
conforme definido no documento de configuração do Docker.

Também verifica o funcionamento básico do DataServiceHub e do DataProxyAgent.

Uso:
    python -m tests.test_forced_connections
"""

import os
import sys
import logging
import time
import socket
from pathlib import Path
from contextlib import contextmanager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ConnectionTests")

# Adicionar diretório raiz ao path para importações relativas funcionarem
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

# Classe de teste principal
class ServiceConnectionTester:
    """Testa conexões com serviços Docker essenciais para o ChatwootAI"""
    
    def __init__(self):
        """Inicializa o testador com as configurações do ambiente"""
        # PostgreSQL
        self.pg_config = {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': int(os.environ.get('POSTGRES_PORT', '5433')),
            'database': os.environ.get('POSTGRES_DB', 'chatwootai'),
            'user': os.environ.get('POSTGRES_USER', 'postgres'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'postgres')
        }
        
        # Redis
        self.redis_config = {
            'url': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
            'host': os.environ.get('REDIS_HOST', 'localhost'),
            'port': int(os.environ.get('REDIS_PORT', '6379')),
            'db': int(os.environ.get('REDIS_DB', '0')),
            'password': os.environ.get('REDIS_PASSWORD', None)
        }
        
        # Qdrant
        self.qdrant_config = {
            'url': os.environ.get('QDRANT_URL', 'http://localhost:6335')
        }
        
        # Resultados
        self.results = {
            'postgres': False,
            'redis': False,
            'qdrant': False,
            'data_service_hub': False,
            'data_proxy_agent': False
        }

    @contextmanager
    def timed_operation(self, operation_name):
        """Context manager para medir o tempo de uma operação"""
        start_time = time.time()
        logger.info(f"Iniciando {operation_name}...")
        try:
            yield
            elapsed = time.time() - start_time
            logger.info(f"{operation_name} concluído em {elapsed:.2f} segundos")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{operation_name} falhou após {elapsed:.2f} segundos: {str(e)}")
            raise

    def check_socket(self, host, port, timeout=2.0):
        """Verifica se um host:porta está acessível"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            return True
        except Exception as e:
            logger.warning(f"Erro ao conectar a {host}:{port} - {str(e)}")
            return False

    def test_postgres_connection(self):
        """Testa a conexão com o PostgreSQL"""
        logger.info(f"Testando conexão PostgreSQL: {self.pg_config['host']}:{self.pg_config['port']}")
        
        # Primeiro verificar se a porta está acessível
        if not self.check_socket(self.pg_config['host'], self.pg_config['port']):
            logger.error("PostgreSQL não está acessível (porta fechada)")
            return False
        
        # Tentar importar psycopg2
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            logger.error("Módulo psycopg2 não está instalado")
            return False
            
        # Tentar conexão
        try:
            with self.timed_operation("Conexão PostgreSQL"):
                conn = psycopg2.connect(
                    host=self.pg_config['host'],
                    port=self.pg_config['port'],
                    dbname=self.pg_config['database'],
                    user=self.pg_config['user'],
                    password=self.pg_config['password']
                )
                
                # Testar consulta simples
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                
                if result[0] == 1:
                    logger.info("Consulta PostgreSQL bem-sucedida")
                    
                    # Listar tabelas
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                    
                    tables = cursor.fetchall()
                    logger.info(f"Tabelas encontradas no PostgreSQL: {len(tables)}")
                    for table in tables[:5]:  # Mostrar até 5 tabelas
                        logger.info(f"- {table[0]}")
                    
                    if len(tables) > 5:
                        logger.info(f"... e mais {len(tables) - 5} tabelas")
                    
                cursor.close()
                conn.close()
                
                self.results['postgres'] = True
                return True
                
        except Exception as e:
            logger.error(f"Erro na conexão com PostgreSQL: {str(e)}")
            return False

    def test_redis_connection(self):
        """Testa a conexão com o Redis"""
        logger.info(f"Testando conexão Redis: {self.redis_config['host']}:{self.redis_config['port']}")
        
        # Verificar se a porta está acessível
        if not self.check_socket(self.redis_config['host'], self.redis_config['port']):
            logger.error("Redis não está acessível (porta fechada)")
            return False
        
        # Tentar importar redis
        try:
            import redis
        except ImportError:
            logger.error("Módulo redis não está instalado")
            return False
            
        # Tentar conexão
        try:
            with self.timed_operation("Conexão Redis"):
                client = redis.Redis(
                    host=self.redis_config['host'],
                    port=self.redis_config['port'],
                    db=self.redis_config['db'],
                    password=self.redis_config['password'],
                    decode_responses=True,
                    socket_timeout=2.0
                )
                
                # Testar ping
                if client.ping():
                    logger.info("Ping Redis bem-sucedido")
                
                # Testar operações básicas
                test_key = f"test_connection_{int(time.time())}"
                test_value = "Teste de conexão ChatwootAI"
                
                client.set(test_key, test_value)
                retrieved = client.get(test_key)
                
                if retrieved == test_value:
                    logger.info(f"Operação SET/GET Redis bem-sucedida")
                    
                # Limpar chave de teste
                client.delete(test_key)
                client.close()
                
                self.results['redis'] = True
                return True
                
        except Exception as e:
            logger.error(f"Erro na conexão com Redis: {str(e)}")
            return False

    def test_qdrant_connection(self):
        """Testa a conexão com o Qdrant"""
        # Extrair host e porta do URL
        import urllib.parse
        parsed_url = urllib.parse.urlparse(self.qdrant_config['url'])
        host = parsed_url.hostname or 'localhost'
        port = parsed_url.port or 6335
        
        logger.info(f"Testando conexão Qdrant: {host}:{port}")
        
        # Verificar se a porta está acessível
        if not self.check_socket(host, port):
            logger.error("Qdrant não está acessível (porta fechada)")
            return False
        
        # Tentar importar qdrant_client
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import VectorParams, Distance
        except ImportError:
            logger.error("Módulo qdrant_client não está instalado")
            return False
            
        # Tentar conexão
        try:
            with self.timed_operation("Conexão Qdrant"):
                client = QdrantClient(url=self.qdrant_config['url'])
                
                # Testar API básica - listar coleções
                collections = client.get_collections()
                
                # Extrair nomes das coleções (formato pode variar com a versão)
                if hasattr(collections, 'collections'):
                    collection_names = [c.name for c in collections.collections]
                else:
                    collection_names = [c.get('name', str(c)) for c in collections]
                
                logger.info(f"Coleções encontradas no Qdrant: {len(collection_names)}")
                for name in collection_names[:5]:  # Mostrar até 5 coleções
                    logger.info(f"- {name}")
                
                if len(collection_names) > 5:
                    logger.info(f"... e mais {len(collection_names) - 5} coleções")
                
                # Não fechar o cliente explicitamente, ele usa gerenciamento de contexto
                
                self.results['qdrant'] = True
                return True
                
        except Exception as e:
            logger.error(f"Erro na conexão com Qdrant: {str(e)}")
            return False

    def test_data_service_hub(self):
        """Testa o DataServiceHub com as conexões configuradas"""
        logger.info("Testando DataServiceHub")
        
        try:
            from src.core.data_service_hub import DataServiceHub
            
            with self.timed_operation("Inicialização DataServiceHub"):
                hub = DataServiceHub()
                
                # Verificar se as conexões foram estabelecidas
                if hasattr(hub, 'pg_conn') and hub.pg_conn:
                    logger.info("DataServiceHub: Conexão PostgreSQL estabelecida")
                else:
                    logger.warning("DataServiceHub: Sem conexão PostgreSQL")
                
                if hasattr(hub, 'redis_client') and hub.redis_client:
                    logger.info("DataServiceHub: Conexão Redis estabelecida")
                else:
                    logger.warning("DataServiceHub: Sem conexão Redis")
                
                # Testar funções básicas do hub
                services = hub.list_services()
                logger.info(f"Serviços registrados no DataServiceHub: {len(services)}")
                for service in services[:5]:  # Mostrar até 5 serviços
                    logger.info(f"- {service}")
                
                self.results['data_service_hub'] = True
                return True
                
        except Exception as e:
            logger.error(f"Erro ao testar DataServiceHub: {str(e)}")
            return False

    def test_data_proxy_agent(self):
        """Testa o DataProxyAgent com o DataServiceHub"""
        logger.info("Testando DataProxyAgent")
        
        # Se o DataServiceHub não foi testado com sucesso, pular
        if not self.results['data_service_hub']:
            logger.warning("Pulando teste do DataProxyAgent porque o DataServiceHub falhou")
            return False
        
        try:
            from src.core.data_service_hub import DataServiceHub
            from src.core.data_proxy_agent import DataProxyAgent
            
            with self.timed_operation("Inicialização DataProxyAgent"):
                hub = DataServiceHub()
                
                # Tentar obter uma instância do agente pelo método do hub
                if hasattr(hub, 'get_data_proxy_agent'):
                    try:
                        agent = hub.get_data_proxy_agent()
                        logger.info(f"DataProxyAgent obtido via hub: {agent}")
                        self.results['data_proxy_agent'] = True
                        return True
                    except Exception as agent_error:
                        # Tentar instanciar diretamente como plano B
                        try:
                            agent = DataProxyAgent(data_service_hub=hub)
                            logger.info(f"DataProxyAgent criado diretamente: {agent}")
                            self.results['data_proxy_agent'] = True
                            return True
                        except Exception as direct_error:
                            logger.error(f"Tentativa direta de criar o DataProxyAgent também falhou: {str(direct_error)}")
                            return False
                else:
                    logger.warning("Método get_data_proxy_agent não encontrado no DataServiceHub")
                    return False
                
        except Exception as e:
            logger.error(f"Erro ao testar DataProxyAgent: {str(e)}")
            return False

    def run_all_tests(self):
        """Executa todos os testes de conexão em sequência"""
        logger.info("Iniciando testes de conexão com serviços Docker")
        
        # Teste de PostgreSQL
        pg_success = self.test_postgres_connection()
        
        # Teste de Redis
        redis_success = self.test_redis_connection()
        
        # Teste de Qdrant
        qdrant_success = self.test_qdrant_connection()
        
        # Se todas as conexões básicas estiverem funcionando, testar componentes
        if pg_success and redis_success and qdrant_success:
            logger.info("Conexões básicas funcionando, testando componentes do sistema")
            self.test_data_service_hub()
            self.test_data_proxy_agent()
        
        # Exibir resumo
        self.display_results()
        
        # Retornar True se todos os testes passaram
        return all(self.results.values())

    def display_results(self):
        """Exibe um resumo dos resultados dos testes"""
        logger.info("\n" + "="*50)
        logger.info("RESUMO DOS TESTES DE CONEXÃO")
        logger.info("="*50)
        
        for service, success in self.results.items():
            status = "✅ PASSOU" if success else "❌ FALHOU"
            logger.info(f"{service.replace('_', ' ').title()}: {status}")
            
        logger.info("="*50)


# Ponto de entrada para execução direta
if __name__ == "__main__":
    tester = ServiceConnectionTester()
    success = tester.run_all_tests()
    
    # Sair com código de erro se algum teste falhou
    sys.exit(0 if success else 1)
