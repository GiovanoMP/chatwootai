"""
Serviço para gerenciar o contexto das conversas usando a simulação do CRM.

Este serviço se comunica com as tabelas SQL que simulam o módulo CRM do Odoo
para armazenar e recuperar o contexto das conversas.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

from src.core.domain import DomainManager

logger = logging.getLogger(__name__)

class CRMContextService:
    """
    Serviço para gerenciar o contexto das conversas usando a simulação do CRM.
    
    Esta classe é responsável por:
    1. Buscar ou criar clientes no CRM simulado
    2. Armazenar threads de conversas vinculadas aos clientes
    3. Recuperar o histórico de conversas dos clientes
    4. Gerenciar o contexto das conversas para os agentes de IA
    """
    
    def __init__(self, db_connection=None, redis_client=None, domain_manager=None):
        """
        Inicializa o serviço de contexto do CRM.
        
        Args:
            db_connection: Conexão com o banco de dados PostgreSQL
            redis_client: Cliente do Redis (opcional, para cache)
            domain_manager: Gerenciador de domínios de negócio
        """
        self.db_connection = db_connection
        self.redis_client = redis_client
        self.domain_manager = domain_manager or DomainManager()
        self.cache_ttl = 3600  # 1 hora em segundos
        
        # Inicializa a conexão com o banco de dados se não foi fornecida
        if not self.db_connection:
            self._initialize_db_connection()
    
    def _initialize_db_connection(self):
        """
        Inicializa a conexão com o banco de dados PostgreSQL.
        """
        try:
            # Obtém as credenciais do banco de dados das variáveis de ambiente
            import os
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DATABASE", "chatwoot")
            db_user = os.getenv("POSTGRES_USERNAME", "postgres")
            db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
            
            # Cria a conexão
            self.db_connection = psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password
            )
            
            logger.info("Conexão com o banco de dados PostgreSQL inicializada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar a conexão com o banco de dados: {str(e)}")
            raise
    
    def get_or_create_customer(self, contact_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Busca um cliente no CRM ou cria um novo lead se não existir.
        
        Args:
            contact_info: Informações do contato (email, telefone, nome, etc.)
            
        Returns:
            Dict[str, Any]: Informações do cliente/lead
        """
        logger.info(f"Buscando cliente com informações: {contact_info}")
        
        # Extrai as informações do contato
        email = contact_info.get('email')
        phone = contact_info.get('phone')
        name = contact_info.get('name', 'Novo Contato')
        
        # Verifica se temos pelo menos email ou telefone para buscar
        if not email and not phone:
            logger.warning("Nenhum critério de busca fornecido (email ou telefone)")
            # Cria um novo lead mesmo sem email ou telefone
            return self._create_customer({
                'name': name,
                'type': 'lead',
                'status': 'new',
                'source': 'chatwoot'
            })
        
        # Busca o cliente pelo email ou telefone
        customer = self._search_customer(email, phone)
        
        # Se não encontrou, cria um novo lead
        if not customer:
            logger.info(f"Cliente não encontrado. Criando novo lead.")
            customer = self._create_customer({
                'name': name,
                'email': email,
                'phone': phone,
                'type': 'lead',
                'status': 'new',
                'source': 'chatwoot'
            })
        
        return customer
    
    def _search_customer(self, email=None, phone=None) -> Optional[Dict[str, Any]]:
        """
        Busca um cliente pelo email ou telefone.
        
        Args:
            email: Email do cliente (opcional)
            phone: Telefone do cliente (opcional)
            
        Returns:
            Optional[Dict[str, Any]]: Cliente encontrado ou None
        """
        try:
            # Verifica se temos pelo menos email ou telefone para buscar
            if not email and not phone:
                return None
            
            # Constrói a query SQL
            query = "SELECT * FROM crm_customers WHERE "
            params = []
            
            if email:
                query += "email = %s"
                params.append(email)
                
                if phone:
                    query += " OR phone = %s"
                    params.append(phone)
            elif phone:
                query += "phone = %s"
                params.append(phone)
            
            # Executa a query
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                if result:
                    # Converte o resultado para um dicionário
                    return dict(result)
                
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar cliente: {str(e)}")
            return None
    
    def _create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo cliente/lead no CRM.
        
        Args:
            customer_data: Dados do cliente/lead
            
        Returns:
            Dict[str, Any]: Cliente/lead criado
        """
        try:
            # Extrai os campos do dicionário
            name = customer_data.get('name', 'Novo Contato')
            email = customer_data.get('email')
            phone = customer_data.get('phone')
            customer_type = customer_data.get('type', 'lead')
            status = customer_data.get('status', 'new')
            source = customer_data.get('source', 'chatwoot')
            metadata = customer_data.get('metadata', {})
            
            # Converte o metadata para JSON se for um dicionário
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata)
            
            # Constrói a query SQL
            query = """
                INSERT INTO crm_customers (name, email, phone, type, status, source, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            
            # Executa a query
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (name, email, phone, customer_type, status, source, metadata))
                self.db_connection.commit()
                result = cursor.fetchone()
                
                # Converte o resultado para um dicionário
                return dict(result)
                
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {str(e)}")
            self.db_connection.rollback()
            raise
    
    def store_conversation_thread(self, customer_id: int, conversation_id: str, 
                                 messages: List[Dict[str, Any]], 
                                 domain_id: str = None) -> bool:
        """
        Armazena uma thread de conversa vinculada ao cliente.
        
        Args:
            customer_id: ID do cliente no CRM
            conversation_id: ID da conversa no Chatwoot
            messages: Lista de mensagens da conversa
            domain_id: ID do domínio de negócio (opcional)
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        logger.info(f"Armazenando thread de conversa para o cliente {customer_id}, conversa {conversation_id}")
        
        try:
            # Primeiro, verifica se a thread já existe
            thread = self._get_thread_by_conversation_id(conversation_id)
            
            # Se não existir, cria uma nova thread
            if not thread:
                # Cria a thread
                thread = self._create_conversation_thread(customer_id, conversation_id, domain_id)
            
            # Armazena as mensagens
            for message in messages:
                self._store_conversation_message(
                    thread_id=thread['id'],
                    sender_type=message.get('role', 'system'),
                    content=message.get('content', ''),
                    metadata=message.get('metadata', {})
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar thread de conversa: {str(e)}")
            self.db_connection.rollback()
            return False
    
    def _get_thread_by_conversation_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma thread de conversa pelo ID da conversa.
        
        Args:
            conversation_id: ID da conversa no Chatwoot
            
        Returns:
            Optional[Dict[str, Any]]: Thread encontrada ou None
        """
        try:
            # Constrói a query SQL
            query = "SELECT * FROM crm_conversation_threads WHERE conversation_id = %s"
            
            # Executa a query
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (conversation_id,))
                result = cursor.fetchone()
                
                if result:
                    # Converte o resultado para um dicionário
                    return dict(result)
                
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar thread de conversa: {str(e)}")
            return None
    
    def _create_conversation_thread(self, customer_id: int, conversation_id: str, 
                                  domain_id: str = None) -> Dict[str, Any]:
        """
        Cria uma nova thread de conversa.
        
        Args:
            customer_id: ID do cliente no CRM
            conversation_id: ID da conversa no Chatwoot
            domain_id: ID do domínio de negócio (opcional)
            
        Returns:
            Dict[str, Any]: Thread criada
        """
        try:
            # Prepara o metadata
            metadata = {
                'created_at': datetime.now().isoformat()
            }
            
            if domain_id:
                metadata['domain_id'] = domain_id
            
            # Converte o metadata para JSON
            metadata_json = json.dumps(metadata)
            
            # Constrói a query SQL
            query = """
                INSERT INTO crm_conversation_threads (customer_id, conversation_id, domain_id, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """
            
            # Executa a query
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (customer_id, conversation_id, domain_id, metadata_json))
                self.db_connection.commit()
                result = cursor.fetchone()
                
                # Converte o resultado para um dicionário
                return dict(result)
                
        except Exception as e:
            logger.error(f"Erro ao criar thread de conversa: {str(e)}")
            self.db_connection.rollback()
            raise
    
    def _store_conversation_message(self, thread_id: int, sender_type: str, 
                                  content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Armazena uma mensagem de conversa.
        
        Args:
            thread_id: ID da thread de conversa
            sender_type: Tipo do remetente ('customer', 'agent', 'system')
            content: Conteúdo da mensagem
            metadata: Metadados da mensagem (opcional)
            
        Returns:
            Dict[str, Any]: Mensagem armazenada
        """
        try:
            # Normaliza o tipo do remetente
            if sender_type not in ['customer', 'agent', 'system']:
                if sender_type == 'user':
                    sender_type = 'customer'
                elif sender_type == 'assistant':
                    sender_type = 'agent'
                else:
                    sender_type = 'system'
            
            # Prepara o metadata
            if metadata is None:
                metadata = {}
            
            # Converte o metadata para JSON
            metadata_json = json.dumps(metadata)
            
            # Constrói a query SQL
            query = """
                INSERT INTO crm_conversation_messages (thread_id, sender_type, content, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """
            
            # Executa a query
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (thread_id, sender_type, content, metadata_json))
                self.db_connection.commit()
                result = cursor.fetchone()
                
                # Converte o resultado para um dicionário
                return dict(result)
                
        except Exception as e:
            logger.error(f"Erro ao armazenar mensagem de conversa: {str(e)}")
            self.db_connection.rollback()
            raise
    
    def get_customer_conversation_history(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera o histórico de conversas do cliente.
        
        Args:
            customer_id: ID do cliente no CRM
            limit: Número máximo de threads a serem retornadas
            
        Returns:
            List[Dict[str, Any]]: Lista de threads de conversa com suas mensagens
        """
        logger.info(f"Recuperando histórico de conversas para o cliente {customer_id}")
        
        # Verifica se tem no cache do Redis
        if self.redis_client:
            cache_key = f"conversation_history:{customer_id}"
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Histórico encontrado no cache para o cliente {customer_id}")
                return json.loads(cached_data)
        
        try:
            # Busca as threads do cliente
            threads = self._get_customer_threads(customer_id, limit)
            
            # Para cada thread, busca as mensagens
            for thread in threads:
                thread['messages'] = self._get_thread_messages(thread['id'])
            
            # Atualiza o cache se tiver Redis
            if self.redis_client and threads:
                cache_key = f"conversation_history:{customer_id}"
                self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(threads))
            
            return threads
            
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico de conversas: {str(e)}")
            return []
    
    def _get_customer_threads(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca as threads de conversa de um cliente.
        
        Args:
            customer_id: ID do cliente no CRM
            limit: Número máximo de threads a serem retornadas
            
        Returns:
            List[Dict[str, Any]]: Lista de threads de conversa
        """
        try:
            # Constrói a query SQL
            query = """
                SELECT * FROM crm_conversation_threads
                WHERE customer_id = %s
                ORDER BY updated_at DESC
                LIMIT %s
            """
            
            # Executa a query
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (customer_id, limit))
                results = cursor.fetchall()
                
                # Converte os resultados para uma lista de dicionários
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Erro ao buscar threads de conversa: {str(e)}")
            return []
    
    def _get_thread_messages(self, thread_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca as mensagens de uma thread de conversa.
        
        Args:
            thread_id: ID da thread de conversa
            limit: Número máximo de mensagens a serem retornadas
            
        Returns:
            List[Dict[str, Any]]: Lista de mensagens
        """
        try:
            # Constrói a query SQL
            query = """
                SELECT * FROM crm_conversation_messages
                WHERE thread_id = %s
                ORDER BY created_at ASC
                LIMIT %s
            """
            
            # Executa a query
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (thread_id, limit))
                results = cursor.fetchall()
                
                # Converte os resultados para uma lista de dicionários
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens da thread: {str(e)}")
            return []
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Recupera o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa no Chatwoot
            
        Returns:
            Dict[str, Any]: Contexto da conversa
        """
        logger.info(f"Recuperando contexto da conversa {conversation_id}")
        
        # Verifica se tem no cache do Redis
        if self.redis_client:
            cache_key = f"conversation_context:{conversation_id}"
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Contexto encontrado no cache para a conversa {conversation_id}")
                return json.loads(cached_data)
        
        try:
            # Constrói a query SQL
            query = "SELECT * FROM crm_conversation_contexts WHERE conversation_id = %s"
            
            # Executa a query
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (conversation_id,))
                result = cursor.fetchone()
                
                if result:
                    # Converte o resultado para um dicionário
                    context = dict(result)
                    
                    # Atualiza o cache se tiver Redis
                    if self.redis_client:
                        cache_key = f"conversation_context:{conversation_id}"
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(context))
                    
                    return context
                
                return {}
                
        except Exception as e:
            logger.error(f"Erro ao recuperar contexto da conversa: {str(e)}")
            return {}
    
    def update_conversation_context(self, conversation_id: str, 
                                  customer_id: int, 
                                  context_data: Dict[str, Any]) -> bool:
        """
        Atualiza o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa no Chatwoot
            customer_id: ID do cliente no CRM
            context_data: Dados de contexto a serem atualizados
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        logger.info(f"Atualizando contexto da conversa {conversation_id}")
        
        try:
            # Verifica se o contexto já existe
            existing_context = self.get_conversation_context(conversation_id)
            
            if existing_context:
                # Atualiza o contexto existente
                # Mescla os dados de contexto existentes com os novos
                merged_context = existing_context.get('context_data', {})
                if isinstance(merged_context, str):
                    merged_context = json.loads(merged_context)
                
                merged_context.update(context_data)
                
                # Converte o contexto mesclado para JSON
                context_json = json.dumps(merged_context)
                
                # Constrói a query SQL
                query = """
                    UPDATE crm_conversation_contexts
                    SET context_data = %s, updated_at = NOW()
                    WHERE conversation_id = %s
                    RETURNING *
                """
                
                # Executa a query
                with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (context_json, conversation_id))
                    self.db_connection.commit()
                    result = cursor.fetchone()
                    
                    # Atualiza o cache se tiver Redis
                    if self.redis_client and result:
                        cache_key = f"conversation_context:{conversation_id}"
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(dict(result)))
                    
                    return True
            else:
                # Cria um novo contexto
                # Obtém o domínio ativo
                domain_id = self.domain_manager.active_domain_name if self.domain_manager else None
                
                # Converte o contexto para JSON
                context_json = json.dumps(context_data)
                
                # Constrói a query SQL
                query = """
                    INSERT INTO crm_conversation_contexts 
                    (conversation_id, customer_id, context_data, domain_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                """
                
                # Executa a query
                with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (conversation_id, customer_id, context_json, domain_id))
                    self.db_connection.commit()
                    result = cursor.fetchone()
                    
                    # Atualiza o cache se tiver Redis
                    if self.redis_client and result:
                        cache_key = f"conversation_context:{conversation_id}"
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(dict(result)))
                    
                    return True
                
        except Exception as e:
            logger.error(f"Erro ao atualizar contexto da conversa: {str(e)}")
            self.db_connection.rollback()
            return False
