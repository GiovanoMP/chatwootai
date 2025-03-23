"""
BaseDataService - Classe base para todos os serviços de dados.

Este módulo define a interface e funcionalidades comuns que todos os
serviços de dados específicos devem implementar ou herdar.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseDataService(ABC):
    """
    Classe base abstrata para todos os serviços de dados.
    
    Implementa funcionalidades comuns e define a interface
    que todos os serviços de dados devem seguir.
    """
    
    def __init__(self, data_service_hub):
        """
        Inicializa o serviço de dados com uma referência ao hub central.
        
        Args:
            data_service_hub: Instância do DataServiceHub.
        """
        self.hub = data_service_hub
        self.service_name = self.__class__.__name__
        
        # Registrar automaticamente no hub
        self.hub.register_service(self.service_name, self)
        
        logger.info(f"Serviço {self.service_name} inicializado e registrado no hub")
    
    @abstractmethod
    def get_entity_type(self) -> str:
        """
        Retorna o tipo de entidade gerenciada por este serviço.
        
        Deve ser implementado por cada serviço concreto.
        
        Returns:
            String representando o tipo de entidade (ex: "product", "customer").
        """
        pass
    
    def get_cache_key(self, entity_id: Union[str, int]) -> str:
        """
        Gera uma chave de cache para a entidade.
        
        Args:
            entity_id: ID da entidade.
            
        Returns:
            Chave de cache formatada.
        """
        return f"{self.get_entity_type()}:{entity_id}"
    
    def get_by_id(self, entity_id: Union[str, int], use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Obtém uma entidade pelo ID.
        
        Args:
            entity_id: ID da entidade.
            use_cache: Se True, tenta obter do cache primeiro.
            
        Returns:
            Dados da entidade ou None se não encontrada.
        """
        # Verificar cache se solicitado
        if use_cache:
            cached_data = self.hub.cache_get(str(entity_id), self.get_entity_type())
            if cached_data:
                logger.debug(f"Cache hit para {self.get_entity_type()}:{entity_id}")
                return cached_data
        
        # Implementação padrão que pode ser sobrescrita
        table_name = self.get_entity_type()
        query = f"SELECT * FROM {table_name} WHERE id = %(id)s"
        params = {"id": entity_id}
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        # Armazenar em cache se encontrado
        if result and use_cache:
            self.hub.cache_set(str(entity_id), result, self.get_entity_type())
        
        return result
    
    def query(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Consulta entidades com base em filtros.
        
        Args:
            filters: Critérios de filtro.
            limit: Limite de resultados.
            offset: Deslocamento para paginação.
            
        Returns:
            Lista de entidades que correspondem aos filtros.
        """
        # Implementação básica que pode ser sobrescrita por serviços específicos
        table_name = self.get_entity_type()
        
        # Construir cláusula WHERE
        where_clauses = []
        params = {}
        
        for key, value in filters.items():
            where_clauses.append(f"{key} = %({key})s")
            params[key] = value
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT * FROM {table_name}
            WHERE {where_clause}
            LIMIT {limit} OFFSET {offset}
        """
        
        return self.hub.execute_query(query, params) or []
    
    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Cria uma nova entidade.
        
        Args:
            data: Dados da entidade.
            
        Returns:
            Entidade criada com ID ou None em caso de erro.
        """
        table_name = self.get_entity_type()
        
        # Extrair colunas e valores
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({key})s" for key in data.keys()])
        
        query = f"""
            INSERT INTO {table_name} ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        
        result = self.hub.execute_query(query, data, fetch_all=False)
        
        # Invalidar cache potencialmente desatualizado
        if result and 'id' in result:
            self.hub.cache_invalidate(str(result['id']), self.get_entity_type())
        
        return result
    
    def update(self, entity_id: Union[str, int], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Atualiza uma entidade existente.
        
        Args:
            entity_id: ID da entidade.
            data: Dados para atualizar.
            
        Returns:
            Entidade atualizada ou None em caso de erro.
        """
        table_name = self.get_entity_type()
        
        # Construir SET clause
        set_clauses = [f"{key} = %({key})s" for key in data.keys()]
        set_clause = ", ".join(set_clauses)
        
        # Adicionar ID aos parâmetros
        params = dict(data)
        params['id'] = entity_id
        
        query = f"""
            UPDATE {table_name}
            SET {set_clause}
            WHERE id = %(id)s
            RETURNING *
        """
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        # Invalidar cache
        self.hub.cache_invalidate(str(entity_id), self.get_entity_type())
        
        return result
    
    def delete(self, entity_id: Union[str, int]) -> bool:
        """
        Exclui uma entidade.
        
        Args:
            entity_id: ID da entidade.
            
        Returns:
            True se excluído com sucesso, False caso contrário.
        """
        table_name = self.get_entity_type()
        
        query = f"""
            DELETE FROM {table_name}
            WHERE id = %(id)s
            RETURNING id
        """
        
        result = self.hub.execute_query(query, {"id": entity_id}, fetch_all=False)
        
        # Invalidar cache
        self.hub.cache_invalidate(str(entity_id), self.get_entity_type())
        
        return result is not None
    
    def execute_custom_query(self, query: str, params: Dict[str, Any] = None, fetch_all: bool = True):
        """
        Executa uma consulta SQL personalizada.
        
        Este método permite que serviços específicos executem consultas
        mais complexas quando necessário.
        
        Args:
            query: Consulta SQL.
            params: Parâmetros para a consulta.
            fetch_all: Se True, retorna todos os resultados; se False, apenas o primeiro.
            
        Returns:
            Resultados da consulta ou None em caso de erro.
        """
        return self.hub.execute_query(query, params, fetch_all)
