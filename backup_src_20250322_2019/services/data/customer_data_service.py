"""
CustomerDataService - Serviço para acesso e gerenciamento de dados de clientes.

Este serviço implementa funcionalidades específicas para clientes,
incluindo gerenciamento de perfis, histórico de interações, preferências
e endereços.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Union, Optional

from .base_data_service import BaseDataService

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerDataService(BaseDataService):
    """
    Serviço de dados especializado em clientes.
    
    Implementa operações específicas para clientes, incluindo:
    - Gerenciamento de perfis
    - Histórico de interações
    - Preferências personalizadas
    - Endereços de entrega
    """
    
    def __init__(self, data_service_hub):
        """
        Inicializa o serviço de dados de clientes.
        
        Args:
            data_service_hub: Instância do DataServiceHub.
        """
        super().__init__(data_service_hub)
        logger.info("CustomerDataService inicializado")
    
    def get_entity_type(self) -> str:
        """
        Retorna o tipo de entidade gerenciada por este serviço.
        
        Returns:
            String representando o tipo de entidade.
        """
        return "customers"
    
    def get_full_profile(self, customer_id: int) -> Dict[str, Any]:
        """
        Obtém o perfil completo de um cliente, incluindo dados básicos,
        preferências, endereços e estatísticas de interação.
        
        Args:
            customer_id: ID do cliente.
            
        Returns:
            Perfil completo do cliente.
        """
        # Obter dados básicos do cliente
        customer = self.get_by_id(customer_id)
        
        if not customer:
            logger.warning(f"Cliente não encontrado: {customer_id}")
            return {}
        
        # Obter preferências
        preferences = self.get_preferences(customer_id)
        
        # Obter endereços
        addresses = self.get_addresses(customer_id)
        
        # Obter estatísticas de interação
        interaction_stats = self.get_interaction_statistics(customer_id)
        
        # Obter histórico de compras (resumido)
        purchase_history = self.get_purchase_history_summary(customer_id)
        
        # Combinar tudo em um perfil completo
        full_profile = {
            **customer,
            "preferences": preferences,
            "addresses": addresses,
            "interaction_stats": interaction_stats,
            "purchase_history": purchase_history
        }
        
        return full_profile
    
    def get_preferences(self, customer_id: int) -> Dict[str, Any]:
        """
        Obtém as preferências de um cliente.
        
        Args:
            customer_id: ID do cliente.
            
        Returns:
            Preferências do cliente.
        """
        query = """
            SELECT preference_key, preference_value
            FROM customer_preferences
            WHERE customer_id = %(customer_id)s
        """
        
        params = {"customer_id": customer_id}
        
        results = self.hub.execute_query(query, params)
        
        if not results:
            return {}
        
        # Converter para dicionário
        preferences = {}
        for pref in results:
            # Tentar converter valores JSON
            try:
                value = json.loads(pref['preference_value'])
            except (json.JSONDecodeError, TypeError):
                value = pref['preference_value']
                
            preferences[pref['preference_key']] = value
        
        return preferences
    
    def set_preference(self, customer_id: int, key: str, value: Any) -> bool:
        """
        Define ou atualiza uma preferência de cliente.
        
        Args:
            customer_id: ID do cliente.
            key: Chave da preferência.
            value: Valor da preferência.
            
        Returns:
            True se a operação foi bem-sucedida, False caso contrário.
        """
        # Converter valor para JSON se não for string
        if not isinstance(value, str):
            value = json.dumps(value)
        
        # Verificar se a preferência já existe
        query_check = """
            SELECT id FROM customer_preferences
            WHERE customer_id = %(customer_id)s AND preference_key = %(key)s
        """
        
        params_check = {
            "customer_id": customer_id,
            "key": key
        }
        
        existing = self.hub.execute_query(query_check, params_check, fetch_all=False)
        
        if existing:
            # Atualizar preferência existente
            query = """
                UPDATE customer_preferences
                SET preference_value = %(value)s, updated_at = NOW()
                WHERE customer_id = %(customer_id)s AND preference_key = %(key)s
                RETURNING id
            """
        else:
            # Inserir nova preferência
            query = """
                INSERT INTO customer_preferences
                (customer_id, preference_key, preference_value, created_at, updated_at)
                VALUES (%(customer_id)s, %(key)s, %(value)s, NOW(), NOW())
                RETURNING id
            """
        
        params = {
            "customer_id": customer_id,
            "key": key,
            "value": value
        }
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        # Invalidar cache do cliente
        self.hub.cache_invalidate(str(customer_id), self.get_entity_type())
        
        return result is not None
    
    def get_addresses(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        Obtém os endereços de um cliente.
        
        Args:
            customer_id: ID do cliente.
            
        Returns:
            Lista de endereços do cliente.
        """
        query = """
            SELECT * FROM customer_addresses
            WHERE customer_id = %(customer_id)s
            ORDER BY is_default DESC, created_at DESC
        """
        
        params = {"customer_id": customer_id}
        
        return self.hub.execute_query(query, params) or []
    
    def add_address(self, customer_id: int, address_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Adiciona um novo endereço para o cliente.
        
        Args:
            customer_id: ID do cliente.
            address_data: Dados do endereço.
            
        Returns:
            Endereço adicionado ou None em caso de erro.
        """
        # Adicionar customer_id aos dados
        data = dict(address_data)
        data['customer_id'] = customer_id
        
        # Verificar se deve ser o endereço padrão
        is_default = data.get('is_default', False)
        
        # Se for o padrão, remover o padrão anterior
        if is_default:
            update_query = """
                UPDATE customer_addresses
                SET is_default = FALSE
                WHERE customer_id = %(customer_id)s
            """
            
            update_params = {"customer_id": customer_id}
            
            self.hub.execute_query(update_query, update_params)
        
        # Inserir novo endereço
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({key})s" for key in data.keys()])
        
        query = f"""
            INSERT INTO customer_addresses ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        
        result = self.hub.execute_query(query, data, fetch_all=False)
        
        # Invalidar cache do cliente
        self.hub.cache_invalidate(str(customer_id), self.get_entity_type())
        
        return result
    
    def update_address(self, address_id: int, address_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Atualiza um endereço existente.
        
        Args:
            address_id: ID do endereço.
            address_data: Dados do endereço para atualizar.
            
        Returns:
            Endereço atualizado ou None em caso de erro.
        """
        # Verificar se o endereço existe
        check_query = "SELECT customer_id, is_default FROM customer_addresses WHERE id = %(address_id)s"
        existing = self.hub.execute_query(check_query, {"address_id": address_id}, fetch_all=False)
        
        if not existing:
            logger.warning(f"Endereço não encontrado: {address_id}")
            return None
        
        customer_id = existing['customer_id']
        
        # Verificar se deve ser o endereço padrão
        is_default = address_data.get('is_default', False)
        
        # Se for o padrão, remover o padrão anterior
        if is_default and not existing.get('is_default', False):
            update_query = """
                UPDATE customer_addresses
                SET is_default = FALSE
                WHERE customer_id = %(customer_id)s
            """
            
            update_params = {"customer_id": customer_id}
            
            self.hub.execute_query(update_query, update_params)
        
        # Construir SET clause
        set_clauses = [f"{key} = %({key})s" for key in address_data.keys()]
        set_clause = ", ".join(set_clauses)
        
        # Adicionar updated_at
        set_clause += ", updated_at = NOW()"
        
        # Adicionar ID aos parâmetros
        params = dict(address_data)
        params['address_id'] = address_id
        
        query = f"""
            UPDATE customer_addresses
            SET {set_clause}
            WHERE id = %(address_id)s
            RETURNING *
        """
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        # Invalidar cache do cliente
        self.hub.cache_invalidate(str(customer_id), self.get_entity_type())
        
        return result
    
    def delete_address(self, address_id: int) -> bool:
        """
        Exclui um endereço.
        
        Args:
            address_id: ID do endereço.
            
        Returns:
            True se excluído com sucesso, False caso contrário.
        """
        # Obter customer_id antes de excluir (para invalidação de cache)
        check_query = "SELECT customer_id FROM customer_addresses WHERE id = %(address_id)s"
        existing = self.hub.execute_query(check_query, {"address_id": address_id}, fetch_all=False)
        
        if not existing:
            logger.warning(f"Endereço não encontrado: {address_id}")
            return False
        
        customer_id = existing['customer_id']
        
        query = """
            DELETE FROM customer_addresses
            WHERE id = %(address_id)s
            RETURNING id
        """
        
        params = {"address_id": address_id}
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        # Invalidar cache do cliente
        if result:
            self.hub.cache_invalidate(str(customer_id), self.get_entity_type())
        
        return result is not None
    
    def get_interaction_statistics(self, customer_id: int) -> Dict[str, Any]:
        """
        Obtém estatísticas de interação do cliente.
        
        Args:
            customer_id: ID do cliente.
            
        Returns:
            Estatísticas de interação.
        """
        query = """
            SELECT 
                COUNT(*) as total_interactions,
                COUNT(DISTINCT conversation_id) as total_conversations,
                MAX(created_at) as last_interaction,
                AVG(duration) as avg_duration
            FROM customer_interactions
            WHERE customer_id = %(customer_id)s
        """
        
        params = {"customer_id": customer_id}
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        if not result:
            return {
                "total_interactions": 0,
                "total_conversations": 0,
                "last_interaction": None,
                "avg_duration": 0
            }
        
        return result
    
    def record_interaction(self, customer_id: int, interaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Registra uma nova interação do cliente.
        
        Args:
            customer_id: ID do cliente.
            interaction_data: Dados da interação.
            
        Returns:
            Interação registrada ou None em caso de erro.
        """
        # Adicionar customer_id aos dados
        data = dict(interaction_data)
        data['customer_id'] = customer_id
        
        # Adicionar timestamp se não fornecido
        if 'created_at' not in data:
            data['created_at'] = datetime.now().isoformat()
        
        # Inserir interação
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({key})s" for key in data.keys()])
        
        query = f"""
            INSERT INTO customer_interactions ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        
        result = self.hub.execute_query(query, data, fetch_all=False)
        
        # Invalidar cache do cliente
        self.hub.cache_invalidate(str(customer_id), self.get_entity_type())
        
        return result
    
    def get_purchase_history_summary(self, customer_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém um resumo do histórico de compras do cliente.
        
        Args:
            customer_id: ID do cliente.
            limit: Número máximo de compras recentes.
            
        Returns:
            Resumo do histórico de compras.
        """
        query = """
            SELECT 
                o.id as order_id,
                o.order_date,
                o.status,
                o.total_amount,
                COUNT(oi.id) as total_items,
                STRING_AGG(p.name, ', ' ORDER BY oi.id LIMIT 3) as product_summary
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.customer_id = %(customer_id)s
            GROUP BY o.id, o.order_date, o.status, o.total_amount
            ORDER BY o.order_date DESC
            LIMIT %(limit)s
        """
        
        params = {
            "customer_id": customer_id,
            "limit": limit
        }
        
        return self.hub.execute_query(query, params) or []
    
    def get_customer_by_identifier(self, identifier_type: str, identifier_value: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um cliente por um identificador alternativo (email, telefone, etc).
        
        Args:
            identifier_type: Tipo de identificador (email, phone, etc).
            identifier_value: Valor do identificador.
            
        Returns:
            Dados do cliente ou None se não encontrado.
        """
        # Mapear tipos de identificador para colunas da tabela
        identifier_map = {
            "email": "email",
            "phone": "phone",
            "external_id": "external_id",
            "username": "username"
        }
        
        if identifier_type not in identifier_map:
            logger.warning(f"Tipo de identificador inválido: {identifier_type}")
            return None
        
        column = identifier_map[identifier_type]
        
        query = f"""
            SELECT * FROM customers
            WHERE {column} = %(value)s
        """
        
        params = {"value": identifier_value}
        
        return self.hub.execute_query(query, params, fetch_all=False)
    
    def get_customer_segments(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        Obtém os segmentos de cliente aos quais o cliente pertence.
        
        Args:
            customer_id: ID do cliente.
            
        Returns:
            Lista de segmentos do cliente.
        """
        query = """
            SELECT s.*
            FROM customer_segments cs
            JOIN segments s ON cs.segment_id = s.id
            WHERE cs.customer_id = %(customer_id)s
        """
        
        params = {"customer_id": customer_id}
        
        return self.hub.execute_query(query, params) or []
