"""
Serviço de contexto para gerenciar o contexto das conversas usando o Odoo CRM.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

from src.core.erp.odoo_client import OdooClient

logger = logging.getLogger(__name__)

class OdooCRMContextService:
    """
    Serviço para gerenciar o contexto das conversas usando o Odoo CRM.
    
    Esta classe é responsável por:
    1. Buscar ou criar clientes no Odoo CRM
    2. Armazenar threads de conversas vinculadas aos clientes
    3. Recuperar o histórico de conversas dos clientes
    """
    
    def __init__(self, odoo_client: OdooClient = None, redis_client = None):
        """
        Inicializa o serviço de contexto do Odoo CRM.
        
        Args:
            odoo_client: Cliente do Odoo
            redis_client: Cliente do Redis (opcional, para cache)
        """
        self.odoo_client = odoo_client or OdooClient()
        self.redis_client = redis_client
        self.cache_ttl = 3600  # 1 hora em segundos
    
    def get_or_create_customer(self, contact_info: Dict[str, Any], domain_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Busca um cliente no Odoo CRM ou cria um novo lead se não existir.
        Adapta o comportamento com base no domínio de negócio atual.
        
        Args:
            contact_info: Informações do contato (email, telefone, nome, etc.)
            domain_context: Contexto do domínio de negócio (opcional)
            
        Returns:
            Dict[str, Any]: Informações do cliente/lead
        """
        logger.info(f"Buscando cliente com informações: {contact_info} para domínio: {domain_context}")
        
        # Tenta buscar o cliente pelo email ou telefone
        customer = self.odoo_client.search_customer(
            email=contact_info.get('email'),
            phone=contact_info.get('phone')
        )
        
        if not customer:
            logger.info(f"Cliente não encontrado. Criando novo lead para domínio: {domain_context}")
            
            # Prepara os dados do lead com base no domínio de negócio
            lead_data = {
                'name': contact_info.get('name', 'Novo Contato'),
                'email': contact_info.get('email'),
                'phone': contact_info.get('phone'),
                'source': 'chatwoot',
                'description': 'Contato iniciado via chat'
            }
            
            # Adiciona informações específicas do domínio, se disponível
            if domain_context:
                domain_type = domain_context.get('type', '')
                
                # Adapta o lead com base no tipo de domínio
                if domain_type == 'cosmetics':
                    lead_data['description'] = 'Contato iniciado via chat - Cliente de Cosméticos'
                    lead_data['interest_category'] = 'beauty'
                elif domain_type == 'health':
                    lead_data['description'] = 'Contato iniciado via chat - Cliente de Saúde'
                    lead_data['interest_category'] = 'health'
                elif domain_type == 'retail':
                    lead_data['description'] = 'Contato iniciado via chat - Cliente de Varejo'
                    lead_data['interest_category'] = 'retail'
                
                # Adiciona tags específicas do domínio
                if 'tags' in domain_context:
                    lead_data['tags'] = domain_context['tags']
            
            # Criar novo lead
            customer = self.odoo_client.create_lead(lead_data)
            
        return customer
    
    def store_conversation(self, customer_id: int, conversation: Dict[str, Any]) -> bool:
        """
        Armazena uma conversa individual no histórico do cliente.
        
        Args:
            customer_id: ID do cliente no Odoo
            conversation: Dados da conversa (mensagem, resposta, timestamp)
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        logger.info(f"Armazenando conversa para cliente {customer_id}")
        
        try:
            # Armazena a conversa no Odoo
            self.odoo_client.store_conversation(
                customer_id=customer_id,
                message=conversation.get('message', ''),
                response=conversation.get('response', ''),
                timestamp=conversation.get('timestamp', datetime.now().isoformat())
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar conversa: {str(e)}")
            return False
    
    def store_conversation_thread(self, customer_id: int, conversation_id: str, 
                                 messages: List[Dict[str, Any]], 
                                 domain_id: str = None) -> bool:
        """
        Armazena uma thread de conversa vinculada ao cliente.
        
        Args:
            customer_id: ID do cliente no Odoo
            conversation_id: ID da conversa no Chatwoot
            messages: Lista de mensagens da conversa
            domain_id: ID do domínio de negócio (opcional)
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        logger.info(f"Armazenando thread de conversa para o cliente {customer_id}, conversa {conversation_id}")
        
        thread = {
            'customer_id': customer_id,
            'conversation_id': conversation_id,
            'messages': messages,
            'timestamp': datetime.now().isoformat(),
            'domain_id': domain_id
        }
        
        # Armazena a thread no Odoo
        result = self.odoo_client.create_conversation_thread(thread)
        
        # Se tiver Redis, atualiza o cache
        if self.redis_client:
            cache_key = f"conversation_thread:{customer_id}:{conversation_id}"
            self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(thread))
        
        return result
    
    def get_customer_conversation_history(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera o histórico de conversas do cliente.
        
        Args:
            customer_id: ID do cliente no Odoo
            limit: Número máximo de threads a serem retornadas
            
        Returns:
            List[Dict[str, Any]]: Lista de threads de conversa
        """
        logger.info(f"Recuperando histórico de conversas para o cliente {customer_id}")
        
        # Verifica se tem no cache do Redis
        if self.redis_client:
            cache_key = f"conversation_history:{customer_id}"
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Histórico encontrado no cache para o cliente {customer_id}")
                return json.loads(cached_data)
        
        # Busca no Odoo
        threads = self.odoo_client.get_conversation_threads(customer_id, limit=limit)
        
        # Atualiza o cache se tiver Redis
        if self.redis_client and threads:
            cache_key = f"conversation_history:{customer_id}"
            self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(threads))
        
        return threads
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Recupera o contexto completo de uma conversa.
        
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
        
        # Busca no Odoo
        context = self.odoo_client.get_conversation_context(conversation_id)
        
        # Atualiza o cache se tiver Redis
        if self.redis_client and context:
            cache_key = f"conversation_context:{conversation_id}"
            self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(context))
        
        return context
    
    def update_conversation_context(self, conversation_id: str, 
                                  customer_id: int, 
                                  context_data: Dict[str, Any]) -> bool:
        """
        Atualiza o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa no Chatwoot
            customer_id: ID do cliente no Odoo
            context_data: Dados de contexto a serem atualizados
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        logger.info(f"Atualizando contexto da conversa {conversation_id}")
        
        # Adiciona timestamp
        context_data['updated_at'] = datetime.now().isoformat()
        
        # Atualiza no Odoo
        result = self.odoo_client.update_conversation_context(
            conversation_id=conversation_id,
            customer_id=customer_id,
            context_data=context_data
        )
        
        # Atualiza o cache se tiver Redis
        if self.redis_client:
            cache_key = f"conversation_context:{conversation_id}"
            # Obtém o contexto atual do cache ou do Odoo
            current_context = self.get_conversation_context(conversation_id) or {}
            # Atualiza com os novos dados
            current_context.update(context_data)
            # Salva no cache
            self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(current_context))
        
        return result
