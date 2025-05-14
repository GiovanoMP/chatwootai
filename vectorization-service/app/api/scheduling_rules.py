"""
API para sincronização de regras de agendamento.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status

from app.models.scheduling_rule import SchedulingRuleSync, SchedulingRuleResponse
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.services.cache_service import CacheService
from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.exceptions import VectorDBError, EmbeddingError
from app.core.dependencies import get_vector_service, get_embedding_service, get_cache_service

router = APIRouter(prefix="/api/v1/scheduling-rules", tags=["scheduling-rules"])

# Loggers específicos
logger = logging.getLogger(__name__)
sync_logger = logging.getLogger("vectorization.sync")
embedding_logger = logging.getLogger("vectorization.embedding")
critical_logger = logging.getLogger("vectorization.critical")

@router.post("/sync", response_model=SchedulingRuleResponse)
async def sync_scheduling_rules(
    data: SchedulingRuleSync,
    vector_service: VectorService = Depends(get_vector_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    cache_service: CacheService = Depends(get_cache_service),
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Sincroniza regras de agendamento com o sistema de IA.
    """
    start_time = time.time()
    operation_id = f"sync_scheduling_{datetime.now().strftime('%Y%m%d%H%M%S')}_{data.account_id}"

    sync_logger.info(f"[{operation_id}] Iniciando sincronização de regras de agendamento para account_id={data.account_id}, business_rule_id={data.business_rule_id}")

    # Verificar API key
    verify_api_key(api_key)

    account_id = data.account_id
    business_rule_id = data.business_rule_id

    # Coleção global para regras de agendamento
    collection_name = "scheduling_rules"

    # Contadores
    vectorized_rules = 0
    removed_rules = 0

    sync_logger.info(f"[{operation_id}] Regras de agendamento: {len(data.scheduling_rules)}")

    try:
        # 1. Obter IDs de todas as regras existentes no Qdrant para esta conta
        existing_rule_ids = await vector_service.get_all_rule_ids(
            collection_name=collection_name,
            account_id=account_id
        )

        # 2. Coletar IDs de todas as regras recebidas na sincronização
        current_rule_ids = {f"scheduling_rule_{rule.id}" for rule in data.scheduling_rules}

        # 3. Identificar regras a serem removidas (existem no Qdrant mas não na sincronização atual)
        rules_to_remove = existing_rule_ids - current_rule_ids

        # 4. Remover regras que não existem mais
        if rules_to_remove:
            await vector_service.delete_vectors(
                collection_name=collection_name,
                vector_ids=list(rules_to_remove)
            )
            removed_rules = len(rules_to_remove)
            logger.info(f"Removidas {removed_rules} regras de agendamento obsoletas da coleção {collection_name}")

        # 5. Processar regras de agendamento
        for rule in data.scheduling_rules:
            # Preparar texto para embedding
            days_available = []
            if rule.days_available.monday:
                days_available.append("Segunda-feira")
            if rule.days_available.tuesday:
                days_available.append("Terça-feira")
            if rule.days_available.wednesday:
                days_available.append("Quarta-feira")
            if rule.days_available.thursday:
                days_available.append("Quinta-feira")
            if rule.days_available.friday:
                days_available.append("Sexta-feira")
            if rule.days_available.saturday:
                days_available.append("Sábado")
            if rule.days_available.sunday:
                days_available.append("Domingo")

            days_text = ", ".join(days_available)

            rule_text = f"""
            Nome: {rule.name}
            Tipo de Serviço: {rule.service_type}
            Descrição: {rule.description}
            Duração: {rule.duration} minutos
            Intervalo Mínimo: {rule.min_interval} minutos
            Antecedência Mínima: {rule.min_advance_time} horas
            Antecedência Máxima: {rule.max_advance_time} dias
            Dias Disponíveis: {days_text}
            Horário Manhã: {rule.hours.morning_start} às {rule.hours.morning_end}
            Horário Tarde: {rule.hours.afternoon_start} às {rule.hours.afternoon_end}
            Política de Cancelamento: {rule.policies.cancellation}
            Política de Reagendamento: {rule.policies.rescheduling}
            """

            # Gerar embedding com limite de tokens
            embedding = await embedding_service.generate_embedding(
                text=rule_text,
                max_tokens=settings.MAX_EMBEDDING_TOKENS
            )

            # Preparar payload
            payload = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "service_type": rule.service_type,
                "service_type_other": rule.service_type_other,
                "duration": rule.duration,
                "min_interval": rule.min_interval,
                "min_advance_time": rule.min_advance_time,
                "max_advance_time": rule.max_advance_time,
                "days_available": rule.days_available.model_dump(),
                "hours": rule.hours.model_dump(),
                "special_hours": rule.special_hours.model_dump(),
                "policies": rule.policies.model_dump(),
                "account_id": account_id,
                "business_rule_id": business_rule_id,
                "last_updated": rule.last_updated
            }

            # Armazenar no Qdrant
            await vector_service.store_vector(
                collection_name=collection_name,
                vector_id=f"scheduling_rule_{rule.id}",
                vector=embedding,
                payload=payload
            )

            vectorized_rules += 1

        # 6. Invalidar cache no Redis
        await cache_service.invalidate_collection_cache(
            account_id=account_id,
            collection_type="scheduling_rules"
        )

        # 7. Atualizar metadados de sincronização no Redis
        sync_metadata = {
            "last_sync": datetime.now().isoformat(),
            "rule_count": vectorized_rules,
            "removed_count": removed_rules,
            "business_rule_id": business_rule_id
        }

        await vector_service.redis_service.set_json(
            key=f"sync:scheduling_rules:{account_id}",
            value=sync_metadata,
            expiry=settings.REDIS_SYNC_METADATA_TTL
        )

        # Calcular tempo de execução
        execution_time = time.time() - start_time

        # Registrar conclusão da sincronização
        sync_logger.info(f"[{operation_id}] Sincronização concluída em {execution_time:.2f}s. Regras vetorizadas: {vectorized_rules}, Regras removidas: {removed_rules}")

        return {
            "success": True,
            "data": {
                "vectorized_rules": vectorized_rules,
                "removed_rules": removed_rules,
                "collection": collection_name,
                "execution_time": f"{execution_time:.2f}s"
            },
            "message": f"Sincronizadas {vectorized_rules} regras de agendamento, removidas {removed_rules} regras obsoletas"
        }

    except (VectorDBError, EmbeddingError) as e:
        execution_time = time.time() - start_time
        error_message = f"Erro ao sincronizar regras de agendamento: {str(e)}"
        critical_logger.error(f"[{operation_id}] {error_message} (após {execution_time:.2f}s)")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        execution_time = time.time() - start_time
        error_message = f"Erro inesperado ao sincronizar regras de agendamento: {str(e)}"
        critical_logger.error(f"[{operation_id}] {error_message} (após {execution_time:.2f}s)")
        # Registrar traceback completo para depuração
        import traceback
        critical_logger.error(f"[{operation_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
