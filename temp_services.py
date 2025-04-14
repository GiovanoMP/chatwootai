# -*- coding: utf-8 -*-

"""
Serviços para o módulo Business Rules.
"""

import logging
import base64
import io
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, timedelta

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import ValidationError, NotFoundError, OdooOperationError, VectorDBError
from odoo_api.core.odoo_connector import OdooConnector, OdooConnectorFactory
from odoo_api.services.cache_service import get_cache_service
from odoo_api.services.vector_service import get_vector_service
from odoo_api.embedding_agents.business_rules_agent import get_business_rules_agent
from qdrant_client.http import models
from odoo_api.modules.business_rules.schemas import (
    BusinessRuleRequest,
    TemporaryRuleRequest,
    BusinessRuleResponse,
    BusinessRuleListResponse,
    BusinessRuleSyncResponse,
    DocumentUploadRequest,
    DocumentResponse,
    DocumentListResponse,
    RuleType,
)

logger = logging.getLogger(__name__)

class BusinessRulesService:
    """Serviço para o módulo Business Rules."""

    async def sync_business_rules(
        self,
        account_id: str,
    ) -> BusinessRuleSyncResponse:
        """
        Sincroniza regras de negócio com o sistema de IA.

        Armazena as regras tanto no Redis (para acesso rápido) quanto no Qdrant (para busca semântica).

        Args:
            account_id: ID da conta

        Returns:
            Resultado da sincronização
        """
        try:
            # Obter regras ativas
            active_rules = await self.list_active_rules(account_id)

            # Contar regras permanentes e temporárias
            permanent_rules = sum(1 for rule in active_rules if not rule.is_temporary)
            temporary_rules = sum(1 for rule in active_rules if rule.is_temporary)

            # 1. Sincronizar com Redis para acesso rápido
            cache = await get_cache_service()

            # Agrupar regras por tipo
            rules_by_type = {}
            for rule in active_rules:
                if rule.type not in rules_by_type:
                    rules_by_type[rule.type] = []
                rules_by_type[rule.type].append(rule.model_dump())

            # Armazenar cada tipo de regra separadamente no Redis
            for rule_type, rules in rules_by_type.items():
                await cache.set(
                    f"{account_id}:ai:rules:{rule_type}",
                    rules,
                    ttl=86400,  # 24 horas
                )

            # Armazenar todas as regras juntas no Redis
            await cache.set(
                f"{account_id}:ai:rules:all",
                [rule.model_dump() for rule in active_rules],
                ttl=86400,  # 24 horas
            )

            # 2. Sincronizar com Qdrant para busca semântica
            vector_service = await get_vector_service()
            collection_name = f"business_rules_{account_id}"

            # Garantir que a coleção existe
            await vector_service.ensure_collection_exists(collection_name)

            # Obter o agente de embedding específico para regras de negócio
            embedding_agent = await get_business_rules_agent()

            # Obter a área de negócio da conta (se disponível)
            business_area = await self._get_business_area(account_id)

            # Vetorizar e armazenar cada regra
            vectorized_rules = 0
            for rule in active_rules:
                # Preparar dados da regra para o agente
                rule_data = rule.model_dump()

                # Processar a regra usando o agente de embeddings específico
                processed_text = await embedding_agent.process_data(rule_data, business_area)

                # Gerar embedding do texto processado
                embedding = await vector_service.generate_embedding(processed_text)

                # Armazenar no Qdrant
                point_id = f"rule_{rule.id}"
                await vector_service.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=[
                        models.PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                "rule_id": rule.id,
                                "name": rule.name,
                                "description": rule.description,
                                "type": rule.type,
                                "priority": rule.priority if hasattr(rule, "priority") else None,
                                "is_temporary": rule.is_temporary,
                                "start_date": rule.start_date.isoformat() if rule.start_date else None,
                                "end_date": rule.end_date.isoformat() if rule.end_date else None,
                                "rule_data": rule.rule_data,
                                "processed_text": processed_text,
                                "last_updated": datetime.now().isoformat()
                            }
                        )
                    ],
                )
                vectorized_rules += 1

            # Armazenar timestamp da sincronização
            await cache.set(
                key=f"{account_id}:ai:rules:last_sync",
                value=datetime.now().isoformat(),
                ttl=86400 * 30  # 30 dias
            )

            return BusinessRuleSyncResponse(
                permanent_rules=permanent_rules,
                temporary_rules=temporary_rules,
                vectorized_rules=vectorized_rules,
                sync_status="completed",
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Failed to sync business rules: {e}")
            return BusinessRuleSyncResponse(
                permanent_rules=0,
                temporary_rules=0,
                vectorized_rules=0,
                sync_status="failed",
                timestamp=datetime.now(),
                error=str(e)
            )

    async def _get_business_area(self, account_id: str) -> Optional[str]:
        """
        Obtém a área de negócio da conta.

        Args:
            account_id: ID da conta

        Returns:
            Área de negócio ou None se não encontrada
        """
        try:
            # Obter conector Odoo
            odoo_connector = await OdooConnectorFactory.create_connector(account_id)

            # Buscar configurações da empresa
            company_settings = await odoo_connector.search_read(
                model="business.rules",
                domain=[],
                fields=["business_model", "business_model_other"],
                limit=1
            )

            if company_settings and len(company_settings) > 0:
                business_model = company_settings[0].get("business_model")

                # Se for "other", usar o campo business_model_other
                if business_model == "other":
                    return company_settings[0].get("business_model_other")

                return business_model

            return None

        except Exception as e:
            logger.warning(f"Failed to get business area for account {account_id}: {e}")
            return None

    async def search_business_rules(
        self,
        account_id: str,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca regras de negócio por similaridade semântica.

        Args:
            account_id: ID da conta
            query: Consulta de busca
            limit: Limite de resultados
            score_threshold: Limiar de similaridade

        Returns:
            Lista de regras ordenadas por similaridade
        """
        try:
            # Obter serviços
            vector_service = await get_vector_service()

            # Gerar embedding da consulta
            query_embedding = await vector_service.generate_embedding(query)

            # Buscar regras similares
            collection_name = f"business_rules_{account_id}"
            search_results = await vector_service.search_vectors(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )

            return search_results

        except Exception as e:
            logger.error(f"Failed to search business rules: {e}")
            return []
