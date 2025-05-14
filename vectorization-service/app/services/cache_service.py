"""
Serviço para gerenciamento de cache.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.redis_service import RedisService
from app.core.config import settings
from app.core.exceptions import CacheError

logger = logging.getLogger(__name__)

class CacheService:
    """Serviço para gerenciamento de cache com invalidação inteligente."""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
    
    async def invalidate_rule_cache(self, account_id: str, rule_id: Optional[int] = None):
        """
        Invalida o cache relacionado a uma regra específica ou todas as regras de uma conta.
        
        Args:
            account_id: ID da conta
            rule_id: ID da regra (opcional, se None invalida todas as regras da conta)
        """
        try:
            # Chaves de cache a serem invalidadas
            keys_to_invalidate = []
            
            # Chave principal de regras da conta
            main_key = f"business_rules:{account_id}"
            keys_to_invalidate.append(main_key)
            
            # Se um rule_id específico foi fornecido
            if rule_id is not None:
                # Invalidar cache específico da regra
                rule_key = f"business_rule:{account_id}:{rule_id}"
                keys_to_invalidate.append(rule_key)
                
                # Invalidar cache de pesquisa que pode conter esta regra
                search_pattern = f"search:business_rules:{account_id}:*"
                search_keys = await self.redis.keys(search_pattern)
                keys_to_invalidate.extend(search_keys)
            else:
                # Invalidar todos os caches relacionados a regras desta conta
                all_rules_pattern = f"business_rule:{account_id}:*"
                all_search_pattern = f"search:business_rules:{account_id}:*"
                
                rule_keys = await self.redis.keys(all_rules_pattern)
                search_keys = await self.redis.keys(all_search_pattern)
                
                keys_to_invalidate.extend(rule_keys)
                keys_to_invalidate.extend(search_keys)
            
            # Invalidar todas as chaves identificadas
            if keys_to_invalidate:
                await self.redis.delete_many(keys_to_invalidate)
                logger.info(f"Invalidados {len(keys_to_invalidate)} caches para account_id={account_id}, rule_id={rule_id}")
            
            # Atualizar metadados de cache
            await self.redis.set_json(
                key=f"cache_meta:{account_id}:business_rules",
                value={
                    "last_invalidation": datetime.now().isoformat(),
                    "invalidated_by": f"rule_id={rule_id}" if rule_id else "full_sync"
                },
                expiry=settings.REDIS_METADATA_TTL
            )
            
        except Exception as e:
            logger.error(f"Erro ao invalidar cache: {str(e)}")
            # Não propagar exceção para não interromper o fluxo principal
    
    async def invalidate_collection_cache(self, account_id: str, collection_type: str):
        """
        Invalida o cache relacionado a uma coleção inteira.
        
        Args:
            account_id: ID da conta
            collection_type: Tipo de coleção (business_rules, scheduling_rules, support_documents)
        """
        try:
            # Padrão para todas as chaves relacionadas à coleção
            pattern = f"{collection_type}:{account_id}:*"
            keys = await self.redis.keys(pattern)
            
            # Adicionar chave principal da coleção
            main_key = f"{collection_type}:{account_id}"
            keys.append(main_key)
            
            # Invalidar todas as chaves
            if keys:
                await self.redis.delete_many(keys)
                logger.info(f"Invalidados {len(keys)} caches para coleção {collection_type} da conta {account_id}")
            
            # Atualizar metadados de cache
            await self.redis.set_json(
                key=f"cache_meta:{account_id}:{collection_type}",
                value={
                    "last_invalidation": datetime.now().isoformat(),
                    "invalidated_by": "collection_sync"
                },
                expiry=settings.REDIS_METADATA_TTL
            )
            
        except Exception as e:
            logger.error(f"Erro ao invalidar cache de coleção: {str(e)}")
            # Não propagar exceção para não interromper o fluxo principal
