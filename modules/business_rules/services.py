# -*- coding: utf-8 -*-

"""
Serviços para o módulo Business Rules.

Este módulo implementa os serviços para o módulo Business Rules,
incluindo criação, atualização, exclusão e sincronização de regras de negócio.
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
    RulePriority,
)

logger = logging.getLogger(__name__)

class BusinessRulesService:
    """Serviço para o módulo Business Rules."""

    async def create_business_rule(
        self,
        account_id: str,
        rule_data: BusinessRuleRequest,
    ) -> BusinessRuleResponse:
        """
        Cria uma nova regra de negócio.

        Args:
            account_id: ID da conta
            rule_data: Dados da regra

        Returns:
            Regra criada
        """
        try:
            # Validar dados
            self._validate_rule_data(rule_data)

            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Converter dados para formato do Odoo
            odoo_data = {
                'name': rule_data.name,
                'description': rule_data.description,
                'type': rule_data.type,
                'priority': rule_data.priority if hasattr(rule_data, 'priority') else RulePriority.MEDIUM,
                'is_temporary': rule_data.is_temporary,
                'website': rule_data.website or '',
            }

            # Adicionar dados específicos para regras temporárias
            if rule_data.is_temporary:
                if not hasattr(rule_data, 'start_date') or not hasattr(rule_data, 'end_date'):
                    raise ValidationError("Temporary rules must have start_date and end_date")

                odoo_data['start_date'] = rule_data.start_date.isoformat()
                odoo_data['end_date'] = rule_data.end_date.isoformat()

            # Adicionar dados específicos por tipo de regra
            if hasattr(rule_data, 'rule_data') and rule_data.rule_data:
                odoo_data['rule_data'] = json.dumps(rule_data.rule_data)

            # Criar regra no Odoo
            rule_id = await odoo.create(
                model="business.rules",
                values=odoo_data
            )

            # Buscar regra criada
            rule = await self._get_rule_by_id(odoo, rule_id)

            # Sincronizar com IA
            await self._sync_single_rule(account_id, rule)

            return rule

        except Exception as e:
            logger.error(f"Failed to create business rule: {e}")
            raise

    async def update_business_rule(
        self,
        account_id: str,
        rule_id: int,
        rule_data: BusinessRuleRequest,
    ) -> BusinessRuleResponse:
        """
        Atualiza uma regra de negócio existente.

        Args:
            account_id: ID da conta
            rule_id: ID da regra
            rule_data: Dados atualizados da regra

        Returns:
            Regra atualizada
        """
        try:
            # Validar dados
            self._validate_rule_data(rule_data)

            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Verificar se a regra existe
            existing_rule = await self._get_rule_by_id(odoo, rule_id)
            if not existing_rule:
                raise NotFoundError(f"Business rule with ID {rule_id} not found")

            # Converter dados para formato do Odoo
            odoo_data = {
                'name': rule_data.name,
                'description': rule_data.description,
                'type': rule_data.type,
                'priority': rule_data.priority if hasattr(rule_data, 'priority') else existing_rule.priority,
                'is_temporary': rule_data.is_temporary,
                'website': rule_data.website or '',
            }

            # Adicionar dados específicos para regras temporárias
            if rule_data.is_temporary:
                if not hasattr(rule_data, 'start_date') or not hasattr(rule_data, 'end_date'):
                    raise ValidationError("Temporary rules must have start_date and end_date")

                odoo_data['start_date'] = rule_data.start_date.isoformat()
                odoo_data['end_date'] = rule_data.end_date.isoformat()

            # Adicionar dados específicos por tipo de regra
            if hasattr(rule_data, 'rule_data') and rule_data.rule_data:
                odoo_data['rule_data'] = json.dumps(rule_data.rule_data)

            # Atualizar regra no Odoo
            await odoo.write(
                model="business.rules",
                ids=[rule_id],
                values=odoo_data
            )

            # Buscar regra atualizada
            rule = await self._get_rule_by_id(odoo, rule_id)

            # Sincronizar com IA
            await self._sync_single_rule(account_id, rule)

            return rule

        except Exception as e:
            logger.error(f"Failed to update business rule: {e}")
            raise

    async def delete_business_rule(
        self,
        account_id: str,
        rule_id: int,
    ) -> bool:
        """
        Exclui uma regra de negócio.

        Args:
            account_id: ID da conta
            rule_id: ID da regra

        Returns:
            True se a regra foi excluída com sucesso
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Verificar se a regra existe
            existing_rule = await self._get_rule_by_id(odoo, rule_id)
            if not existing_rule:
                raise NotFoundError(f"Business rule with ID {rule_id} not found")

            # Excluir regra no Odoo
            await odoo.unlink(
                model="business.rules",
                ids=[rule_id]
            )

            # Remover da IA
            await self._remove_rule_from_ai(account_id, rule_id)

            return True

        except Exception as e:
            logger.error(f"Failed to delete business rule: {e}")
            raise

    async def get_business_rule(
        self,
        account_id: str,
        rule_id: int,
    ) -> BusinessRuleResponse:
        """
        Obtém uma regra de negócio pelo ID.

        Args:
            account_id: ID da conta
            rule_id: ID da regra

        Returns:
            Regra encontrada
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Buscar regra
            rule = await self._get_rule_by_id(odoo, rule_id)
            if not rule:
                raise NotFoundError(f"Business rule with ID {rule_id} not found")

            return rule

        except Exception as e:
            logger.error(f"Failed to get business rule: {e}")
            raise

    async def list_business_rules(
        self,
        account_id: str,
        limit: int = 100,
        offset: int = 0,
        include_temporary: bool = True,
    ) -> BusinessRuleListResponse:
        """
        Lista regras de negócio.

        Args:
            account_id: ID da conta
            limit: Limite de resultados
            offset: Deslocamento para paginação
            include_temporary: Incluir regras temporárias

        Returns:
            Lista de regras
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Construir domínio
            domain = []
            if not include_temporary:
                domain.append(("is_temporary", "=", False))

            # Buscar regras
            rules_data = await odoo.search_read(
                model="business.rules",
                domain=domain,
                fields=self._get_rule_fields(),
                limit=limit,
                offset=offset
            )

            # Converter para formato da API
            rules = [self._convert_to_api_format(rule) for rule in rules_data]

            # Contar total
            total = await odoo.search_count(
                model="business.rules",
                domain=domain
            )

            return BusinessRuleListResponse(
                total=total,
                limit=limit,
                offset=offset,
                rules=rules
            )

        except Exception as e:
            logger.error(f"Failed to list business rules: {e}")
            raise

    async def list_active_rules(
        self,
        account_id: str,
    ) -> List[BusinessRuleResponse]:
        """
        Lista regras de negócio ativas (permanentes e temporárias válidas).

        Args:
            account_id: ID da conta

        Returns:
            Lista de regras ativas
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Buscar regras permanentes
            permanent_domain = [("is_temporary", "=", False)]
            permanent_rules_data = await odoo.search_read(
                model="business.rules",
                domain=permanent_domain,
                fields=self._get_rule_fields()
            )

            # Buscar regras temporárias válidas
            today = date.today().isoformat()
            temporary_domain = [
                ("is_temporary", "=", True),
                ("start_date", "<=", today),
                ("end_date", ">=", today)
            ]
            temporary_rules_data = await odoo.search_read(
                model="business.rules",
                domain=temporary_domain,
                fields=self._get_rule_fields()
            )

            # Combinar e converter para formato da API
            all_rules_data = permanent_rules_data + temporary_rules_data
            rules = [self._convert_to_api_format(rule) for rule in all_rules_data]

            return rules

        except Exception as e:
            logger.error(f"Failed to list active rules: {e}")
            raise

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

    async def customer_support(
        self,
        account_id: str,
        message: str,
        file_content: Optional[str] = None,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Envia uma mensagem de suporte ao cliente, opcionalmente com um arquivo anexado.

        Args:
            account_id: ID da conta
            message: Mensagem de suporte
            file_content: Conteúdo do arquivo em base64 (opcional)
            file_name: Nome do arquivo (opcional)
            file_type: Tipo do arquivo (opcional)

        Returns:
            Resposta do sistema de suporte
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Preparar dados
            support_data = {
                'message': message,
                'source': 'api',
                'status': 'new',
            }

            # Adicionar arquivo, se fornecido
            if file_content and file_name:
                support_data['file_name'] = file_name
                support_data['file_type'] = file_type or 'application/octet-stream'
                support_data['file_content'] = file_content

            # Criar ticket de suporte no Odoo
            ticket_id = await odoo.create(
                model="business.rules.support",
                values=support_data
            )

            # Buscar ticket criado
            ticket_data = await odoo.search_read(
                model="business.rules.support",
                domain=[("id", "=", ticket_id)],
                fields=["id", "message", "status", "create_date", "response"],
                limit=1
            )

            if not ticket_data:
                raise NotFoundError(f"Support ticket with ID {ticket_id} not found")

            return {
                "id": ticket_data[0]["id"],
                "message": ticket_data[0]["message"],
                "status": ticket_data[0]["status"],
                "created_at": ticket_data[0]["create_date"],
                "response": ticket_data[0].get("response", "")
            }

        except Exception as e:
            logger.error(f"Failed to create support ticket: {e}")
            raise

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

    async def _get_rule_by_id(self, odoo: OdooConnector, rule_id: int) -> Optional[BusinessRuleResponse]:
        """
        Obtém uma regra pelo ID.

        Args:
            odoo: Conector Odoo
            rule_id: ID da regra

        Returns:
            Regra encontrada ou None
        """
        rules_data = await odoo.search_read(
            model="business.rules",
            domain=[("id", "=", rule_id)],
            fields=self._get_rule_fields(),
            limit=1
        )

        if not rules_data:
            return None

        return self._convert_to_api_format(rules_data[0])

    async def _sync_single_rule(self, account_id: str, rule: BusinessRuleResponse) -> bool:
        """
        Sincroniza uma única regra com o sistema de IA.

        Args:
            account_id: ID da conta
            rule: Regra a ser sincronizada

        Returns:
            True se a sincronização foi bem-sucedida
        """
        try:
            # Verificar se a regra está ativa
            today = date.today()
            is_active = (
                not rule.is_temporary or
                (rule.start_date <= today and rule.end_date >= today)
            )

            # Se não estiver ativa, remover da IA
            if not is_active:
                await self._remove_rule_from_ai(account_id, rule.id)
                return True

            # Obter serviços
            vector_service = await get_vector_service()
            cache_service = await get_cache_service()

            # Obter agente de embedding
            embedding_agent = await get_business_rules_agent()

            # Obter área de negócio
            business_area = await self._get_business_area(account_id)

            # Preparar coleção no Qdrant
            collection_name = f"business_rules_{account_id}"
            await vector_service.ensure_collection_exists(collection_name)

            # Preparar dados da regra para o agente
            rule_data = rule.model_dump()

            # Processar a regra usando o agente de embeddings
            processed_text = await embedding_agent.process_data(rule_data, business_area)

            # Gerar embedding do texto processado
            embedding = await vector_service.generate_embedding(processed_text)

            # Armazenar no Qdrant
            await vector_service.store_vector(
                collection_name=collection_name,
                vector_id=f"rule_{rule.id}",
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

            # Atualizar no Redis
            redis_key = f"{account_id}:ai:rules:all"
            redis_rules = await cache_service.get(redis_key) or []

            # Remover regra existente (se houver)
            redis_rules = [r for r in redis_rules if r.get("id") != rule.id]

            # Adicionar regra atualizada
            redis_rules.append(rule_data)

            # Armazenar no Redis
            await cache_service.set(
                key=redis_key,
                value=redis_rules,
                ttl=86400 * 7  # 7 dias
            )

            return True

        except Exception as e:
            logger.error(f"Failed to sync single rule: {e}")
            raise

    async def _remove_rule_from_ai(self, account_id: str, rule_id: int) -> bool:
        """
        Remove uma regra do sistema de IA.

        Args:
            account_id: ID da conta
            rule_id: ID da regra

        Returns:
            True se a remoção foi bem-sucedida
        """
        try:
            # Obter serviços
            vector_service = await get_vector_service()
            cache_service = await get_cache_service()

            # Remover do Qdrant
            collection_name = f"business_rules_{account_id}"
            await vector_service.delete_vector(
                collection_name=collection_name,
                vector_id=f"rule_{rule_id}"
            )

            # Remover do Redis
            redis_key = f"{account_id}:ai:rules:all"
            redis_rules = await cache_service.get(redis_key) or []

            # Filtrar regra
            redis_rules = [r for r in redis_rules if r.get("id") != rule_id]

            # Armazenar no Redis
            await cache_service.set(
                key=redis_key,
                value=redis_rules,
                ttl=86400 * 7  # 7 dias
            )

            return True

        except Exception as e:
            logger.error(f"Failed to remove rule from AI: {e}")
            raise

    def _convert_to_api_format(self, rule_data: Dict[str, Any]) -> BusinessRuleResponse:
        """
        Converte dados do Odoo para formato da API.

        Args:
            rule_data: Dados da regra no formato do Odoo

        Returns:
            Regra no formato da API
        """
        # Converter datas
        start_date = None
        if rule_data.get("start_date"):
            start_date = date.fromisoformat(rule_data["start_date"])

        end_date = None
        if rule_data.get("end_date"):
            end_date = date.fromisoformat(rule_data["end_date"])

        # Converter rule_data
        rule_specific_data = {}
        if rule_data.get("rule_data"):
            try:
                if isinstance(rule_data["rule_data"], str):
                    rule_specific_data = json.loads(rule_data["rule_data"])
                else:
                    rule_specific_data = rule_data["rule_data"]
            except Exception as e:
                logger.warning(f"Failed to parse rule_data: {e}")

        return BusinessRuleResponse(
            id=rule_data["id"],
            name=rule_data["name"],
            description=rule_data.get("description", ""),
            type=rule_data.get("type", RuleType.GENERAL),
            priority=rule_data.get("priority", RulePriority.MEDIUM),
            is_temporary=rule_data.get("is_temporary", False),
            start_date=start_date,
            end_date=end_date,
            rule_data=rule_specific_data,
            website=rule_data.get("website", ""),
            created_at=rule_data.get("create_date"),
            updated_at=rule_data.get("write_date"),
            sync_status=rule_data.get("sync_status", "not_synced"),
            last_sync_date=rule_data.get("last_sync_date")
        )

    def _get_rule_fields(self) -> List[str]:
        """
        Obtém a lista de campos para buscar regras.

        Returns:
            Lista de campos
        """
        return [
            "id",
            "name",
            "description",
            "type",
            "priority",
            "is_temporary",
            "start_date",
            "end_date",
            "rule_data",
            "website",
            "create_date",
            "write_date",
            "sync_status",
            "last_sync_date"
        ]

    def _validate_rule_data(self, rule_data: BusinessRuleRequest) -> None:
        """
        Valida os dados da regra.

        Args:
            rule_data: Dados da regra

        Raises:
            ValidationError: Se os dados forem inválidos
        """
        # Validações específicas por tipo de regra
        if rule_data.type == RuleType.BUSINESS_HOURS:
            if not hasattr(rule_data, 'rule_data') or not isinstance(rule_data.rule_data, dict) or 'days' not in rule_data.rule_data:
                raise ValidationError("Business hours rule must include 'days' field")

            if 'start_time' not in rule_data.rule_data or 'end_time' not in rule_data.rule_data:
                raise ValidationError("Business hours rule must include 'start_time' and 'end_time' fields")

        elif rule_data.type == RuleType.DELIVERY:
            if not hasattr(rule_data, 'rule_data') or not isinstance(rule_data.rule_data, dict) or 'min_days' not in rule_data.rule_data:
                raise ValidationError("Delivery rule must include 'min_days' field")

        elif rule_data.type == RuleType.RETURN_POLICY:
            if not hasattr(rule_data, 'rule_data') or not isinstance(rule_data.rule_data, dict) or 'days' not in rule_data.rule_data:
                raise ValidationError("Return policy rule must include 'days' field")


# Instância global do serviço
business_rules_service = BusinessRulesService()

# Função para obter o serviço
def get_business_rules_service() -> BusinessRulesService:
    """
    Obtém o serviço de regras de negócio.

    Returns:
        Instância do serviço
    """
    return business_rules_service
