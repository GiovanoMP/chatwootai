"""
DataServiceHub - Componente central da camada de serviços de dados.

Este módulo implementa o hub central que gerencia todos os serviços de dados
da aplicação, fornecendo uma interface unificada para acesso a dados,
sistema de cache e integração com diferentes bancos de dados.
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Union, Optional, Tuple
from pathlib import Path
from functools import partial

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    # Carregar variáveis de ambiente do arquivo .env no diretório raiz do projeto
    dotenv_path = Path(__file__).resolve().parents[3] / '.env'
    load_dotenv(dotenv_path)
    logger = logging.getLogger(__name__)
    logger.info(f"Carregando variáveis de ambiente de: {dotenv_path}")
except ImportError:
    print("Pacote python-dotenv não está instalado. Variáveis de ambiente não serão carregadas do arquivo .env")

# Tentar importar dependências opcionais
try:
    import redis
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
    REDIS_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    REDIS_AVAILABLE = False

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataServiceHub:
    """
    Hub central para todos os serviços de dados da aplicação.
    
    Responsabilidades:
    - Gerenciar conexões com bancos de dados (PostgreSQL, Redis, etc.)
    - Implementar sistema de cache em dois níveis
    - Fornecer interface unificada para todos os serviços de dados
    - Criar e gerenciar o DataProxyAgent para acesso unificado a dados
    - Facilitar comunicação entre diferentes serviços
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o DataServiceHub com as conexões necessárias.
        
        Args:
            config: Configurações para conexões com bancos de dados e cache.
                   Se None, usa variáveis de ambiente.
        """
        self.config = config or self._load_config_from_env()
        
        # Verificar se estamos em modo de desenvolvimento
        self.dev_mode = os.environ.get('DEV_MODE', 'false').lower() == 'true'
        
        # Inicializar conexões
        self.pg_conn = None
        self.redis_client = None
        self.sqlite_conn = None
        
        # Em modo de desenvolvimento, usar SQLite
        if self.dev_mode or not POSTGRES_AVAILABLE:
            self._init_sqlite_connection()
        else:
            # Em modo de produção, usar PostgreSQL e Redis
            self.pg_conn = self._init_postgres_connection()
            self.redis_client = self._init_redis_connection()
        
        # Dicionário para armazenar serviços registrados
        self.services = {}
        
        # Cache L1 (memória local) - mais rápido, capacidade limitada
        self.l1_cache = {}
        
        # Registrar serviços padrão
        self._register_default_services()
        
        # Registrar VectorSearchService
        try:
            from src.tools.vector_tools import QdrantVectorSearchTool
            # Obter a URL do Qdrant das variáveis de ambiente ou usar um valor padrão
            qdrant_url = os.environ.get('QDRANT_URL', 'http://localhost:6333')
            logger.info(f"Conectando ao Qdrant em: {qdrant_url}")
            self.register_service('VectorSearchService', QdrantVectorSearchTool(qdrant_url=qdrant_url))
            logger.info("Serviço VectorSearchService registrado com sucesso")
        except Exception as e:
            logger.warning(f"Não foi possível registrar VectorSearchService: {str(e)}. A funcionalidade de busca vetorial estará indisponível.")
        
        logger.info("DataServiceHub inicializado com sucesso")
    
    def _load_config_from_env(self) -> Dict[str, Any]:
        """
        Carrega configurações a partir de variáveis de ambiente.
        
        Returns:
            Dicionário com configurações.
        """
        # Forçando o uso de localhost para o Redis
        redis_url = "redis://localhost:6379/0"  # Forçando localhost
        redis_host = "localhost"  # Forçando localhost
        redis_port = "6379"
        
        logger.info(f"Carregando configuração do Redis - URL: {redis_url}, Host: {redis_host}, Porta: {redis_port}")
        
        return {
            'postgres': {
                'host': os.environ.get('POSTGRES_HOST', 'localhost'),
                'port': os.environ.get('POSTGRES_PORT', '5433'),
                'user': os.environ.get('POSTGRES_USER', 'postgres'),
                'password': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
                'database': os.environ.get('POSTGRES_DB', 'chatwootai')
            },
            'redis': {
                # Extrair informações da URL do Redis
                'url': redis_url,
                'host': redis_host,
                'port': redis_port,
                'db': os.environ.get('REDIS_DB', '0'),
                'password': os.environ.get('REDIS_PASSWORD', None)
            },
            'cache': {
                'l1_max_size': int(os.environ.get('CACHE_L1_MAX_SIZE', '1000')),
                'l1_ttl': int(os.environ.get('CACHE_L1_TTL', '300')),  # 5 minutos
                'l2_ttl': int(os.environ.get('CACHE_L2_TTL', '3600'))  # 1 hora
            },
            'sqlite': {
                'db_path': os.environ.get('SQLITE_DB_PATH', 'data/chatwootai.db')
            }
        }
    
    def _init_postgres_connection(self):
        """
        Inicializa conexão com PostgreSQL.
        
        Returns:
            Conexão com PostgreSQL.
        """
        try:
            pg_config = self.config['postgres']
            conn = psycopg2.connect(
                host=pg_config['host'],
                port=pg_config['port'],
                user=pg_config['user'],
                password=pg_config['password'],
                database=pg_config['database']
            )
            logger.info(f"Conexão com PostgreSQL estabelecida: {pg_config['host']}:{pg_config['port']}/{pg_config['database']}")
            return conn
        except Exception as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {str(e)}")
            return None
            
    def get_data_proxy_agent(self):
        """
        Cria ou retorna uma instância do DataProxyAgent.
        
        Este método inicializa e configura um DataProxyAgent com as ferramentas
        necessárias para acesso aos dados, incluindo busca vetorial, banco de dados
        e sistema de cache.
        
        Returns:
            DataProxyAgent: Uma instância configurada do DataProxyAgent.
        """
        from src.core.data_proxy_agent import DataProxyAgent
        from src.tools.vector_tools import QdrantVectorSearchTool
        from src.tools.database_tools import PGSearchTool
        from src.tools.cache_tools import TwoLevelCache
        from src.core.memory import MemorySystem
        
        # Obter configurações do ambiente
        qdrant_url = os.environ.get('QDRANT_URL', 'http://localhost:6333')
        qdrant_api_key = os.environ.get('QDRANT_API_KEY', None)
        openai_api_key = os.environ.get('OPENAI_API_KEY', None)
        
        # Log das configurações
        logger.info(f"Inicializando ferramentas com: Qdrant URL={qdrant_url}")
        
        # Construir a string de conexão PostgreSQL
        db_uri = None
        if self.pg_conn:
            pg_config = self.config['postgres']
            db_uri = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
        
        # Inicializa ferramentas para o agente
        vector_tool = QdrantVectorSearchTool(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            collection_name="business_rules",  # Usar uma coleção que sabemos que existe
            openai_api_key=openai_api_key
        )
        
        # Só criar o PGSearchTool se tivermos uma conexão com o PostgreSQL
        if db_uri:
            db_tool = PGSearchTool(
                db_uri=db_uri,
                table_name="business_rules"  # Tabela que sabemos que existe
            )
        else:
            # Ferramenta mock ou simplificada se não tiver PostgreSQL
            from crewai.tools.base_tool import BaseTool
            class MockPGSearchTool(BaseTool):
                def name(self):
                    return "MockPGSearchTool"
                def description(self):
                    return "Uma ferramenta simulada quando PostgreSQL não está disponível"
                def _run(self, query):
                    return "PostgreSQL não disponível neste ambiente"
            db_tool = MockPGSearchTool()
            
        # Criar ferramenta de cache apenas se tiver Redis disponível
        if self.redis_client:
            cache_tool = TwoLevelCache(redis_client=self.redis_client)
        else:
            # Ferramenta mock se não tiver Redis
            class MockCacheTool(BaseTool):
                def name(self):
                    return "MockCacheTool"
                def description(self):
                    return "Uma ferramenta de cache simulada quando Redis não está disponível"
                def _run(self, key, value=None):
                    return "Cache não disponível neste ambiente"
            cache_tool = MockCacheTool()
        memory_system = MemorySystem()
        
        # Inicializa o DataProxyAgent com as ferramentas necessárias
        data_proxy_agent = DataProxyAgent(
            data_service_hub=self,  # Passar a instância atual do hub como parâmetro obrigatório
            memory_system=memory_system,
            role="Data Proxy",
            goal="Fornecer acesso otimizado e consistente aos dados para outros agentes",
            backstory="Sou um agente especializado em busca e transformação de dados, "
                     "utilizando diversas fontes como bancos relacionais, vetoriais, e sistemas de cache.",
            verbose=True,
            allow_delegation=False,
            tools=[vector_tool, db_tool, cache_tool]
        )
        
        logger.info("DataProxyAgent inicializado com sucesso.")
        return data_proxy_agent
    
    def _init_redis_connection(self):
        """
        Inicializa conexão com Redis.
        
        Returns:
            Cliente Redis.
        """
        try:
            redis_config = self.config['redis']
            logger.info(f"Tentando conectar ao Redis com configuração: {redis_config}")
            
            # Verificar novamente as variáveis de ambiente (para debug)
            env_redis_url = os.environ.get('REDIS_URL', 'não definido')
            env_redis_host = os.environ.get('REDIS_HOST', 'não definido')
            env_redis_port = os.environ.get('REDIS_PORT', 'não definido')
            logger.info(f"Variáveis de ambiente Redis - URL: {env_redis_url}, Host: {env_redis_host}, Porta: {env_redis_port}")
            
            # Tenta conectar usando a URL completa do Redis (mais simples e recomendado)
            if 'url' in redis_config and redis_config['url']:
                # A URL já contém todas as informações de conexão (host, porta, senha, db)
                logger.info(f"Conectando ao Redis usando URL: {redis_config['url']}")
                client = redis.from_url(
                    redis_config['url'],
                    decode_responses=True  # Retorna strings em vez de bytes
                )
                logger.info(f"Conexão com Redis estabelecida via URL: {redis_config['url']}")
            else:
                # Fallback para parâmetros separados, caso a URL não esteja disponível
                logger.info(f"Conectando ao Redis usando parâmetros: host={redis_config['host']}, port={redis_config['port']}")
                client = redis.Redis(
                    host=redis_config['host'],
                    port=int(redis_config['port']),
                    db=int(redis_config['db']),
                    password=redis_config['password'],
                    decode_responses=True  # Retorna strings em vez de bytes
                )
                logger.info(f"Conexão com Redis estabelecida: {redis_config['host']}:{redis_config['port']}")
            
            # Testar conexão
            client.ping()
            return client
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            # Em produção, você pode querer retentar ou implementar um fallback
            # Por enquanto, apenas registramos o erro e retornamos None
            return None
    
    def register_service(self, service_name: str, service_instance: Any) -> None:
        """
        Registra um serviço de dados no hub.
        
        Args:
            service_name: Nome do serviço.
            service_instance: Instância do serviço.
        """
        if service_name in self.services:
            logger.warning(f"Serviço '{service_name}' já estava registrado e será substituído")
        
        self.services[service_name] = service_instance
        logger.info(f"Serviço '{service_name}' registrado com sucesso")
    
    def get_service(self, service_name: str) -> Any:
        """
        Obtém um serviço de dados registrado.
        
        Args:
            service_name: Nome do serviço.
            
        Returns:
            Instância do serviço ou None se não encontrado.
        """
        if service_name not in self.services:
            logger.warning(f"Tentativa de acessar serviço não registrado: '{service_name}'")
            return None
        
        return self.services[service_name]
    
    def list_services(self) -> List[str]:
        """
        Retorna a lista de nomes de todos os serviços registrados.
        
        Returns:
            Lista com os nomes dos serviços.
        """
        return list(self.services.keys())
    
    # Métodos de serialização e cache
    
    def _json_encoder(self, obj):
        """
        Encoder personalizado para serializar objetos complexos para JSON.
        
        Args:
            obj: Objeto a ser serializado.
            
        Returns:
            Representação serializável do objeto.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._json_encoder(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._json_encoder(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._json_encoder(obj.__dict__)
        elif obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        else:
            return str(obj)
    
    def serialize_for_json(self, data):
        """
        Serializa dados para JSON, lidando com tipos complexos como datetime.
        
        Args:
            data: Dados a serem serializados.
            
        Returns:
            String JSON.
        """
        try:
            return json.dumps(data, default=self._json_encoder)
        except Exception as e:
            logger.error(f"Erro ao serializar para JSON: {str(e)}")
            # Fallback: tentar converter dicts com valores datetime para strings
            if isinstance(data, dict):
                sanitized = {}
                for k, v in data.items():
                    if isinstance(v, datetime):
                        sanitized[k] = v.isoformat()
                    else:
                        sanitized[k] = v
                return json.dumps(sanitized)
            raise
    
    def deserialize_from_json(self, json_str):
        """
        Deserializa uma string JSON para um objeto Python.
        
        Args:
            json_str: String JSON a ser deserializada.
            
        Returns:
            Objeto Python.
        """
        if not json_str:
            return None
            
        # Se já for bytes, decodificar para string
        if isinstance(json_str, bytes):
            json_str = json_str.decode('utf-8')
            
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Erro ao deserializar JSON: {str(e)}")
            return None
    
    def cache_get(self, key: str, entity_type: str = None) -> Any:
        """
        Obtém valor do cache (primeiro L1, depois L2).
        
        Args:
            key: Chave para buscar.
            entity_type: Tipo da entidade (para namespacing).
            
        Returns:
            Valor do cache ou None se não encontrado.
        """
        # Construir chave completa se entity_type for fornecido
        full_key = f"{entity_type}:{key}" if entity_type else key
        
        # Tentar L1 (memória local)
        if full_key in self.l1_cache:
            logger.debug(f"Cache L1 hit: {full_key}")
            value = self.l1_cache[full_key]
            # Se o valor é uma string JSON, desserializar
            if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                return self.deserialize_from_json(value)
            return value
        
        # Tentar L2 (Redis)
        if self.redis_client:
            try:
                value = self.redis_client.get(full_key)
                if value:
                    logger.debug(f"Cache L2 hit: {full_key}")
                    # Atualizar L1 para futuras requisições
                    self.l1_cache[full_key] = value
                    
                    # Se o valor é bytes, decodificar para string
                    if isinstance(value, bytes):
                        value = value.decode('utf-8')
                        
                    # Se o valor é uma string JSON, desserializar
                    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                        return self.deserialize_from_json(value)
                    return value
            except Exception as e:
                logger.error(f"Erro ao acessar cache L2: {str(e)}")
        
        logger.debug(f"Cache miss: {full_key}")
        return None
    
    def cache_set(self, key: str, value: Any, entity_type: str = None, ttl: int = None) -> bool:
        """
        Armazena valor no cache (L1 e L2).
        
        Args:
            key: Chave para armazenar.
            value: Valor para armazenar.
            entity_type: Tipo da entidade (para namespacing).
            ttl: Tempo de vida em segundos (se None, usa padrão da configuração).
            
        Returns:
            True se armazenado com sucesso, False caso contrário.
        """
        # Construir chave completa se entity_type for fornecido
        full_key = f"{entity_type}:{key}" if entity_type else key
        
        # Armazenar em L1 (memória local)
        self.l1_cache[full_key] = value
        
        # Controlar tamanho do L1
        if len(self.l1_cache) > self.config['cache']['l1_max_size']:
            # Estratégia simples: remover o primeiro item
            # Em uma implementação mais sofisticada, usaríamos LRU
            self.l1_cache.pop(next(iter(self.l1_cache)))
        
        # Armazenar em L2 (Redis)
        if self.redis_client:
            try:
                # Sempre serializar para JSON se não for um tipo primitivo ou se já é uma string JSON
                if not isinstance(value, (str, int, float, bool, bytes, type(None))):
                    # Garantir que temos uma string JSON válida
                    value = self.serialize_for_json(value)
                # Se for uma string, verificar se já não é uma string JSON válida
                elif isinstance(value, str) and not (value.startswith('{') or value.startswith('[')):
                    # Envolver em aspas para tornar JSON válido se não for
                    value = f'"{value}"'
                    
                l2_ttl = ttl or self.config['cache']['l2_ttl']
                self.redis_client.set(full_key, value, ex=l2_ttl)
                logger.debug(f"Valor armazenado no cache para: {full_key} (TTL: {l2_ttl}s)")
                return True
            except Exception as e:
                logger.error(f"Erro ao armazenar em cache L2: {str(e)}")
                return False
        
        return True  # Pelo menos L1 funcionou
    
    def cache_invalidate(self, key: str, entity_type: str = None) -> bool:
        """
        Invalida uma entrada do cache (L1 e L2).
        
        Args:
            key: Chave para invalidar.
            entity_type: Tipo da entidade (para namespacing).
            
        Returns:
            True se invalidado com sucesso, False caso contrário.
        """
        # Construir chave completa se entity_type for fornecido
        full_key = f"{entity_type}:{key}" if entity_type else key
        
        # Remover de L1
        if full_key in self.l1_cache:
            del self.l1_cache[full_key]
        
        # Remover de L2 (Redis) - apenas se não estivermos no modo de desenvolvimento
        if self.redis_client:
            try:
                self.redis_client.delete(full_key)
                logger.debug(f"Cache invalidado para: {full_key}")
                return True
            except Exception as e:
                logger.error(f"Erro ao invalidar cache L2: {str(e)}")
                return False
        
        return True  # Pelo menos L1 foi invalidado
    
    # Métodos para acesso a dados
    
    def _init_sqlite_connection(self):
        """
        Inicializa conexão com SQLite.
        
        Returns:
            Conexão com SQLite.
        """
        try:
            # Garantir que o diretório data existe
            db_path = self.config['sqlite']['db_path']
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Conectar ao SQLite
            self.sqlite_conn = sqlite3.connect(db_path)
            
            # Configurar o SQLite para retornar resultados como dicionários
            self.sqlite_conn.row_factory = lambda cursor, row: {
                column[0]: row[idx] for idx, column in enumerate(cursor.description)
            }
            
            logger.info(f"Conexão com SQLite estabelecida: {db_path}")
            return self.sqlite_conn
        except Exception as e:
            logger.error(f"Erro ao conectar ao SQLite: {str(e)}")
            return None
            
    def execute_query(self, query: str, params: Dict[str, Any] = None, fetch_all: bool = True) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """
        Executa uma consulta SQL no banco de dados.
        
        Args:
            query: Consulta SQL.
            params: Parâmetros para a consulta.
            fetch_all: Se True, retorna todos os resultados; se False, apenas o primeiro.
            
        Returns:
            Resultados da consulta ou None em caso de erro.
        """
        # Decidir qual conexão usar com base na disponibilidade
        if self.sqlite_conn:
            return self._execute_sqlite_query(query, params, fetch_all)
        elif self.pg_conn:
            return self._execute_pg_query(query, params, fetch_all)
        else:
            logger.error("Tentativa de executar consulta sem conexão com banco de dados")
            return None
            
    def _execute_pg_query(self, query: str, params: Dict[str, Any] = None, fetch_all: bool = True):
        """
        Executa uma consulta SQL no PostgreSQL.
        
        Args:
            query: Consulta SQL.
            params: Parâmetros para a consulta.
            fetch_all: Se True, retorna todos os resultados; se False, apenas o primeiro.
            
        Returns:
            Resultados da consulta ou None em caso de erro.
        """
        try:
            # Criar uma nova conexão com autocommit para evitar problemas com transações abortadas
            # Isso é mais seguro para operações pontuais que não requerem transações
            conn = psycopg2.connect(
                host=self.config['postgres']['host'],
                port=self.config['postgres']['port'],
                user=self.config['postgres']['user'],
                password=self.config['postgres']['password'],
                database=self.config['postgres']['database']
            )
            conn.autocommit = True  # Importante para evitar problemas com transações abortadas
            
            # Usar RealDictCursor para retornar dicionários em vez de tuplas
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                
                if query.strip().upper().startswith(('SELECT', 'WITH')):
                    if fetch_all:
                        result = cursor.fetchall()
                    else:
                        result = cursor.fetchone()
                else:
                    # Para operações que não retornam resultados (INSERT, UPDATE, DELETE)
                    result = cursor.rowcount if fetch_all else None
            
            # Fechar conexão temporária
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Erro ao executar consulta PostgreSQL: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return None
            
    def _execute_sqlite_query(self, query: str, params: Dict[str, Any] = None, fetch_all: bool = True):
        """
        Executa uma consulta SQL no SQLite.
        
        Args:
            query: Consulta SQL.
            params: Parâmetros para a consulta.
            fetch_all: Se True, retorna todos os resultados; se False, apenas o primeiro.
            
        Returns:
            Resultados da consulta ou None em caso de erro.
        """
        # Converter query PostgreSQL para SQLite
        query = self._convert_query_to_sqlite(query)
        
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, params or {})
            
            if query.strip().upper().startswith(('SELECT', 'WITH')):
                if fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
                    
                return result
            else:
                self.sqlite_conn.commit()
                return cursor.rowcount if fetch_all else None
        except Exception as e:
            logger.error(f"Erro ao executar consulta SQLite: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            self.sqlite_conn.rollback()
            return None
    
    def _convert_query_to_sqlite(self, query: str) -> str:
        """
        Converte uma consulta PostgreSQL para formato compatível com SQLite.
        """
        # Substituir RETURNING por um comentário (SQLite não suporta)
        if 'RETURNING' in query.upper():
            query = query.replace('RETURNING', '--RETURNING')
            query = query.replace('returning', '--returning')
        
        # Substituir JSONB por TEXT
        query = query.replace('JSONB', 'TEXT')
        
        # Substituir NOW() por DATETIME('now')
        query = query.replace('NOW()', "DATETIME('now')")
        
        return query
    
    def execute_transaction(self, queries: List[Tuple[str, Dict[str, Any]]]) -> bool:
        """
        Executa múltiplas consultas em uma transação.
        
        Args:
            queries: Lista de tuplas (query, params).
            
        Returns:
            True se a transação foi concluída com sucesso, False caso contrário.
        """
        # Verificar qual banco de dados está sendo utilizado
        if self.sqlite_conn:
            return self._execute_sqlite_transaction(queries)
        elif self.pg_conn:
            return self._execute_pg_transaction(queries)
        else:
            logger.error("Tentativa de executar transação sem conexão com banco de dados")
            return False
    
    def _execute_pg_transaction(self, queries: List[Tuple[str, Dict[str, Any]]]) -> bool:
        """
        Executa múltiplas consultas em uma transação usando PostgreSQL.
        
        Args:
            queries: Lista de tuplas (query, params).
            
        Returns:
            True se a transação foi concluída com sucesso, False caso contrário.
        """
        try:
            with self.pg_conn:  # Isso garante commit/rollback automático
                with self.pg_conn.cursor() as cursor:
                    for query, params in queries:
                        cursor.execute(query, params or {})
            
            logger.info(f"Transação PostgreSQL concluída com sucesso ({len(queries)} queries)")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar transação PostgreSQL: {str(e)}")
            # O rollback é automático pelo gerenciador de contexto
            return False
    
    def _execute_sqlite_transaction(self, queries: List[Tuple[str, Dict[str, Any]]]) -> bool:
        """
        Executa múltiplas consultas em uma transação usando SQLite.
        
        Args:
            queries: Lista de tuplas (query, params).
            
        Returns:
            True se a transação foi concluída com sucesso, False caso contrário.
        """
        try:
            # SQLite também suporta gerenciador de contexto para transações
            with self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                for query, params in queries:
                    # Converter query para formato SQLite
                    converted_query = self._convert_query_to_sqlite(query)
                    cursor.execute(converted_query, params or {})
            
            logger.info(f"Transação SQLite concluída com sucesso ({len(queries)} queries)")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar transação SQLite: {str(e)}")
            # O rollback é automático pelo gerenciador de contexto
            return False
    
    def _register_default_services(self):
        """
        Registra os serviços padrão que são carregados automaticamente.
        
        Este método é chamado durante a inicialização do DataServiceHub.
        Nota: Os serviços são auto-registrados quando inicializados via BaseDataService,
        então este método apenas verifica e inicializa os serviços necessários.
        """
        try:
            # Adicionando logs diagnósticos
            logger.info("DIAGNÓSTICO: Iniciando registro de serviços padrão no DataServiceHub")
            
            # Lista de serviços que devem ser carregados
            services_to_register = {
                'ProductDataService': ('product_data_service', 'ProductDataService'),
                'CustomerDataService': ('customer_data_service', 'CustomerDataService'),
                'ConversationContextService': ('conversation_context_service', 'ConversationContextService'),
                'ConversationAnalyticsService': ('conversation_analytics_service', 'ConversationAnalyticsService'),
                'DomainRulesService': ('domain_rules_service', 'DomainRulesService'),
                'VectorSearchService': ('vector_search_service', 'VectorSearchService')
            }
            
            logger.info(f"DIAGNÓSTICO: Serviços a serem registrados: {list(services_to_register.keys())}")
            
            # Verificar quais serviços já estão registrados
            missing_services = {}
            for service_name, details in services_to_register.items():
                # Se o serviço não estiver registrado, adicioná-lo à lista de serviços a registrar
                if service_name not in self.services and service_name.replace('Service', '') not in self.services:
                    missing_services[service_name] = details
            
            # Registrar apenas os serviços não registrados
            for service_name, (module_name, class_name) in missing_services.items():
                try:
                    # Importar dinamicamente usando path relativo ao pacote atual
                    import importlib
                    full_module_name = f"src.services.data.{module_name}"
                    
                    # Log detalhado da tentativa de importação
                    logger.info(f"DIAGNÓSTICO: Tentando importar módulo {full_module_name} para serviço {service_name}")
                    
                    try:
                        module = importlib.import_module(full_module_name)
                        logger.info(f"DIAGNÓSTICO: Módulo {full_module_name} importado com sucesso")
                    except ImportError as ie:
                        logger.error(f"DIAGNÓSTICO: Erro ao importar módulo {full_module_name}: {str(ie)}")
                        raise
                    
                    # Verificar se a classe existe no módulo
                    if hasattr(module, class_name):
                        service_class = getattr(module, class_name)
                        logger.info(f"DIAGNÓSTICO: Classe {class_name} encontrada no módulo {full_module_name}")
                    else:
                        logger.error(f"DIAGNÓSTICO: Classe {class_name} não encontrada no módulo {full_module_name}")
                        raise AttributeError(f"Módulo {full_module_name} não contém a classe {class_name}")
                    
                    # Verificar se a classe herda de BaseDataService
                    from src.services.data.base_data_service import BaseDataService
                    if not issubclass(service_class, BaseDataService):
                        logger.warning(f"DIAGNÓSTICO: A classe {class_name} não herda de BaseDataService")
                    
                    # Instanciar e registrar (o serviço se auto-registrará via BaseDataService)
                    logger.info(f"DIAGNÓSTICO: Tentando instanciar {class_name} para serviço {service_name}")
                    service_instance = service_class(self)
                    
                    # Verificar se o serviço foi registrado corretamente
                    if service_name in self.services or service_name.replace('Service', '') in self.services:
                        logger.info(f"DIAGNÓSTICO: Serviço {service_name} registrado com sucesso!")
                    else:
                        logger.warning(f"DIAGNÓSTICO: Serviço {service_name} criado mas não foi registrado automaticamente!")
                        # Registrar manualmente se não foi feito automaticamente
                        self.register_service(service_name, service_instance)
                    
                    logger.info(f"Serviço {service_name} inicializado")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Não foi possível carregar o serviço {service_name}: {str(e)}")
                except Exception as e:
                    logger.error(f"Erro inesperado ao inicializar {service_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao registrar serviços padrão: {str(e)}")
    
    def close(self) -> None:
        """
        Fecha todas as conexões.
        """
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Conexão PostgreSQL fechada")
        
        if self.redis_client:
            self.redis_client.close()
            logger.info("Conexão Redis fechada")
            
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("Conexão SQLite fechada")


# Exemplo de uso:
if __name__ == "__main__":
    # Este código só é executado quando o arquivo é executado diretamente
    # É útil para testes rápidos
    
    # Criar instância do hub
    hub = DataServiceHub()
    
    # Testar cache
    hub.cache_set("test_key", "test_value", "test_entity")
    value = hub.cache_get("test_key", "test_entity")
    print(f"Valor recuperado do cache: {value}")
    
    # Testar consulta SQL
    result = hub.execute_query("SELECT 1 as test")
    print(f"Resultado da consulta: {result}")
    
    # Fechar conexões
    hub.close()
