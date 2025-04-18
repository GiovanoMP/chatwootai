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
from odoo_api.embedding_agents.business_rules_agent import get_business_rules_agent
from odoo_api.core.odoo_connector import OdooConnector, OdooConnectorFactory
from odoo_api.services.cache_service import get_cache_service
from odoo_api.services.vector_service import get_vector_service
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

# Importar bibliotecas para processamento de documentos
try:
    import PyPDF2
    from docx import Document
except ImportError:
    logging.warning("PyPDF2 or python-docx not installed. Document processing will be limited.")

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

        Raises:
            ValidationError: Se os dados forem inválidos
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Validar dados da regra
            self._validate_rule_data(rule_data)

            # Preparar dados para o Odoo
            odoo_data = {
                'name': rule_data.name,
                'description': rule_data.description,
                'rule_type': rule_data.type.value,
                'priority': rule_data.priority.value,
                'active': rule_data.active,
                'rule_data': json.dumps(self._prepare_rule_data(rule_data)),
                'is_temporary': False,
            }

            # Criar regra no Odoo
            rule_id = await odoo.execute_kw(
                'business.rule',
                'create',
                [odoo_data],
            )

            # Obter regra criada
            return await self._get_rule_by_id(odoo, rule_id)

        except ValidationError:
            raise

        except Exception as e:
            logger.error(f"Failed to create business rule: {e}")
            raise ValidationError(f"Failed to create business rule: {e}")

    async def create_temporary_rule(
        self,
        account_id: str,
        rule_data: TemporaryRuleRequest,
    ) -> BusinessRuleResponse:
        """
        Cria uma nova regra de negócio temporária.

        Args:
            account_id: ID da conta
            rule_data: Dados da regra

        Returns:
            Regra criada

        Raises:
            ValidationError: Se os dados forem inválidos
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Validar dados da regra
            self._validate_rule_data(rule_data)

            # Validar datas
            today = date.today()
            if rule_data.start_date < today:
                raise ValidationError("Start date must be today or in the future")

            if rule_data.end_date < rule_data.start_date:
                raise ValidationError("End date must be after start date")

            # Preparar dados para o Odoo
            odoo_data = {
                'name': rule_data.name,
                'description': rule_data.description,
                'rule_type': rule_data.type.value,
                'priority': rule_data.priority.value,
                'active': rule_data.active,
                'rule_data': json.dumps(self._prepare_rule_data(rule_data)),
                'is_temporary': True,
                'start_date': rule_data.start_date.isoformat(),
                'end_date': rule_data.end_date.isoformat(),
            }

            # Criar regra no Odoo
            rule_id = await odoo.execute_kw(
                'business.rule',
                'create',
                [odoo_data],
            )

            # Obter regra criada
            return await self._get_rule_by_id(odoo, rule_id)

        except ValidationError:
            raise

        except Exception as e:
            logger.error(f"Failed to create temporary rule: {e}")
            raise ValidationError(f"Failed to create temporary rule: {e}")

    async def update_business_rule(
        self,
        account_id: str,
        rule_id: int,
        rule_data: Union[BusinessRuleRequest, TemporaryRuleRequest],
    ) -> BusinessRuleResponse:
        """
        Atualiza uma regra de negócio existente.

        Args:
            account_id: ID da conta
            rule_id: ID da regra
            rule_data: Dados da regra

        Returns:
            Regra atualizada

        Raises:
            NotFoundError: Se a regra não for encontrada
            ValidationError: Se os dados forem inválidos
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Verificar se a regra existe
            rule = await self._get_rule_by_id(odoo, rule_id)
            if not rule:
                raise NotFoundError(f"Business rule {rule_id} not found")

            # Validar dados da regra
            self._validate_rule_data(rule_data)

            # Preparar dados para o Odoo
            odoo_data = {
                'name': rule_data.name,
                'description': rule_data.description,
                'rule_type': rule_data.type.value,
                'priority': rule_data.priority.value,
                'active': rule_data.active,
                'rule_data': json.dumps(self._prepare_rule_data(rule_data)),
            }

            # Adicionar datas se for regra temporária
            if hasattr(rule_data, 'start_date') and hasattr(rule_data, 'end_date'):
                # Validar datas
                today = date.today()
                if rule_data.end_date < rule_data.start_date:
                    raise ValidationError("End date must be after start date")

                odoo_data.update({
                    'is_temporary': True,
                    'start_date': rule_data.start_date.isoformat(),
                    'end_date': rule_data.end_date.isoformat(),
                })

            # Atualizar regra no Odoo
            await odoo.execute_kw(
                'business.rule',
                'write',
                [[rule_id], odoo_data],
            )

            # Obter regra atualizada
            return await self._get_rule_by_id(odoo, rule_id)

        except NotFoundError:
            raise

        except ValidationError:
            raise

        except Exception as e:
            logger.error(f"Failed to update business rule: {e}")
            raise ValidationError(f"Failed to update business rule: {e}")

    async def delete_business_rule(
        self,
        account_id: str,
        rule_id: int,
    ) -> bool:
        """
        Remove uma regra de negócio.

        Args:
            account_id: ID da conta
            rule_id: ID da regra

        Returns:
            True se a regra foi removida com sucesso

        Raises:
            NotFoundError: Se a regra não for encontrada
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Verificar se a regra existe
            rule = await self._get_rule_by_id(odoo, rule_id)
            if not rule:
                raise NotFoundError(f"Business rule {rule_id} not found")

            # Remover regra do Odoo
            await odoo.execute_kw(
                'business.rule',
                'unlink',
                [[rule_id]],
            )

            # Invalidar cache
            cache = await get_cache_service()
            await cache.delete(f"{account_id}:business_rule:{rule_id}")
            await cache.delete(f"{account_id}:business_rules:active")

            return True

        except NotFoundError:
            raise

        except Exception as e:
            logger.error(f"Failed to delete business rule: {e}")
            raise ValidationError(f"Failed to delete business rule: {e}")

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
            Regra de negócio

        Raises:
            NotFoundError: Se a regra não for encontrada
        """
        try:
            # Verificar cache
            cache = await get_cache_service()
            cache_key = f"{account_id}:business_rule:{rule_id}"
            cached_rule = await cache.get(cache_key)

            if cached_rule:
                return BusinessRuleResponse(**cached_rule)

            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Obter regra do Odoo
            rule = await self._get_rule_by_id(odoo, rule_id)
            if not rule:
                raise NotFoundError(f"Business rule {rule_id} not found")

            # Armazenar em cache
            await cache.set(cache_key, rule.model_dump(), ttl=3600)  # 1 hora

            return rule

        except NotFoundError:
            raise

        except Exception as e:
            logger.error(f"Failed to get business rule: {e}")
            raise ValidationError(f"Failed to get business rule: {e}")

    async def list_business_rules(
        self,
        account_id: str,
        page: int = 1,
        page_size: int = 20,
        active_only: bool = False,
        rule_type: Optional[str] = None,
    ) -> BusinessRuleListResponse:
        """
        Lista regras de negócio.

        Args:
            account_id: ID da conta
            page: Número da página
            page_size: Tamanho da página
            active_only: Filtrar apenas regras ativas
            rule_type: Filtrar por tipo de regra

        Returns:
            Lista de regras de negócio
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Construir domínio de busca
            domain = []

            if active_only:
                domain.append(('active', '=', True))

            if rule_type:
                domain.append(('rule_type', '=', rule_type))

            # Calcular offset
            offset = (page - 1) * page_size

            # Contar total de regras
            total = await odoo.execute_kw(
                'business.rule',
                'search_count',
                [domain],
            )

            # Calcular total de páginas
            total_pages = (total + page_size - 1) // page_size

            # Obter IDs das regras
            rule_ids = await odoo.execute_kw(
                'business.rule',
                'search',
                [domain],
                {
                    'offset': offset,
                    'limit': page_size,
                    'order': 'priority desc, name',
                },
            )

            # Obter dados das regras
            rules = []
            for rule_id in rule_ids:
                rule = await self._get_rule_by_id(odoo, rule_id)
                rules.append(rule)

            return BusinessRuleListResponse(
                rules=rules,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

        except Exception as e:
            logger.error(f"Failed to list business rules: {e}")
            raise ValidationError(f"Failed to list business rules: {e}")

    async def list_active_rules(
        self,
        account_id: str,
        rule_type: Optional[str] = None,
    ) -> List[BusinessRuleResponse]:
        """
        Lista regras de negócio ativas no momento.

        Args:
            account_id: ID da conta
            rule_type: Filtrar por tipo de regra

        Returns:
            Lista de regras de negócio ativas
        """
        try:
            # Verificar cache
            cache = await get_cache_service()
            cache_key = f"{account_id}:business_rules:active"
            if rule_type:
                cache_key += f":{rule_type}"

            cached_rules = await cache.get(cache_key)
            if cached_rules:
                return [BusinessRuleResponse(**rule) for rule in cached_rules]

            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Construir domínio de busca para regras permanentes
            domain_permanent = [('active', '=', True)]
            if rule_type:
                domain_permanent.append(('rule_type', '=', rule_type))

            # Construir domínio de busca para regras temporárias
            domain_temporary = [('active', '=', True), ('state', '=', 'active')]
            if rule_type:
                domain_temporary.append(('rule_type', '=', rule_type))

            # Obter IDs das regras permanentes
            permanent_rule_ids = await odoo.execute_kw(
                'business.rule.item',  # Nome correto do modelo no Odoo
                'search',
                [domain_permanent],
                {'order': 'name'},  # Removido 'priority desc' pois o campo foi removido
            )

            # Obter IDs das regras temporárias
            temporary_rule_ids = await odoo.execute_kw(
                'business.temporary.rule',  # Nome correto do modelo no Odoo
                'search',
                [domain_temporary],
                {'order': 'name'},  # Removido 'priority desc' pois o campo foi removido
            )

            # Combinar IDs
            rule_ids = permanent_rule_ids + temporary_rule_ids

            # Obter dados das regras
            rules = []
            for rule_id in rule_ids:
                # Determinar o modelo correto com base no ID
                model_name = 'business.rule.item' if rule_id in permanent_rule_ids else 'business.temporary.rule'

                # Obter dados da regra
                rule_data = await odoo.execute_kw(
                    model_name,
                    'read',
                    [[rule_id]],
                    {'fields': [
                        'name', 'description', 'rule_type', 'active',
                        'create_date', 'write_date'
                    ]},
                )

                if rule_data and rule_data[0]:
                    rule_data = rule_data[0]

                    # Determinar se é uma regra temporária com base no modelo
                    is_temporary = model_name == 'business.temporary.rule'

                    # Obter datas de início e fim para regras temporárias
                    start_date = None
                    end_date = None

                    if is_temporary:
                        # Para regras temporárias, obter datas de início e fim
                        date_fields = await odoo.execute_kw(
                            model_name,
                            'read',
                            [[rule_id]],
                            {'fields': ['date_start', 'date_end']},
                        )

                        if date_fields and date_fields[0]:
                            date_start_str = date_fields[0].get('date_start')
                            date_end_str = date_fields[0].get('date_end')

                            if date_start_str:
                                start_date = datetime.fromisoformat(date_start_str).date()
                            if date_end_str:
                                end_date = datetime.fromisoformat(date_end_str).date()

                    # Criar objeto BusinessRuleResponse
                    rule = BusinessRuleResponse(
                        id=rule_id,
                        name=rule_data['name'],
                        description=rule_data['description'],
                        type=rule_data['rule_type'],
                        priority=1,  # Valor padrão, já que o campo foi removido
                        active=rule_data['active'],
                        rule_data={},  # Objeto vazio, já que o campo foi removido
                        is_temporary=is_temporary,
                        start_date=start_date,
                        end_date=end_date,
                        created_at=datetime.fromisoformat(rule_data['create_date']),
                        updated_at=datetime.fromisoformat(rule_data['write_date']),
                    )
                    rules.append(rule)

            # Armazenar em cache - converter datetime para string para evitar erro de serialização JSON
            rules_for_cache = []
            for rule in rules:
                rule_dict = {
                    'id': rule.id,
                    'name': rule.name,
                    'description': rule.description,
                    'type': rule.type,
                    'priority': rule.priority,
                    'active': rule.active,
                    'rule_data': rule.rule_data,
                    'is_temporary': rule.is_temporary,
                    'start_date': rule.start_date.isoformat() if rule.start_date else None,
                    'end_date': rule.end_date.isoformat() if rule.end_date else None,
                    'created_at': rule.created_at.isoformat(),
                    'updated_at': rule.updated_at.isoformat()
                }
                rules_for_cache.append(rule_dict)

            await cache.set(
                cache_key,
                rules_for_cache,
                ttl=300,  # 5 minutos
            )

            return rules

        except Exception as e:
            logger.error(f"Failed to list active rules: {e}")
            raise ValidationError(f"Failed to list active rules: {e}")

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
            # Obter regras ativas - usando uma nova chamada para evitar reutilização de coroutine
            try:
                # Obter conector Odoo
                odoo = await OdooConnectorFactory.create_connector(account_id)

                # Construir domínio de busca para regras permanentes
                domain_permanent = [('active', '=', True)]

                # Obter data atual
                today = date.today().isoformat()

                # Construir domínio de busca para regras temporárias
                domain_temporary = [
                    ('active', '=', True),
                    ('state', '=', 'active')  # Usar o campo state em vez de datas
                ]

                # Obter IDs das regras permanentes
                permanent_rule_ids = await odoo.execute_kw(
                    'business.rule.item',  # Nome correto do modelo no Odoo
                    'search',
                    [domain_permanent],
                    {'order': 'name'},  # Removido 'priority desc' pois o campo foi removido
                )

                # Obter IDs das regras temporárias
                temporary_rule_ids = await odoo.execute_kw(
                    'business.temporary.rule',  # Nome correto do modelo no Odoo
                    'search',
                    [domain_temporary],
                    {'order': 'name'},  # Removido 'priority desc' pois o campo foi removido
                )

                # Combinar IDs
                rule_ids = permanent_rule_ids + temporary_rule_ids

                # Obter dados das regras
                active_rules = []
                for rule_id in rule_ids:
                    # Obter dados da regra diretamente aqui para evitar reutilização de coroutine
                    try:
                        # Determinar o modelo correto com base no ID
                        # Assumimos que os IDs das regras permanentes vêm primeiro na lista
                        model_name = 'business.rule.item' if rule_id in permanent_rule_ids else 'business.temporary.rule'

                        # Obter dados da regra
                        rule_data = await odoo.execute_kw(
                            model_name,
                            'read',
                            [[rule_id]],
                            {'fields': [
                                'name', 'description', 'rule_type', 'active',
                                'create_date', 'write_date'
                            ]},
                        )

                        if rule_data:
                            rule_data = rule_data[0]

                            # Determinar se é uma regra temporária com base no modelo
                            is_temporary = model_name == 'business.temporary.rule'

                            # Obter datas de início e fim para regras temporárias
                            start_date = None
                            end_date = None

                            if is_temporary:
                                # Para regras temporárias, obter datas de início e fim
                                date_fields = await odoo.execute_kw(
                                    model_name,
                                    'read',
                                    [[rule_id]],
                                    {'fields': ['date_start', 'date_end']},
                                )

                                if date_fields and date_fields[0]:
                                    date_start_str = date_fields[0].get('date_start')
                                    date_end_str = date_fields[0].get('date_end')

                                    if date_start_str:
                                        start_date = datetime.fromisoformat(date_start_str).date()
                                    if date_end_str:
                                        end_date = datetime.fromisoformat(date_end_str).date()

                            # Criar objeto BusinessRuleResponse
                            rule = BusinessRuleResponse(
                                id=rule_id,
                                name=rule_data['name'],
                                description=rule_data['description'],
                                type=rule_data['rule_type'],
                                priority=1,  # Valor padrão, já que o campo foi removido
                                active=rule_data['active'],
                                rule_data={},  # Objeto vazio, já que o campo foi removido
                                is_temporary=is_temporary,
                                start_date=start_date,
                                end_date=end_date,
                                created_at=datetime.fromisoformat(rule_data['create_date']),
                                updated_at=datetime.fromisoformat(rule_data['write_date']),
                            )
                            active_rules.append(rule)
                    except Exception as e:
                        logger.error(f"Failed to get rule {rule_id}: {e}")

            except Exception as e:
                logger.error(f"Failed to get active rules: {e}")
                raise ValidationError(f"Failed to get active rules: {e}")

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
                # Converter datetime para string para evitar erro de serialização JSON
                rule_dict = {
                    'id': rule.id,
                    'name': rule.name,
                    'description': rule.description,
                    'type': rule.type,
                    'priority': rule.priority,
                    'active': rule.active,
                    'rule_data': rule.rule_data,
                    'is_temporary': rule.is_temporary,
                    'start_date': rule.start_date.isoformat() if rule.start_date else None,
                    'end_date': rule.end_date.isoformat() if rule.end_date else None,
                    'created_at': rule.created_at.isoformat(),
                    'updated_at': rule.updated_at.isoformat()
                }
                rules_by_type[rule.type].append(rule_dict)

            # Armazenar cada tipo de regra separadamente no Redis
            for rule_type, rules in rules_by_type.items():
                await cache.set(
                    f"{account_id}:ai:rules:{rule_type}",
                    rules,
                    ttl=86400,  # 24 horas
                )

            # Armazenar todas as regras juntas no Redis
            all_rules = []
            for rule in active_rules:
                # Converter datetime para string para evitar erro de serialização JSON
                rule_dict = {
                    'id': rule.id,
                    'name': rule.name,
                    'description': rule.description,
                    'type': rule.type,
                    'priority': rule.priority,
                    'active': rule.active,
                    'rule_data': rule.rule_data,
                    'is_temporary': rule.is_temporary,
                    'start_date': rule.start_date.isoformat() if rule.start_date else None,
                    'end_date': rule.end_date.isoformat() if rule.end_date else None,
                    'created_at': rule.created_at.isoformat(),
                    'updated_at': rule.updated_at.isoformat()
                }
                all_rules.append(rule_dict)

            await cache.set(
                f"{account_id}:ai:rules:all",
                all_rules,
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
                point_id = rule.id  # Usar o ID numérico diretamente
                # Não usar await aqui, pois o método não retorna uma coroutine
                vector_service.qdrant_client.upsert(
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
    async def upload_document(
        self,
        account_id: str,
        document_data: DocumentUploadRequest,
    ) -> DocumentResponse:
        """
        Faz upload de um documento para extração de regras de negócio.

        Args:
            account_id: ID da conta
            document_data: Dados do documento

        Returns:
            Documento criado
        """
        try:
            # Implementação futura
            return DocumentResponse(
                id=1,
                name="Documento de teste",
                content="Conteúdo de teste",
                created_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            raise ValidationError(f"Failed to upload document: {e}")

    async def list_documents(
        self,
        account_id: str,
    ) -> DocumentListResponse:
        """
        Lista documentos de regras de negócio.

        Args:
            account_id: ID da conta

        Returns:
            Lista de documentos
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Obter IDs dos documentos
            document_ids = await odoo.execute_kw(
                'business.rule.document',
                'search',
                [[]],
                {'order': 'create_date desc'},
            )

            # Obter dados dos documentos
            documents_data = await odoo.execute_kw(
                'business.rule.document',
                'read',
                [document_ids],
                {'fields': ['name', 'description', 'document_type', 'status', 'create_date', 'write_date']},
            )

            # Converter para objetos DocumentResponse
            documents = []
            for doc in documents_data:
                documents.append(DocumentResponse(
                    id=doc['id'],
                    name=doc['name'],
                    description=doc['description'],
                    document_type=doc['document_type'],
                    created_at=datetime.fromisoformat(doc['create_date']),
                    updated_at=datetime.fromisoformat(doc['write_date']),
                    status=doc['status'],
                ))

            return DocumentListResponse(
                documents=documents,
                total=len(documents),
            )

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise ValidationError(f"Failed to list documents: {e}")

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
            if not isinstance(rule_data.rule_data, dict) or 'days' not in rule_data.rule_data:
                raise ValidationError("Business hours rule must include 'days' field")

            if 'start_time' not in rule_data.rule_data or 'end_time' not in rule_data.rule_data:
                raise ValidationError("Business hours rule must include 'start_time' and 'end_time' fields")

        elif rule_data.type == RuleType.DELIVERY:
            if not isinstance(rule_data.rule_data, dict) or 'min_days' not in rule_data.rule_data:
                raise ValidationError("Delivery rule must include 'min_days' field")

            if 'max_days' not in rule_data.rule_data:
                raise ValidationError("Delivery rule must include 'max_days' field")

        elif rule_data.type == RuleType.PROMOTION:
            if not isinstance(rule_data.rule_data, dict) or 'name' not in rule_data.rule_data:
                raise ValidationError("Promotion rule must include 'name' field")

            if 'discount_type' not in rule_data.rule_data or 'discount_value' not in rule_data.rule_data:
                raise ValidationError("Promotion rule must include 'discount_type' and 'discount_value' fields")

    def _prepare_rule_data(self, rule_data: BusinessRuleRequest) -> Dict[str, Any]:
        """
        Prepara os dados da regra para armazenamento.

        Args:
            rule_data: Dados da regra

        Returns:
            Dados preparados
        """
        # Se rule_data.rule_data for um modelo Pydantic, converter para dict
        if hasattr(rule_data.rule_data, 'model_dump'):
            return rule_data.rule_data.model_dump()

        # Se já for um dict, retornar diretamente
        return rule_data.rule_data

    def _prepare_rule_text_for_vectorization(self, rule: BusinessRuleResponse) -> str:
        """
        Prepara o texto da regra para vetorização.

        Cria um texto rico que captura todos os aspectos importantes da regra
        para melhorar a qualidade da busca semântica.

        Args:
            rule: Regra de negócio

        Returns:
            Texto preparado para vetorização
        """
        # Iniciar com informações básicas
        text_parts = [
            f"Nome da regra: {rule.name}",
            f"Descrição: {rule.description}",
            f"Tipo: {rule.type}",
            f"Prioridade: {rule.priority}"
        ]

        # Adicionar informações de temporalidade
        if rule.is_temporary:
            text_parts.append(f"Regra temporária válida de {rule.start_date} até {rule.end_date}")
        else:
            text_parts.append("Regra permanente")

        # Adicionar dados específicos da regra
        if isinstance(rule.rule_data, dict):
            # Processar diferentes tipos de regras
            if rule.type == "business_hours":
                days = rule.rule_data.get("days", [])
                days_text = ", ".join([self._day_number_to_name(day) for day in days])
                text_parts.append(f"Dias de funcionamento: {days_text}")
                text_parts.append(f"Horário: {rule.rule_data.get('start_time', '')} até {rule.rule_data.get('end_time', '')}")
                text_parts.append(f"Fuso horário: {rule.rule_data.get('timezone', '')}")

            elif rule.type == "delivery":
                text_parts.append(f"Prazo de entrega: {rule.rule_data.get('min_days', '')} a {rule.rule_data.get('max_days', '')} dias")
                if rule.rule_data.get('free_shipping_min_value'):
                    text_parts.append(f"Frete grátis para compras acima de {rule.rule_data.get('free_shipping_min_value')}")
                if rule.rule_data.get('excluded_regions'):
                    text_parts.append(f"Regiões excluídas: {', '.join(rule.rule_data.get('excluded_regions', []))}")

            elif rule.type == "pricing":
                if rule.rule_data.get('discount_percentage'):
                    text_parts.append(f"Desconto de {rule.rule_data.get('discount_percentage')}%")
                if rule.rule_data.get('min_margin_percentage'):
                    text_parts.append(f"Margem mínima de {rule.rule_data.get('min_margin_percentage')}%")

            elif rule.type == "promotion":
                text_parts.append(f"Promoção: {rule.rule_data.get('name', '')}")
                text_parts.append(f"Descrição da promoção: {rule.rule_data.get('description', '')}")
                text_parts.append(f"Tipo de desconto: {rule.rule_data.get('discount_type', '')}")
                text_parts.append(f"Valor do desconto: {rule.rule_data.get('discount_value', '')}")
                if rule.rule_data.get('coupon_code'):
                    text_parts.append(f"Código do cupom: {rule.rule_data.get('coupon_code', '')}")

            elif rule.type == "customer_service":
                if rule.rule_data.get('greeting_message'):
                    text_parts.append(f"Mensagem de saudação: {rule.rule_data.get('greeting_message', '')}")
                if rule.rule_data.get('farewell_message'):
                    text_parts.append(f"Mensagem de despedida: {rule.rule_data.get('farewell_message', '')}")
                if rule.rule_data.get('auto_response_keywords'):
                    text_parts.append(f"Palavras-chave para resposta automática: {', '.join(rule.rule_data.get('auto_response_keywords', []))}")

            # Adicionar todos os outros campos como texto
            for key, value in rule.rule_data.items():
                if key not in ['days', 'start_time', 'end_time', 'timezone', 'min_days', 'max_days',
                              'free_shipping_min_value', 'excluded_regions', 'discount_percentage',
                              'min_margin_percentage', 'name', 'description', 'discount_type',
                              'discount_value', 'coupon_code', 'greeting_message', 'farewell_message',
                              'auto_response_keywords']:
                    if isinstance(value, (list, tuple)):
                        text_parts.append(f"{key}: {', '.join(map(str, value))}")
                    elif isinstance(value, dict):
                        text_parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
                    else:
                        text_parts.append(f"{key}: {value}")

        # Combinar todas as partes em um único texto
        return "\n".join(text_parts)

    def _day_number_to_name(self, day_number: int) -> str:
        """
        Converte número do dia da semana para nome.

        Args:
            day_number: Número do dia (0=Segunda, 6=Domingo)

        Returns:
            Nome do dia da semana
        """
        days = {
            0: "Segunda-feira",
            1: "Terça-feira",
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo"
        }
        return days.get(day_number, str(day_number))

    async def _get_business_area(self, account_id: str) -> Optional[str]:
        """
        Obtém a área de negócio da conta.

        Args:
            account_id: ID da conta

        Returns:
            Área de negócio ou None se não encontrada
        """
        try:
            # Criar um novo conector Odoo para cada chamada
            odoo_connector = await OdooConnectorFactory.create_connector(account_id)

            # Buscar configurações da empresa
            # Usar execute_kw diretamente para evitar reutilização de coroutine
            company_settings_ids = await odoo_connector.execute_kw(
                'business.rules',
                'search',
                [[]],
                {'limit': 1}
            )

            if not company_settings_ids:
                return None

            company_settings = await odoo_connector.execute_kw(
                'business.rules',
                'read',
                [company_settings_ids],
                {'fields': ['business_area', 'business_area_other']}
            )

            if company_settings and len(company_settings) > 0:
                business_model = company_settings[0].get("business_area")

                # Se for "other", usar o campo business_area_other
                if business_model == "other":
                    return company_settings[0].get("business_area_other")

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
            Regra de negócio ou None se não encontrada
        """
        # Obter dados da regra
        rule_data = await odoo.execute_kw(
            'business.rule',
            'read',
            [[rule_id]],
            {'fields': [
                'name', 'description', 'rule_type', 'priority', 'active',
                'rule_data', 'is_temporary', 'start_date', 'end_date',
                'create_date', 'write_date'
            ]},
        )

        if not rule_data:
            return None

        rule_data = rule_data[0]

        # Converter dados para BusinessRuleResponse
        try:
            rule_data_json = json.loads(rule_data.get('rule_data', '{}'))
        except:
            rule_data_json = {}

        return BusinessRuleResponse(
            id=rule_id,
            name=rule_data['name'],
            description=rule_data['description'],
            type=rule_data['rule_type'],
            priority=rule_data['priority'],
            active=rule_data['active'],
            rule_data=rule_data_json,
            is_temporary=rule_data['is_temporary'],
            start_date=date.fromisoformat(rule_data['start_date']) if rule_data.get('start_date') else None,
            end_date=date.fromisoformat(rule_data['end_date']) if rule_data.get('end_date') else None,
            created_at=datetime.fromisoformat(rule_data['create_date']),
            updated_at=datetime.fromisoformat(rule_data['write_date']),
        )

    def _extract_text_from_pdf(self, content_bytes: bytes) -> str:
        """
        Extrai texto de um arquivo PDF.

        Args:
            content_bytes: Conteúdo do arquivo em bytes

        Returns:
            Texto extraído
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""

    def _extract_text_from_docx(self, content_bytes: bytes) -> str:
        """
        Extrai texto de um arquivo DOCX.

        Args:
            content_bytes: Conteúdo do arquivo em bytes

        Returns:
            Texto extraído
        """
        try:
            doc = Document(io.BytesIO(content_bytes))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {e}")
            return ""

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

        Raises:
            ValidationError: Se ocorrer um erro na busca
        """
        try:
            # Obter serviço de vetorização
            vector_service = await get_vector_service()
            collection_name = f"business_rules_{account_id}"

            # Verificar se a coleção existe
            collections = vector_service.qdrant_client.get_collections()
            if collection_name not in [c.name for c in collections.collections]:
                # Se não existir, sincronizar regras primeiro
                logger.info(f"Collection {collection_name} not found. Syncing rules first.")
                await self.sync_business_rules(account_id)

            # Gerar embedding para a consulta
            query_embedding = await vector_service.generate_embedding(query)

            # Buscar regras semanticamente similares
            search_results = vector_service.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )

            # Extrair regras dos resultados
            relevant_rules = []
            for result in search_results:
                relevant_rules.append({
                    "rule_id": result.payload.get("rule_id"),
                    "name": result.payload.get("name"),
                    "description": result.payload.get("description"),
                    "type": result.payload.get("type"),
                    "priority": result.payload.get("priority"),
                    "is_temporary": result.payload.get("is_temporary"),
                    "rule_data": result.payload.get("rule_data"),
                    "similarity_score": result.score
                })

            return relevant_rules

        except Exception as e:
            logger.error(f"Failed to search business rules: {e}")
            return []


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
