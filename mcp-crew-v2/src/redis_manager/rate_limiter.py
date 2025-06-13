"""
Sistema de Rate Limiting usando Redis para o MCP-Crew v2.

Implementa métodos para limitar o número de requisições por tenant.
"""

import logging
import time
from typing import Dict, Optional, Tuple

from src.redis_manager.redis_manager import redis_manager, DataType

logger = logging.getLogger(__name__)

class RateLimiter:
    """Gerencia limites de requisições usando Redis."""
    
    def __init__(self, tenant_id: str):
        """
        Inicializa o limitador de requisições.
        
        Args:
            tenant_id: ID do tenant (account_id)
        """
        self.tenant_id = tenant_id
    
    def check_limit(self, operation: str, limit: int, window_seconds: int = 60) -> Tuple[bool, Dict]:
        """
        Verifica se uma operação excedeu o limite de requisições.
        
        Args:
            operation: Nome da operação
            limit: Número máximo de requisições permitidas
            window_seconds: Janela de tempo em segundos
            
        Returns:
            Tuple[bool, Dict]: (permitido, informações)
        """
        try:
            # Chave para o contador
            key = f"rate:{operation}"
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Obter contador atual
            counter = redis_manager.get(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=key
            )
            
            if not counter:
                # Inicializar contador
                counter = {
                    "requests": [],
                    "operation": operation,
                    "limit": limit,
                    "window_seconds": window_seconds
                }
            
            # Filtrar requisições dentro da janela de tempo
            counter["requests"] = [ts for ts in counter["requests"] if ts > window_start]
            
            # Verificar se excedeu o limite
            current_count = len(counter["requests"])
            allowed = current_count < limit
            
            if allowed:
                # Adicionar timestamp da requisição atual
                counter["requests"].append(current_time)
                
                # Atualizar contador no Redis
                redis_manager.set(
                    tenant_id=self.tenant_id,
                    data_type=DataType.QUERY_RESULT,
                    identifier=key,
                    value=counter,
                    ttl=window_seconds * 2  # TTL maior que a janela
                )
            
            # Informações sobre o limite
            info = {
                "allowed": allowed,
                "current": current_count + (1 if allowed else 0),
                "limit": limit,
                "remaining": max(0, limit - current_count - (1 if allowed else 0)),
                "reset_after": window_seconds - (current_time - min(counter["requests"] + [current_time])) if counter["requests"] else 0
            }
            
            return allowed, info
            
        except Exception as e:
            logger.error(f"Erro ao verificar limite: {e}")
            # Em caso de erro, permitir a requisição
            return True, {"allowed": True, "error": str(e)}
    
    def increment_counter(self, operation: str, increment: int = 1, ttl: int = 3600) -> int:
        """
        Incrementa um contador genérico.
        
        Args:
            operation: Nome da operação
            increment: Valor a incrementar
            ttl: Tempo de vida do contador em segundos
            
        Returns:
            int: Valor atual do contador
        """
        try:
            # Chave para o contador
            key = f"counter:{operation}"
            
            # Obter valor atual
            value = redis_manager.get(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=key
            )
            
            # Incrementar
            new_value = (value or 0) + increment
            
            # Atualizar no Redis
            redis_manager.set(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=key,
                value=new_value,
                ttl=ttl
            )
            
            return new_value
            
        except Exception as e:
            logger.error(f"Erro ao incrementar contador: {e}")
            return 0
    
    def get_counter(self, operation: str) -> int:
        """
        Obtém o valor atual de um contador.
        
        Args:
            operation: Nome da operação
            
        Returns:
            int: Valor atual do contador
        """
        try:
            # Chave para o contador
            key = f"counter:{operation}"
            
            # Obter valor atual
            value = redis_manager.get(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=key
            )
            
            return value or 0
            
        except Exception as e:
            logger.error(f"Erro ao obter contador: {e}")
            return 0
    
    def reset_counter(self, operation: str) -> bool:
        """
        Reseta um contador.
        
        Args:
            operation: Nome da operação
            
        Returns:
            bool: True se resetado com sucesso
        """
        try:
            # Chave para o contador
            key = f"counter:{operation}"
            
            # Remover do Redis
            return redis_manager.delete(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=key
            )
            
        except Exception as e:
            logger.error(f"Erro ao resetar contador: {e}")
            return False
