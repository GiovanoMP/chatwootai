"""
API para sincronização de regras de negócio.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status

from app.models.business_rule import BusinessRuleSync, BusinessRuleResponse, BusinessRuleSearch
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.services.enrichment_service import EnrichmentService
from app.services.cache_service import CacheService
from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.exceptions import VectorDBError, EmbeddingError
from app.core.dependencies import get_vector_service, get_embedding_service, get_enrichment_service, get_cache_service

router = APIRouter(prefix="/api/v1/business-rules", tags=["business-rules"])

# Loggers específicos
logger = logging.getLogger(__name__)
sync_logger = logging.getLogger("vectorization.sync")
embedding_logger = logging.getLogger("vectorization.embedding")
critical_logger = logging.getLogger("vectorization.critical")

@router.post("/sync", response_model=BusinessRuleResponse)
async def sync_business_rules(
    data: BusinessRuleSync,
    vector_service: VectorService = Depends(get_vector_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    enrichment_service: EnrichmentService = Depends(get_enrichment_service),
    cache_service: CacheService = Depends(get_cache_service),
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Sincroniza regras de negócio permanentes e temporárias com o sistema de IA.
    Ambos os tipos são armazenados na mesma coleção com flags para distingui-los.
    """
    start_time = time.time()
    operation_id = f"sync_{datetime.now().strftime('%Y%m%d%H%M%S')}_{data.account_id}"

    sync_logger.info(f"[{operation_id}] Iniciando sincronização de regras de negócio para account_id={data.account_id}, business_rule_id={data.business_rule_id}")

    # Verificar API key
    verify_api_key(api_key)

    account_id = data.account_id
    business_rule_id = data.business_rule_id

    # Coleção global para regras de negócio
    collection_name = "business_rules"

    # Contadores
    vectorized_rules = 0
    removed_rules = 0

    sync_logger.info(f"[{operation_id}] Regras permanentes: {len(data.rules.permanent_rules)}, Regras temporárias: {len(data.rules.temporary_rules)}")

    try:
        # 1. Obter IDs de todas as regras existentes no Qdrant para esta conta
        existing_rule_ids = await vector_service.get_all_rule_ids(
            collection_name=collection_name,
            account_id=account_id
        )

        # 2. Coletar IDs de todas as regras recebidas na sincronização
        current_rule_ids = set()

        # Mapear regras permanentes para IDs
        permanent_rule_ids = {f"rule_perm_{rule.id}" for rule in data.rules.permanent_rules}
        current_rule_ids.update(permanent_rule_ids)

        # Mapear regras temporárias para IDs
        temporary_rule_ids = {f"rule_temp_{rule.id}" for rule in data.rules.temporary_rules}
        current_rule_ids.update(temporary_rule_ids)

        # 3. Identificar regras a serem removidas (existem no Qdrant mas não na sincronização atual)
        rules_to_remove = existing_rule_ids - current_rule_ids

        # 4. Remover regras que não existem mais
        if rules_to_remove:
            await vector_service.delete_vectors(
                collection_name=collection_name,
                vector_ids=list(rules_to_remove)
            )
            removed_rules = len(rules_to_remove)
            logger.info(f"Removidas {removed_rules} regras obsoletas da coleção {collection_name}")

        # 5. Processar regras permanentes
        for rule in data.rules.permanent_rules:
            # Preparar texto para embedding
            rule_text = f"""
            Nome: {rule.name}
            Tipo: {rule.type}
            Descrição: {rule.description}
            """

            # Gerar embedding com limite de tokens
            embedding = await embedding_service.generate_embedding(
                text=rule_text,
                max_tokens=settings.MAX_EMBEDDING_TOKENS
            )

            # Preparar payload com flag para regra permanente
            payload = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "type": rule.type,
                "account_id": account_id,
                "business_rule_id": business_rule_id,
                "is_temporary": False,
                "last_updated": rule.last_updated
            }

            # Armazenar no Qdrant
            await vector_service.store_vector(
                collection_name=collection_name,
                vector_id=f"rule_perm_{rule.id}",
                vector=embedding,
                payload=payload
            )

            vectorized_rules += 1

        # 6. Processar regras temporárias
        for rule in data.rules.temporary_rules:
            # Preparar texto para embedding
            rule_text = f"""
            Nome: {rule.name}
            Tipo: {rule.type}
            Descrição: {rule.description}
            Data Início: {rule.start_date}
            Data Fim: {rule.end_date}
            """

            # Gerar embedding com limite de tokens
            embedding = await embedding_service.generate_embedding(
                text=rule_text,
                max_tokens=settings.MAX_EMBEDDING_TOKENS
            )

            # Preparar payload com flag para regra temporária
            payload = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "type": rule.type,
                "account_id": account_id,
                "business_rule_id": business_rule_id,
                "is_temporary": True,
                "start_date": rule.start_date,
                "end_date": rule.end_date,
                "last_updated": rule.last_updated
            }

            # Armazenar no Qdrant
            await vector_service.store_vector(
                collection_name=collection_name,
                vector_id=f"rule_temp_{rule.id}",
                vector=embedding,
                payload=payload
            )

            vectorized_rules += 1

        # 7. Invalidar cache no Redis
        await cache_service.invalidate_collection_cache(
            account_id=account_id,
            collection_type="business_rules"
        )

        # 8. Atualizar metadados de sincronização no Redis
        sync_metadata = {
            "last_sync": datetime.now().isoformat(),
            "rule_count": vectorized_rules,
            "removed_count": removed_rules,
            "business_rule_id": business_rule_id
        }

        await vector_service.redis_service.set_json(
            key=f"sync:business_rules:{account_id}",
            value=sync_metadata,
            expiry=settings.REDIS_SYNC_METADATA_TTL
        )

        return {
            "success": True,
            "data": {
                "vectorized_rules": vectorized_rules,
                "removed_rules": removed_rules,
                "collection": collection_name
            },
            "message": f"Sincronizadas {vectorized_rules} regras de negócio, removidas {removed_rules} regras obsoletas"
        }

    except (VectorDBError, EmbeddingError) as e:
        logger.error(f"Erro ao sincronizar regras: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Erro inesperado ao sincronizar regras: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/search", response_model=BusinessRuleResponse)
async def search_business_rules(
    data: BusinessRuleSearch,
    vector_service: VectorService = Depends(get_vector_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    cache_service: CacheService = Depends(get_cache_service),
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Busca regras de negócio semanticamente similares a uma consulta.
    """
    # Verificar API key
    verify_api_key(api_key)

    account_id = data.account_id
    query = data.query
    limit = data.limit
    score_threshold = data.score_threshold

    # Coleção global para regras de negócio
    collection_name = "business_rules"

    try:
        # Verificar cache
        cache_key = f"search:business_rules:{account_id}:{hash(query)}"
        cached_results = await vector_service.redis_service.get_json(cache_key)

        if cached_results:
            logger.info(f"Usando resultados em cache para consulta: {query}")
            return {
                "success": True,
                "data": {
                    "results": cached_results,
                    "count": len(cached_results),
                    "query": query
                },
                "message": f"Encontradas {len(cached_results)} regras de negócio (cache)"
            }

        # Gerar embedding para a consulta
        query_embedding = await embedding_service.generate_embedding(
            text=query,
            max_tokens=settings.MAX_EMBEDDING_TOKENS
        )

        # Buscar regras similares
        results = await vector_service.search_vectors(
            collection_name=collection_name,
            query_vector=query_embedding,
            filter_conditions={"account_id": account_id},
            limit=limit,
            score_threshold=score_threshold
        )

        # Armazenar em cache
        await vector_service.redis_service.set_json(
            key=cache_key,
            value=results,
            expiry=3600  # 1 hora
        )

        return {
            "success": True,
            "data": {
                "results": results,
                "count": len(results),
                "query": query
            },
            "message": f"Encontradas {len(results)} regras de negócio"
        }

    except (VectorDBError, EmbeddingError) as e:
        logger.error(f"Erro ao buscar regras: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar regras: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
