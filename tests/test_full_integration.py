#!/usr/bin/env python3
"""
Teste de Integração Completa do Sistema ChatwootAI

Este script realiza testes abrangentes para verificar se todos os componentes
do sistema ChatwootAI estão funcionando corretamente juntos, incluindo:
- Conexões com bancos de dados (PostgreSQL, Redis, Qdrant)
- Funcionamento do DataServiceHub
- Integração dos plugins
- Fluxo completo de processamento de mensagens

Autor: Giovano
Data: 22/03/2025
"""

import os
import sys
import json
import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

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

class TestFullIntegration(unittest.TestCase):
    """Testes de integração completa do sistema ChatwootAI"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        logger.info("Iniciando testes de integração completa")
        
        # Registrar hora de início
        cls.start_time = datetime.now()
        
        # Armazenar resultados dos testes
        cls.test_results = {
            "database_connections": {},
            "service_hub": {},
            "plugins": {},
            "message_flow": {}
        }
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        # Calcular tempo total de execução
        execution_time = datetime.now() - cls.start_time
        
        # Exibir resumo dos testes
        logger.info("=" * 80)
        logger.info(f"RESUMO DOS TESTES (Tempo total: {execution_time})")
        logger.info("=" * 80)
        
        # Exibir resultados por categoria
        for category, results in cls.test_results.items():
            success = sum(1 for result in results.values() if result.get("status") == "success")
            total = len(results)
            
            if total > 0:
                logger.info(f"{category.upper()}: {success}/{total} testes bem-sucedidos ({success/total*100:.1f}%)")
            
            # Exibir detalhes de falhas
            failures = {name: details for name, details in results.items() 
                       if details.get("status") != "success"}
            
            if failures:
                logger.info(f"Falhas em {category}:")
                for name, details in failures.items():
                    logger.info(f"  - {name}: {details.get('message', 'Erro desconhecido')}")
        
        logger.info("=" * 80)
    
    def timed_operation(self, operation_name):
        """Decorator para medir o tempo de execução de operações"""
        class TimedContext:
            def __init__(self, test_case, operation_name):
                self.test_case = test_case
                self.operation_name = operation_name
            
            def __enter__(self):
                self.start_time = datetime.now()
                logger.info(f"Iniciando: {self.operation_name}")
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                execution_time = datetime.now() - self.start_time
                if exc_type is None:
                    logger.info(f"Concluído: {self.operation_name} em {execution_time}")
                else:
                    logger.error(f"Falha: {self.operation_name} após {execution_time}")
                return False
        
        return TimedContext(self, operation_name)
    
    def record_result(self, category, name, status, message=None, details=None):
        """Registra o resultado de um teste"""
        self.test_results[category][name] = {
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_01_postgres_connection(self):
        """Testa a conexão com o PostgreSQL"""
        logger.info("Testando conexão com PostgreSQL")
        
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Configurações do PostgreSQL
            pg_config = {
                'host': os.environ.get('POSTGRES_HOST', 'localhost'),
                'port': os.environ.get('POSTGRES_PORT', '5433'),
                'user': os.environ.get('POSTGRES_USER', 'postgres'),
                'password': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
                'database': os.environ.get('POSTGRES_DB', 'chatwootai')
            }
            
            with self.timed_operation("Conexão PostgreSQL"):
                # Tentar conectar ao PostgreSQL
                conn = psycopg2.connect(
                    host=pg_config['host'],
                    port=pg_config['port'],
                    user=pg_config['user'],
                    password=pg_config['password'],
                    database=pg_config['database']
                )
                
                # Verificar se a conexão está ativa
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    
                    self.assertEqual(result['test'], 1, "Consulta de teste falhou")
                    logger.info("Conexão com PostgreSQL estabelecida com sucesso")
                
                # Fechar conexão
                conn.close()
            
            self.record_result("database_connections", "postgres", "success")
        
        except ImportError as e:
            logger.warning(f"Módulo psycopg2 não encontrado: {str(e)}")
            self.record_result("database_connections", "postgres", "skipped", 
                              f"Módulo não encontrado: {str(e)}")
            self.skipTest("Módulo psycopg2 não encontrado")
        
        except Exception as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {str(e)}")
            self.record_result("database_connections", "postgres", "failure", str(e))
            self.fail(f"Erro ao conectar ao PostgreSQL: {str(e)}")
    
    def test_02_redis_connection(self):
        """Testa a conexão com o Redis"""
        logger.info("Testando conexão com Redis")
        
        try:
            import redis
            
            # Configurações do Redis
            redis_config = {
                'host': os.environ.get('REDIS_HOST', 'localhost'),
                'port': int(os.environ.get('REDIS_PORT', '6379')),
                'db': int(os.environ.get('REDIS_DB', '0')),
                'password': os.environ.get('REDIS_PASSWORD', None)
            }
            
            with self.timed_operation("Conexão Redis"):
                # Tentar conectar ao Redis
                r = redis.Redis(
                    host=redis_config['host'],
                    port=redis_config['port'],
                    db=redis_config['db'],
                    password=redis_config['password']
                )
                
                # Verificar se a conexão está ativa
                test_key = "chatwootai:test:connection"
                test_value = "test_value"
                
                # Definir valor de teste
                r.set(test_key, test_value)
                
                # Recuperar valor de teste
                retrieved_value = r.get(test_key)
                
                # Limpar após o teste
                r.delete(test_key)
                
                # Verificar se o valor recuperado é o mesmo que foi definido
                self.assertEqual(retrieved_value.decode('utf-8'), test_value, 
                                "Valor recuperado do Redis não corresponde ao valor definido")
                
                logger.info("Conexão com Redis estabelecida com sucesso")
            
            self.record_result("database_connections", "redis", "success")
        
        except ImportError as e:
            logger.warning(f"Módulo redis não encontrado: {str(e)}")
            self.record_result("database_connections", "redis", "skipped", 
                              f"Módulo não encontrado: {str(e)}")
            self.skipTest("Módulo redis não encontrado")
        
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            self.record_result("database_connections", "redis", "failure", str(e))
            self.fail(f"Erro ao conectar ao Redis: {str(e)}")
    
    def test_03_qdrant_connection(self):
        """Testa a conexão com o Qdrant"""
        logger.info("Testando conexão com Qdrant")
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            # Configurações do Qdrant
            qdrant_url = os.environ.get('QDRANT_URL', 'http://localhost:6335')
            
            with self.timed_operation("Conexão Qdrant"):
                # Tentar conectar ao Qdrant
                client = QdrantClient(url=qdrant_url)
                
                # Verificar se a conexão está ativa criando uma coleção de teste
                collection_name = "chatwootai_test_collection"
                
                # Verificar se a coleção já existe e excluí-la se necessário
                collections = client.get_collections().collections
                collection_names = [collection.name for collection in collections]
                
                if collection_name in collection_names:
                    client.delete_collection(collection_name=collection_name)
                
                # Criar coleção de teste
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE)
                )
                
                # Verificar se a coleção foi criada
                collections = client.get_collections().collections
                collection_names = [collection.name for collection in collections]
                
                self.assertIn(collection_name, collection_names, 
                             f"Coleção {collection_name} não foi criada")
                
                # Excluir coleção de teste
                client.delete_collection(collection_name=collection_name)
                
                logger.info("Conexão com Qdrant estabelecida com sucesso")
            
            self.record_result("database_connections", "qdrant", "success")
        
        except ImportError as e:
            logger.warning(f"Módulo qdrant_client não encontrado: {str(e)}")
            self.record_result("database_connections", "qdrant", "skipped", 
                              f"Módulo não encontrado: {str(e)}")
            self.skipTest("Módulo qdrant_client não encontrado")
        
        except Exception as e:
            logger.error(f"Erro ao conectar ao Qdrant: {str(e)}")
            self.record_result("database_connections", "qdrant", "failure", str(e))
            self.fail(f"Erro ao conectar ao Qdrant: {str(e)}")
    
    def test_04_data_service_hub(self):
        """Testa o DataServiceHub"""
        logger.info("Testando DataServiceHub")
        
        try:
            from src.core.data_service_hub import DataServiceHub
            
            with self.timed_operation("Inicialização DataServiceHub"):
                # Inicializar o DataServiceHub
                hub = DataServiceHub()
                
                # Verificar se o hub foi inicializado corretamente
                self.assertIsNotNone(hub, "DataServiceHub não foi inicializado corretamente")
                
                # Verificar conexões
                if hasattr(hub, 'pg_conn') and hub.pg_conn:
                    logger.info("DataServiceHub: Conexão PostgreSQL estabelecida")
                else:
                    logger.warning("DataServiceHub: Sem conexão PostgreSQL")
                
                if hasattr(hub, 'redis_client') and hub.redis_client:
                    logger.info("DataServiceHub: Conexão Redis estabelecida")
                else:
                    logger.warning("DataServiceHub: Sem conexão Redis")
                
                # Verificar serviços registrados
                services = hub.list_services()
                logger.info(f"Serviços registrados no DataServiceHub: {len(services)}")
                for service_name in services:
                    logger.info(f"  - {service_name}")
            
            self.record_result("service_hub", "initialization", "success")
        
        except ImportError as e:
            logger.error(f"Módulo DataServiceHub não encontrado: {str(e)}")
            self.record_result("service_hub", "initialization", "failure", 
                              f"Módulo não encontrado: {str(e)}")
            self.fail(f"Módulo DataServiceHub não encontrado: {str(e)}")
        
        except Exception as e:
            logger.error(f"Erro ao testar DataServiceHub: {str(e)}")
            self.record_result("service_hub", "initialization", "failure", str(e))
            self.fail(f"Erro ao testar DataServiceHub: {str(e)}")
    
    def test_05_plugin_manager(self):
        """Testa o PluginManager e os plugins implementados"""
        logger.info("Testando PluginManager e plugins")
        
        try:
            from src.plugins.core.plugin_manager import PluginManager
            
            with self.timed_operation("Inicialização PluginManager"):
                # Inicializar o PluginManager
                plugin_config = {
                    "plugin_paths": ["src.plugins.implementations"],
                    "plugins": {},
                    "enabled_plugins": [
                        "sentiment_analysis_plugin",
                        "response_enhancer_plugin",
                        "faq_knowledge_plugin"
                    ]
                }
                plugin_manager = PluginManager(plugin_config)
                
                # Descobrir plugins disponíveis
                available_plugins = plugin_manager.discover_plugins()
                logger.info(f"Plugins disponíveis: {len(available_plugins)}")
                for plugin_name in available_plugins:
                    logger.info(f"  - {plugin_name}")
                
                # Verificar se os plugins que implementamos estão disponíveis
                expected_plugins = [
                    "sentiment_analysis_plugin",
                    "response_enhancer_plugin",
                    "faq_knowledge_plugin"
                ]
                
                for plugin in expected_plugins:
                    self.assertIn(plugin, available_plugins, 
                                 f"Plugin {plugin} não foi encontrado")
                
                # Carregar os plugins
                loaded_plugins = plugin_manager.load_plugins()
                logger.info(f"Plugins carregados: {len(loaded_plugins)}")
                
                # Verificar se todos os plugins foram carregados corretamente
                self.assertEqual(len(loaded_plugins), len(expected_plugins), 
                                "Nem todos os plugins foram carregados corretamente")
            
            self.record_result("plugins", "plugin_manager", "success")
            
            # Testar cada plugin individualmente
            for plugin_name, plugin_instance in loaded_plugins.items():
                logger.info(f"Testando plugin: {plugin_name}")
                
                try:
                    # Verificar se o plugin tem o método process_message
                    self.assertTrue(hasattr(plugin_instance, "process_message"), 
                                   f"Plugin {plugin_name} não tem o método process_message")
                    
                    # Testar o plugin com uma mensagem de exemplo
                    test_message = {
                        "content": "Estou muito feliz com o produto que comprei!",
                        "sender": "customer",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Processar a mensagem com o plugin
                    # Criar um contexto vazio para passar como segundo argumento
                    empty_context = {}
                    
                    # Extrair o conteúdo da mensagem para plugins que esperam uma string
                    message_content = test_message["content"]
                    
                    # Processar a mensagem com o plugin
                    result = plugin_instance.process_message(message_content, empty_context)
                    
                    # Verificar se o resultado não é None
                    self.assertIsNotNone(result, f"Plugin {plugin_name} retornou None")
                    
                    logger.info(f"Plugin {plugin_name} testado com sucesso")
                    self.record_result("plugins", plugin_name, "success")
                
                except Exception as e:
                    logger.error(f"Erro ao testar plugin {plugin_name}: {str(e)}")
                    self.record_result("plugins", plugin_name, "failure", str(e))
        
        except ImportError as e:
            logger.error(f"Módulo PluginManager não encontrado: {str(e)}")
            self.record_result("plugins", "plugin_manager", "failure", 
                              f"Módulo não encontrado: {str(e)}")
            self.fail(f"Módulo PluginManager não encontrado: {str(e)}")
        
        except Exception as e:
            logger.error(f"Erro ao testar PluginManager: {str(e)}")
            self.record_result("plugins", "plugin_manager", "failure", str(e))
            self.fail(f"Erro ao testar PluginManager: {str(e)}")
    
    @unittest.skip("Teste de fluxo completo será implementado posteriormente")
    def test_06_full_message_flow(self):
        """Testa o fluxo completo de processamento de mensagens"""
        logger.info("Testando fluxo completo de processamento de mensagens")
        
        try:
            # Importar componentes necessários
            from src.core.hub import HubCrew
            from src.core.data_service_hub import DataServiceHub
            
            with self.timed_operation("Inicialização componentes para fluxo completo"):
                # Inicializar o DataServiceHub
                data_service_hub = DataServiceHub()
                
                # Inicializar o HubCrew
                hub_crew = HubCrew(data_service_hub=data_service_hub)
                
                # Verificar se o HubCrew foi inicializado corretamente
                self.assertIsNotNone(hub_crew, "HubCrew não foi inicializado corretamente")
                
                # Criar uma mensagem de teste
                test_message = {
                    "content": "Vocês têm creme para as mãos?",
                    "conversation_id": "123",
                    "account_id": "1",
                    "sender": {
                        "id": "456",
                        "type": "customer"
                    }
                }
                
                # Processar a mensagem
                response = hub_crew.process_message(test_message)
                
                # Verificar se a resposta não é None
                self.assertIsNotNone(response, "HubCrew não retornou resposta")
                
                logger.info(f"Resposta gerada: {response}")
            
            self.record_result("message_flow", "full_flow", "success")
        
        except ImportError as e:
            logger.error(f"Módulo não encontrado: {str(e)}")
            self.record_result("message_flow", "full_flow", "failure", 
                              f"Módulo não encontrado: {str(e)}")
            self.skipTest(f"Módulo não encontrado: {str(e)}")
        
        except Exception as e:
            logger.error(f"Erro ao testar fluxo completo: {str(e)}")
            self.record_result("message_flow", "full_flow", "failure", str(e))
            self.fail(f"Erro ao testar fluxo completo: {str(e)}")


if __name__ == "__main__":
    unittest.main()
