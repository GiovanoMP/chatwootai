# -*- coding: utf-8 -*-

"""
Serviços para o módulo Business Rules.
"""

import logging
import json
import io
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date

from qdrant_client import models


def format_date_to_iso(date_str):
    """Converte uma string de data para o formato ISO 8601 correto.

    Args:
        date_str: String de data no formato 'YYYY-MM-DD HH:MM:SS' ou similar

    Returns:
        String de data no formato ISO 8601 ou None se a conversão falhar
    """
    if not date_str:
        return None

    try:
        # Tentar converter diretamente se já estiver em formato ISO
        if 'T' in date_str:
            datetime.fromisoformat(date_str)
            return date_str

        # Converter do formato 'YYYY-MM-DD HH:MM:SS' para ISO 8601
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return dt.isoformat()
    except (ValueError, TypeError) as e:
        # Registrar o erro para debug
        logger.error(f"Failed to convert date '{date_str}' to ISO format: {e}")
        # Tentar outros formatos comuns
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.isoformat()
        except (ValueError, TypeError):
            # Retornar None se a conversão falhar
            return None

from odoo_api.core.exceptions import ValidationError, NotFoundError
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
            # Implementação simplificada para evitar problemas de coroutine
            # Vamos focar apenas na sincronização com o Qdrant e na remoção de regras apagadas

            # 1. Sincronizar metadados da empresa
            try:
                logger.info(f"Synchronizing company metadata for account {account_id}")
                # Chamamos o método diretamente sem armazenar a coroutine
                # para evitar problemas de reutilização de coroutines
                await self.sync_company_metadata(account_id)
            except Exception as e:
                logger.error(f"Failed to sync company metadata: {e}")
                logger.exception("Detailed traceback:")

            # 2. Obter regras ativas do Odoo
            active_rule_ids = []
            permanent_rule_ids = []
            temporary_rule_ids = []
            try:
                # Criar um novo conector Odoo para regras permanentes
                odoo_permanent = await OdooConnectorFactory.create_connector(account_id)

                # Buscar regras permanentes ativas
                permanent_rule_ids = await odoo_permanent.execute_kw(
                    'business.rule.item',
                    'search',
                    [[('active', '=', True)]]
                )

                # Criar um novo conector Odoo para regras temporárias
                odoo_temporary = await OdooConnectorFactory.create_connector(account_id)

                # Buscar regras temporárias ativas
                temporary_rule_ids = await odoo_temporary.execute_kw(
                    'business.temporary.rule',
                    'search',
                    [[('active', '=', True), ('state', '=', 'active')]]
                )

                # Combinar IDs
                active_rule_ids = permanent_rule_ids + temporary_rule_ids
                logger.info(f"Found {len(active_rule_ids)} active rules in Odoo for account {account_id}")
            except Exception as e:
                logger.error(f"Failed to get active rule IDs: {e}")
                logger.exception("Detailed traceback:")
                active_rule_ids = []

            # 3. Obter regras existentes no Qdrant
            qdrant_rule_ids = []
            try:
                # Obter serviço de vetorização
                vector_service = await get_vector_service()
                collection_name = "business_rules"  # Coleção compartilhada para todos os tenants

                # Garantir que a coleção existe
                try:
                    await vector_service.ensure_collection_exists(collection_name)
                except Exception as e:
                    logger.error(f"Failed to ensure collection exists: {e}")
                    # Tentar criar a coleção diretamente
                    try:
                        vector_service.qdrant_client.create_collection(
                            collection_name=collection_name,
                            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
                        )
                        # Criar índice para account_id
                        vector_service.qdrant_client.create_payload_index(
                            collection_name=collection_name,
                            field_name="account_id",
                            field_schema=models.PayloadSchemaType.KEYWORD,
                        )
                        logger.info(f"Created collection {collection_name} directly")
                    except Exception as create_error:
                        logger.error(f"Failed to create collection directly: {create_error}")

                # Obter todos os pontos na coleção para este account_id
                try:
                    # Filtrar por account_id
                    filter_condition = models.Filter(
                        must=[
                            models.FieldCondition(
                                key="account_id",
                                match=models.MatchValue(
                                    value=account_id
                                )
                            )
                        ]
                    )

                    qdrant_points = vector_service.qdrant_client.scroll(
                        collection_name=collection_name,
                        limit=10000,  # Limite alto para obter todos os pontos
                        with_payload=True,
                        with_vectors=False,
                        scroll_filter=filter_condition  # Usar scroll_filter em vez de filter
                    )[0]  # O método scroll retorna uma tupla (pontos, next_page_offset)

                    # Extrair IDs dos pontos
                    qdrant_rule_ids = [point.id for point in qdrant_points]
                    logger.info(f"Found {len(qdrant_rule_ids)} rules in Qdrant for account {account_id}")
                except Exception as e:
                    logger.error(f"Failed to get rules from Qdrant: {e}")
                    logger.exception("Detailed traceback:")
                    qdrant_rule_ids = []
            except Exception as e:
                logger.error(f"Failed to initialize vector service: {e}")
                logger.exception("Detailed traceback:")
                qdrant_rule_ids = []

            # 4. Identificar regras a serem removidas do Qdrant (regras que existem no Qdrant mas não no Odoo)
            deleted_rule_ids = [rule_id for rule_id in qdrant_rule_ids if rule_id not in active_rule_ids]

            # 5. Remover regras excluídas do Qdrant
            if deleted_rule_ids:
                try:
                    logger.info(f"Removing {len(deleted_rule_ids)} deleted rules from Qdrant: {deleted_rule_ids}")
                    vector_service = await get_vector_service()
                    vector_service.qdrant_client.delete(
                        collection_name=collection_name,
                        points_selector=models.PointIdsList(points=deleted_rule_ids),
                        wait=True  # Aguardar a conclusão da operação
                    )
                    logger.info(f"Successfully removed {len(deleted_rule_ids)} rules from Qdrant")
                except Exception as e:
                    logger.error(f"Failed to remove deleted rules from Qdrant: {e}")
                    logger.exception("Detailed traceback:")
            else:
                logger.info(f"No deleted rules to remove from Qdrant for account {account_id}")

            # 6. Vetorizar e armazenar regras ativas no Qdrant
            vectorized_count = 0
            try:
                # Criar conectores Odoo para obter dados das regras
                odoo_permanent_data = await OdooConnectorFactory.create_connector(account_id)
                odoo_temporary_data = await OdooConnectorFactory.create_connector(account_id)

                # Processar regras permanentes
                if permanent_rule_ids:
                    permanent_rules_data = await odoo_permanent_data.execute_kw(
                        'business.rule.item',
                        'read',
                        [permanent_rule_ids],
                        {'fields': ['name', 'description', 'rule_type', 'active', 'create_date', 'write_date']}
                    )

                    for rule_data in permanent_rules_data:
                        try:
                            # Criar objeto BusinessRuleResponse
                            rule = BusinessRuleResponse(
                                id=rule_data['id'],
                                name=rule_data['name'],
                                description=rule_data.get('description', ''),
                                type=rule_data.get('rule_type', 'general'),
                                priority='medium',  # Valor padrão
                                active=rule_data.get('active', True),
                                rule_data={},  # Dados específicos da regra
                                is_temporary=False,
                                created_at=datetime.fromisoformat(rule_data['create_date']),
                                updated_at=datetime.fromisoformat(rule_data['write_date']),
                            )

                            # Preparar texto para vetorização
                            rule_text = self._prepare_rule_text_for_vectorization(rule)

                            # Gerar embedding
                            embedding = await vector_service.generate_embedding(rule_text)

                            # Armazenar no Qdrant
                            vector_service.qdrant_client.upsert(
                                collection_name=collection_name,
                                points=[
                                    models.PointStruct(
                                        id=rule.id,
                                        vector=embedding,
                                        payload={
                                            "account_id": account_id,  # Campo crucial para filtragem por tenant
                                            "rule_id": rule.id,
                                            "name": rule.name,
                                            "description": rule.description,
                                            "type": rule.type,
                                            "priority": rule.priority,
                                            "is_temporary": rule.is_temporary,
                                            "rule_data": rule.rule_data,
                                            "processed_text": rule_text,
                                            "last_updated": datetime.now().isoformat()
                                        }
                                    )
                                ],
                            )
                            vectorized_count += 1
                            logger.info(f"Vectorized permanent rule {rule.id}: {rule.name}")
                        except Exception as e:
                            logger.error(f"Failed to vectorize permanent rule {rule_data['id']}: {e}")

                # Processar regras temporárias
                if temporary_rule_ids:
                    temporary_rules_data = await odoo_temporary_data.execute_kw(
                        'business.temporary.rule',
                        'read',
                        [temporary_rule_ids],
                        {'fields': ['name', 'description', 'rule_type', 'active', 'is_temporary', 'date_start', 'date_end', 'create_date', 'write_date']}
                    )

                    for rule_data in temporary_rules_data:
                        try:
                            # Verificar se a regra é realmente temporária
                            is_temporary = rule_data.get('is_temporary', False)

                            # Processar datas de início e fim apenas se for temporária
                            start_date = None
                            end_date = None

                            if is_temporary and rule_data.get('date_start'):
                                try:
                                    # Converter string de data para objeto datetime e depois para date
                                    dt = datetime.fromisoformat(rule_data['date_start'].replace('Z', '+00:00'))
                                    start_date = dt.date()  # Extrair apenas a parte da data
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"Failed to parse start date {rule_data.get('date_start')}: {e}")

                            if is_temporary and rule_data.get('date_end'):
                                try:
                                    # Converter string de data para objeto datetime e depois para date
                                    dt = datetime.fromisoformat(rule_data['date_end'].replace('Z', '+00:00'))
                                    end_date = dt.date()  # Extrair apenas a parte da data
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"Failed to parse end date {rule_data.get('date_end')}: {e}")

                            # Definir prioridade com base no tipo de regra
                            priority = 1 if is_temporary else 3  # 1 para temporárias (máxima), 3 para permanentes

                            # Criar objeto BusinessRuleResponse
                            rule = BusinessRuleResponse(
                                id=rule_data['id'],
                                name=rule_data['name'],
                                description=rule_data.get('description', ''),
                                type=rule_data.get('rule_type', 'general'),
                                priority=priority,
                                active=rule_data.get('active', True),
                                rule_data={},  # Dados específicos da regra
                                is_temporary=is_temporary,
                                start_date=start_date,
                                end_date=end_date,
                                created_at=datetime.fromisoformat(rule_data.get('create_date', datetime.now().isoformat())),
                                updated_at=datetime.fromisoformat(rule_data.get('write_date', datetime.now().isoformat())),
                            )

                            # Preparar texto para vetorização
                            rule_text = self._prepare_rule_text_for_vectorization(rule)

                            # Gerar embedding
                            embedding = await vector_service.generate_embedding(rule_text)

                            # Armazenar no Qdrant
                            vector_service.qdrant_client.upsert(
                                collection_name=collection_name,
                                points=[
                                    models.PointStruct(
                                        id=rule.id,
                                        vector=embedding,
                                        payload={
                                            "account_id": account_id,  # Campo crucial para filtragem por tenant
                                            "rule_id": rule.id,
                                            "name": rule.name,
                                            "description": rule.description,
                                            "type": rule.type,
                                            "priority": rule.priority,
                                            "is_temporary": rule.is_temporary,
                                            "start_date": rule.start_date.isoformat() if rule.start_date else None,
                                            "end_date": rule.end_date.isoformat() if rule.end_date else None,
                                            "rule_data": rule.rule_data,
                                            "processed_text": rule_text,
                                            "last_updated": datetime.now().isoformat()
                                        }
                                    )
                                ],
                            )
                            vectorized_count += 1
                            logger.info(f"Vectorized temporary rule {rule.id}: {rule.name}")
                        except Exception as e:
                            logger.error(f"Failed to vectorize temporary rule {rule_data['id']}: {e}")

                logger.info(f"Vectorized {vectorized_count} rules for account {account_id}")
            except Exception as e:
                logger.error(f"Failed to vectorize rules: {e}")
                logger.exception("Detailed traceback:")

            # 7. Sincronizar documentos de suporte
            try:
                await self.sync_support_documents(account_id)
            except Exception as e:
                logger.error(f"Failed to sync support documents: {e}")
                logger.exception("Detailed traceback:")

            # Retornar resposta
            return BusinessRuleSyncResponse(
                permanent_rules=len([id for id in active_rule_ids if id in permanent_rule_ids]),
                temporary_rules=len([id for id in active_rule_ids if id in temporary_rule_ids]),
                vectorized_rules=vectorized_count,
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
    async def sync_support_documents(self, account_id: str) -> Dict[str, Any]:
        """
        Sincroniza documentos de suporte com o Qdrant.

        Args:
            account_id: ID da conta

        Returns:
            Resultado da sincronização
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Obter IDs dos documentos de suporte
            document_ids = await odoo.execute_kw(
                'business.support.document',
                'search',
                [[('active', '=', True)]],
                {'order': 'create_date desc'},
            )

            if not document_ids:
                logger.info(f"No support documents found for account {account_id}")
                return {"documents_vectorized": 0}

            # Obter dados dos documentos
            documents_data = await odoo.execute_kw(
                'business.support.document',
                'read',
                [document_ids],
                {'fields': ['name', 'document_type', 'content', 'attachment_ids', 'create_date', 'write_date']},
            )

            # Obter serviço de vetorização
            vector_service = await get_vector_service()
            collection_name = "support_documents"  # Coleção compartilhada para todos os tenants

            # Garantir que a coleção existe
            try:
                await vector_service.ensure_collection_exists(collection_name)
            except Exception as e:
                logger.error(f"Failed to ensure collection exists: {e}")
                # Tentar criar a coleção diretamente
                try:
                    vector_service.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
                    )
                    # Criar índice para account_id
                    vector_service.qdrant_client.create_payload_index(
                        collection_name=collection_name,
                        field_name="account_id",
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                    logger.info(f"Created collection {collection_name} directly")
                except Exception as create_error:
                    logger.error(f"Failed to create collection directly: {create_error}")
                    return {"documents_vectorized": 0, "error": str(create_error)}

            # Processar cada documento
            vectorized_count = 0
            for doc_data in documents_data:
                try:
                    # Extrair texto do documento
                    document_text = ""

                    # Se tiver conteúdo direto, usar
                    if doc_data.get('content'):
                        document_text = doc_data['content']
                    # Se tiver arquivo, extrair texto do arquivo
                    elif doc_data.get('file_data'):
                        file_data = doc_data['file_data']
                        file_name = doc_data.get('file_name', '')

                        # Decodificar dados do arquivo
                        import base64
                        file_bytes = base64.b64decode(file_data)

                        # Extrair texto com base no tipo de arquivo
                        if file_name.lower().endswith('.pdf'):
                            document_text = self._extract_text_from_pdf(file_bytes)
                        elif file_name.lower().endswith('.docx'):
                            document_text = self._extract_text_from_docx(file_bytes)
                        elif file_name.lower().endswith('.txt'):
                            document_text = file_bytes.decode('utf-8', errors='ignore')
                        else:
                            logger.warning(f"Unsupported file type: {file_name}")
                            continue

                    # Se não tiver texto, pular
                    if not document_text.strip():
                        logger.warning(f"No text extracted from document {doc_data['id']}: {doc_data['name']}")
                        continue

                    # Preparar texto para vetorização
                    processed_text = f"""Documento de Suporte: {doc_data['name']}

Tipo: {doc_data.get('document_type', '')}

Conteúdo:
{document_text}
"""

                    # Gerar embedding
                    embedding = await vector_service.generate_embedding(processed_text)

                    # Armazenar no Qdrant
                    vector_service.qdrant_client.upsert(
                        collection_name=collection_name,
                        points=[
                            models.PointStruct(
                                id=doc_data['id'],
                                vector=embedding,
                                payload={
                                    "account_id": account_id,  # Campo crucial para filtragem por tenant
                                    "document_id": doc_data['id'],
                                    "name": doc_data['name'],
                                    "document_type": doc_data.get('document_type', ''),
                                    "processed_text": processed_text,
                                    "last_updated": datetime.now().isoformat()
                                }
                            )
                        ],
                    )
                    vectorized_count += 1
                    logger.info(f"Vectorized support document {doc_data['id']}: {doc_data['name']}")
                except Exception as e:
                    logger.error(f"Failed to vectorize support document {doc_data['id']}: {e}")
                    logger.exception("Detailed traceback:")

            logger.info(f"Vectorized {vectorized_count} support documents for account {account_id}")
            return {"documents_vectorized": vectorized_count}

        except Exception as e:
            logger.error(f"Failed to sync support documents: {e}")
            logger.exception("Detailed traceback:")
            return {"documents_vectorized": 0, "error": str(e)}

    async def upload_document(self) -> DocumentResponse:
        """
        Faz upload de um documento para extração de regras de negócio.

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

    async def list_documents(self, account_id: str) -> DocumentListResponse:
        """
        Lista documentos de regras de negócio.

        Args:
            account_id: ID da conta

        Returns:
            Lista de documentos
        """
        try:
            # Obter conector Odoo
            # Chamamos o método diretamente sem armazenar a coroutine
            # para evitar problemas de reutilização de coroutines
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
            f"Tipo: {rule.type}"
        ]

        # Adicionar informações de temporalidade com contexto enriquecido
        if rule.is_temporary:
            # Formatar datas para exibição
            start_date_str = rule.start_date.strftime('%d/%m/%Y') if rule.start_date else "data não especificada"
            end_date_str = rule.end_date.strftime('%d/%m/%Y') if rule.end_date else "data não especificada"

            text_parts.append(f"REGRA TEMPORÁRIA - ALTA PRIORIDADE")
            text_parts.append(f"Válida de {start_date_str} até {end_date_str}")
            text_parts.append(f"Esta é uma regra temporária que deve ser verificada primeiro em qualquer consulta relacionada.")

            # Verificar se a regra está ativa atualmente
            now = datetime.now().date()  # Converter para date para comparar com start_date e end_date
            is_active_now = True
            if rule.start_date and rule.start_date > now:
                is_active_now = False
                text_parts.append(f"Atenção: Esta regra ainda não está ativa, ela começará a valer em {start_date_str}.")
            if rule.end_date and rule.end_date < now:
                is_active_now = False
                text_parts.append(f"Atenção: Esta regra não está mais ativa, ela expirou em {end_date_str}.")

            if is_active_now:
                text_parts.append("Esta regra está ATIVA no momento atual.")
        else:
            # Adicionar informação de que é uma regra permanente
            text_parts.append(f"REGRA PERMANENTE")
            text_parts.append("Regra permanente - aplica-se continuamente sem data de expiração.")

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

    async def _update_company_config_yaml(self, account_id: str, metadata: Dict[str, Any]) -> None:
        """
        Atualiza o arquivo YAML principal de configuração da empresa com os metadados.

        Args:
            account_id: ID da conta
            metadata: Metadados da empresa
        """
        import os
        import yaml

        try:
            # Definir o caminho do arquivo YAML
            yaml_path = f"config/domains/retail/{account_id}/config.yaml"

            # Verificar se o arquivo existe
            if not os.path.exists(yaml_path):
                logger.warning(f"Company config YAML file not found: {yaml_path}")
                # Criar diretórios se não existirem
                os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
                # Criar um arquivo de configuração vazio
                config = {}
            else:
                # Ler o arquivo YAML existente
                with open(yaml_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file) or {}

            # Garantir que o account_id está definido
            config['account_id'] = account_id

            # Adicionar informações básicas da empresa
            company_info = metadata.get('company_info', {})
            if company_info.get('company_name'):
                config['name'] = company_info.get('company_name')
            if company_info.get('description'):
                config['description'] = company_info.get('description')

            # Adicionar metadados da empresa
            if 'company_metadata' not in config:
                config['company_metadata'] = {}

            # Adicionar informações básicas
            config['company_metadata']['company_info'] = company_info

            # Adicionar horários de funcionamento
            if 'business_hours' in metadata:
                config['company_metadata']['business_hours'] = metadata['business_hours']

            # Adicionar informações de atendimento ao cliente
            if 'customer_service' in metadata:
                config['company_metadata']['customer_service'] = metadata['customer_service']

            # Adicionar informações sobre promoções
            if 'promotions' in metadata:
                config['company_metadata']['promotions'] = metadata['promotions']

            # Adicionar informações dos canais online
            if 'online_channels' in metadata:
                config['company_metadata']['online_channels'] = metadata['online_channels']

            # Salvar o arquivo YAML atualizado
            with open(yaml_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False, allow_unicode=True)

            logger.info(f"Updated company config YAML file: {yaml_path}")

        except Exception as e:
            logger.error(f"Failed to update company config YAML: {e}")
            raise

    async def _update_customer_service_yaml(self, account_id: str, customer_service_data: Dict[str, Any], online_channels: Optional[Dict[str, Any]] = None, promotions: Optional[Dict[str, Any]] = None) -> None:
        """
        Atualiza o arquivo YAML de configuração do customer service com os dados de atendimento, canais online e promoções.

        Args:
            account_id: ID da conta
            customer_service_data: Dados de atendimento ao cliente
            online_channels: Informações dos canais online (opcional)
            promotions: Informações sobre promoções (opcional)
        """
        import os
        import yaml

        try:
            # Definir o caminho do arquivo YAML
            yaml_path = f"config/domains/retail/{account_id}/crews/customer_service/config.yaml"

            # Verificar se o arquivo existe
            if not os.path.exists(yaml_path):
                logger.warning(f"Customer service YAML file not found: {yaml_path}")
                # Criar diretórios se não existirem
                os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
                # Criar um arquivo de configuração vazio
                config = {}
            else:
                # Ler o arquivo YAML existente
                with open(yaml_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file) or {}

            # Atualizar as configurações de estilo
            if 'style' not in config:
                config['style'] = {}

            # Atualizar a saudação
            if 'greeting' not in config['style']:
                config['style']['greeting'] = {}

            config['style']['greeting']['enabled'] = True
            if customer_service_data.get('greeting_message'):
                config['style']['greeting']['message'] = customer_service_data['greeting_message']

            # Atualizar o estilo de comunicação
            if 'tone' not in config['style']:
                config['style']['tone'] = {}

            # Mapear o estilo de comunicação para os níveis de formalidade, amigabilidade e técnico
            style_map = {
                'formal': {'formal': 5, 'friendly': 2, 'technical': 3},
                'casual': {'formal': 2, 'friendly': 4, 'technical': 2},
                'friendly': {'formal': 2, 'friendly': 5, 'technical': 2},
                'technical': {'formal': 4, 'friendly': 2, 'technical': 5}
            }

            style = customer_service_data.get('communication_style', 'friendly')
            if style in style_map:
                config['style']['tone'] = style_map[style]

            # Atualizar o uso de emojis
            if 'emojis' not in config['style']:
                config['style']['emojis'] = {}

            emoji_usage = customer_service_data.get('emoji_usage', 'moderate')
            config['style']['emojis']['enabled'] = emoji_usage != 'none'
            config['style']['emojis']['frequency'] = emoji_usage if emoji_usage != 'none' else 'minimal'

            # Adicionar informações dos canais online
            if online_channels:
                if 'online_channels' not in config:
                    config['online_channels'] = {}

                # Site
                website = online_channels.get('website', {})
                if website and website.get('url'):
                    config['online_channels']['website'] = {
                        'url': website.get('url', ''),
                        'mention_at_end': website.get('mention_at_end', False)
                    }

                # Facebook
                facebook = online_channels.get('facebook', {})
                if facebook and facebook.get('url'):
                    config['online_channels']['facebook'] = {
                        'url': facebook.get('url', ''),
                        'mention_at_end': facebook.get('mention_at_end', False)
                    }

                # Instagram
                instagram = online_channels.get('instagram', {})
                if instagram and instagram.get('url'):
                    config['online_channels']['instagram'] = {
                        'url': instagram.get('url', ''),
                        'mention_at_end': instagram.get('mention_at_end', False)
                    }

            # Adicionar informações sobre promoções
            if promotions:
                if 'promotions' not in config:
                    config['promotions'] = {}

                config['promotions']['inform_at_start'] = promotions.get('inform_at_start', False)

            # Salvar o arquivo YAML atualizado
            with open(yaml_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False, allow_unicode=True)

            logger.info(f"Updated customer service YAML file: {yaml_path}")

        except Exception as e:
            logger.error(f"Failed to update customer service YAML: {e}")
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
            # Usar o cache para evitar chamadas repetidas
            cache = await get_cache_service()
            cache_key = f"{account_id}:business_area"

            # Verificar se a área de negócio está em cache
            cached_area = await cache.get(cache_key)
            if cached_area is not None:
                return cached_area

            # Criar um novo conector Odoo para cada chamada
            # Chamamos o método diretamente sem armazenar a coroutine
            # para evitar problemas de reutilização de coroutines
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
                # Armazenar None no cache para evitar chamadas repetidas
                await cache.set(cache_key, "general", ttl=3600)  # 1 hora
                return "general"  # Valor padrão

            company_settings = await odoo_connector.execute_kw(
                'business.rules',
                'read',
                [company_settings_ids],
                {'fields': ['business_area', 'business_area_other']}
            )

            business_area = "general"  # Valor padrão

            if company_settings and len(company_settings) > 0:
                business_model = company_settings[0].get("business_area")

                # Se for "other", usar o campo business_area_other
                if business_model == "other":
                    business_area = company_settings[0].get("business_area_other") or "general"
                elif business_model:
                    business_area = business_model

            # Armazenar em cache para evitar chamadas repetidas
            await cache.set(cache_key, business_area, ttl=3600)  # 1 hora
            return business_area

        except Exception as e:
            logger.warning(f"Failed to get business area for account {account_id}: {e}")
            return "general"  # Valor padrão em caso de erro

    async def sync_company_metadata(self, account_id: str) -> Dict[str, Any]:
        """
        Sincroniza metadados gerais da empresa com o Qdrant.

        Args:
            account_id: ID da conta

        Returns:
            Metadados sincronizados
        """
        try:
            # Criar um novo conector Odoo para cada chamada
            # Chamamos o método diretamente sem armazenar a coroutine
            # para evitar problemas de reutilização de coroutines
            odoo = await OdooConnectorFactory.create_connector(account_id)

            # Obter ID da regra de negócio principal
            business_rule_ids = await odoo.execute_kw(
                'business.rules',
                'search',
                [[]],
                {'limit': 1},
            )

            if not business_rule_ids:
                logger.warning(f"No business rule found for account {account_id}")
                return {}

            # Obter todos os dados da regra de negócio principal
            business_rule_data = await odoo.execute_kw(
                'business.rules',
                'read',
                [business_rule_ids],
                # Não especificar campos para obter todos os campos disponíveis
            )

            if not business_rule_data or not business_rule_data[0]:
                logger.warning(f"Failed to get business rule data for account {account_id}")
                return {}

            business_rule_data = business_rule_data[0]
            logger.info(f"Company metadata for account {account_id}: {json.dumps(business_rule_data, default=str)}")

            # Extrair metadados relevantes
            metadata = {}

            # Informações básicas da empresa
            metadata['company_info'] = {
                'company_name': business_rule_data.get('name', ''),
                'description': business_rule_data.get('description', ''),
                'company_values': business_rule_data.get('company_values', ''),
                'business_area': business_rule_data.get('business_area', ''),
                'business_area_other': business_rule_data.get('business_area_other', ''),
            }

            # Informações dos canais online
            metadata['online_channels'] = {
                'website': {
                    'url': business_rule_data.get('website', ''),
                    'mention_at_end': business_rule_data.get('mention_website_at_end', False),
                },
                'facebook': {
                    'url': business_rule_data.get('facebook_url', ''),
                    'mention_at_end': business_rule_data.get('mention_facebook_at_end', False),
                },
                'instagram': {
                    'url': business_rule_data.get('instagram_url', ''),
                    'mention_at_end': business_rule_data.get('mention_instagram_at_end', False),
                }
            }

            # Converter horas float para formato HH:MM
            def float_to_time(hours_float):
                if hours_float is False or hours_float is None:
                    return "00:00"
                hours = int(hours_float)
                minutes = int((hours_float - hours) * 60)
                return f"{hours:02d}:{minutes:02d}"

            # Horários de funcionamento
            days = []
            if business_rule_data.get('monday'):
                days.append(0)  # Segunda-feira
            if business_rule_data.get('tuesday'):
                days.append(1)  # Terça-feira
            if business_rule_data.get('wednesday'):
                days.append(2)  # Quarta-feira
            if business_rule_data.get('thursday'):
                days.append(3)  # Quinta-feira
            if business_rule_data.get('friday'):
                days.append(4)  # Sexta-feira
            if business_rule_data.get('saturday'):
                days.append(5)  # Sábado
            if business_rule_data.get('sunday'):
                days.append(6)  # Domingo

            metadata['business_hours'] = {
                'days': days,
                'start_time': float_to_time(business_rule_data.get('business_hours_start', 8.0)),
                'end_time': float_to_time(business_rule_data.get('business_hours_end', 18.0)),
                'saturday_start_time': float_to_time(business_rule_data.get('saturday_hours_start', 8.0)),
                'saturday_end_time': float_to_time(business_rule_data.get('saturday_hours_end', 12.0)),
                'has_lunch_break': business_rule_data.get('has_lunch_break', False),
                'lunch_break_start': float_to_time(business_rule_data.get('lunch_break_start', 12.0)),
                'lunch_break_end': float_to_time(business_rule_data.get('lunch_break_end', 13.0)),
            }

            # Informações de atendimento ao cliente
            metadata['customer_service'] = {
                'greeting_message': business_rule_data.get('greeting_message', ''),
                'communication_style': business_rule_data.get('communication_style', 'friendly'),
                'emoji_usage': business_rule_data.get('emoji_usage', 'moderate'),
            }

            # Informações sobre promoções
            metadata['promotions'] = {
                'inform_at_start': business_rule_data.get('inform_promotions_at_start', False),
            }

            # Atualizar o arquivo YAML de configuração do customer service
            try:
                # Criar uma cópia dos dados para evitar problemas de referência
                customer_service_data = dict(metadata['customer_service'])
                online_channels_data = dict(metadata['online_channels'])
                promotions_data = dict(metadata['promotions'])

                await self._update_customer_service_yaml(
                    account_id=account_id,
                    customer_service_data=customer_service_data,
                    online_channels=online_channels_data,
                    promotions=promotions_data
                )
                logger.info(f"Updated customer service YAML for account {account_id}")
            except Exception as e:
                logger.error(f"Failed to update customer service YAML: {e}")
                # Continuar mesmo se falhar a atualização do YAML

            # Atualizar o arquivo YAML principal de configuração da empresa
            try:
                await self._update_company_config_yaml(
                    account_id=account_id,
                    metadata=metadata
                )
                logger.info(f"Updated main company config YAML for account {account_id}")
            except Exception as e:
                logger.error(f"Failed to update main company config YAML: {e}")
                # Continuar mesmo se falhar a atualização do YAML

            # Obter uma nova instância do serviço de vetorização
            # Isso evita reutilizar coroutines já aguardadas
            vector_service = await get_vector_service()
            collection_name = "company_metadata"  # Coleção compartilhada para todos os tenants

            # Garantir que a coleção existe
            try:
                await vector_service.ensure_collection_exists(collection_name)
            except Exception as e:
                logger.error(f"Failed to ensure collection exists: {e}")
                # Tentar criar a coleção diretamente se o método falhar
                try:
                    vector_service.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
                    )
                    # Criar índice para account_id
                    vector_service.qdrant_client.create_payload_index(
                        collection_name=collection_name,
                        field_name="account_id",
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                    logger.info(f"Created collection {collection_name} directly")
                except Exception as create_error:
                    logger.error(f"Failed to create collection directly: {create_error}")
                    # Continuar mesmo se falhar a criação da coleção

            # Importar o agente de metadados da empresa
            from odoo_api.embedding_agents.business_rules import get_company_metadata_agent

            # Obter a área de negócio da empresa
            business_area = await self._get_business_area(account_id)

            # Obter o agente de metadados da empresa
            company_metadata_agent = await get_company_metadata_agent()

            # Texto original para armazenamento
            original_text = self._format_company_metadata(metadata)

            # Processar metadados usando o agente
            try:
                processed_text = await company_metadata_agent.process_data(metadata, business_area)
                logger.info(f"Processed company metadata for account {account_id} using company metadata agent")
            except Exception as agent_error:
                logger.error(f"Failed to process company metadata with agent: {agent_error}")
                # Usar o texto original como fallback
                processed_text = original_text

            # Gerar embedding do texto processado
            try:
                embedding = await vector_service.generate_embedding(processed_text)

                # Gerar um ID único para o documento baseado no account_id
                # Isso permite atualizar o documento existente em vez de criar duplicatas
                # Usar UUID para garantir compatibilidade com o Qdrant
                import uuid
                document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{account_id}_metadata"))

                # Armazenar no Qdrant
                vector_service.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=[
                        models.PointStruct(
                            id=document_id,  # ID baseado no account_id
                            vector=embedding,
                            payload={
                                "account_id": account_id,  # Campo crucial para filtragem por tenant
                                "metadata": metadata,
                                "original_text": original_text,
                                "processed_text": processed_text,
                                "ai_processed": original_text != processed_text,  # Indica se os metadados foram processados pelo agente
                                "last_updated": datetime.now().isoformat()
                            }
                        )
                    ],
                )
                logger.info(f"Stored company metadata in Qdrant for account {account_id}")
            except Exception as e:
                logger.error(f"Failed to generate embedding or store in Qdrant: {e}")
                # Continuar mesmo se falhar a vetorização

            logger.info(f"Synchronized company metadata for account {account_id}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to sync company metadata: {e}")
            logger.exception("Detailed traceback:")
            return {}

    def _format_company_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Formata os metadados da empresa em texto legível para o agente de embeddings.

        Args:
            metadata: Metadados da empresa

        Returns:
            Texto formatado
        """
        formatted_text = """
        Informações Gerais da Empresa
        """

        # Informações básicas da empresa
        company_info = metadata.get('company_info', {})
        formatted_text += f"""
        Nome da empresa: {company_info.get('company_name', 'N/A')}
        Website: {company_info.get('website', 'N/A')}
        Descrição: {company_info.get('description', 'N/A')}
        Valores da empresa: {company_info.get('company_values', 'N/A')}
        Área de negócio: {company_info.get('business_area', 'N/A')}
        """

        # Horários de funcionamento
        business_hours = metadata.get('business_hours', {})
        days_map = {
            0: "Segunda-feira",
            1: "Terça-feira",
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo"
        }

        days = business_hours.get('days', [])
        days_text = ", ".join([days_map.get(day, str(day)) for day in days])

        formatted_text += f"""
        Horário de Funcionamento:
        Dias de funcionamento: {days_text}
        Horário de funcionamento: {business_hours.get('start_time', 'N/A')} até {business_hours.get('end_time', 'N/A')}
        """

        if 5 in days:  # Se sábado está incluído
            formatted_text += f"Horário de sábado: {business_hours.get('saturday_start_time', 'N/A')} até {business_hours.get('saturday_end_time', 'N/A')}\n"

        if business_hours.get('has_lunch_break'):
            formatted_text += f"Intervalo de almoço: {business_hours.get('lunch_break_start', 'N/A')} até {business_hours.get('lunch_break_end', 'N/A')}\n"

        # Informações de atendimento ao cliente
        customer_service = metadata.get('customer_service', {})
        formatted_text += f"""
        Atendimento ao Cliente:
        Saudação: {customer_service.get('greeting_message', 'N/A')}
        Estilo de comunicação: {customer_service.get('communication_style', 'N/A')}
        Uso de emojis: {customer_service.get('emoji_usage', 'N/A')}
        """

        # Informações sobre promoções
        promotions = metadata.get('promotions', {})
        formatted_text += f"""

        Promoções:
        Informar sobre promoções no início da conversa: {'Sim' if promotions.get('inform_at_start', False) else 'Não'}
        """

        # Informações dos canais online
        if "online_channels" in metadata:
            online_channels = metadata["online_channels"]
            formatted_text += f"""

            Canais Online da Empresa:
            """

            # Site
            website = online_channels.get('website', {})
            if website.get('url'):
                formatted_text += f"""
            Site: {website.get('url', 'N/A')}
            Mencionar site ao finalizar: {'Sim' if website.get('mention_at_end', False) else 'Não'}
            """

            # Facebook
            facebook = online_channels.get('facebook', {})
            if facebook.get('url'):
                formatted_text += f"""
            Facebook: {facebook.get('url', 'N/A')}
            Mencionar Facebook ao finalizar: {'Sim' if facebook.get('mention_at_end', False) else 'Não'}
            """

            # Instagram
            instagram = online_channels.get('instagram', {})
            if instagram.get('url'):
                formatted_text += f"""
            Instagram: {instagram.get('url', 'N/A')}
            Mencionar Instagram ao finalizar: {'Sim' if instagram.get('mention_at_end', False) else 'Não'}
            """




        return formatted_text

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
            rules_collection_name = "business_rules"  # Coleção compartilhada para todos os tenants
            metadata_collection_name = "company_metadata"  # Coleção compartilhada para todos os tenants

            # Verificar se as coleções existem
            collections = vector_service.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            # Verificar se as coleções existem e criar se necessário
            for collection_name in [rules_collection_name, metadata_collection_name]:
                if collection_name not in collection_names:
                    logger.info(f"Collection {collection_name} not found. Creating it.")
                    try:
                        await vector_service.ensure_collection_exists(collection_name)
                    except Exception as e:
                        logger.error(f"Failed to create collection {collection_name}: {e}")
                        # Continuar mesmo se falhar a criação da coleção

            # Sincronizar dados se necessário
            # Verificar se há dados para este account_id nas coleções
            account_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            )

            # Verificar se há metadados da empresa
            metadata_points = vector_service.qdrant_client.scroll(
                collection_name=metadata_collection_name,
                scroll_filter=account_filter,  # Usar scroll_filter em vez de filter
                limit=1,
                with_payload=False,
                with_vectors=False,
            )[0]

            if not metadata_points:
                # Se não houver metadados, sincronizar
                logger.info(f"No metadata found for account {account_id}. Syncing data.")
                await self.sync_business_rules(account_id)

            # Gerar embedding para a consulta
            query_embedding = await vector_service.generate_embedding(query)

            # Preparar filtro para buscar apenas regras deste account_id
            account_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            )

            # Buscar regras semanticamente similares
            rules_results = vector_service.qdrant_client.search(
                collection_name=rules_collection_name,
                query_vector=query_embedding,
                query_filter=account_filter,  # Usar query_filter em vez de filter
                limit=limit,
                score_threshold=score_threshold
            )

            # Buscar metadados da empresa semanticamente similares
            try:
                # Usar o mesmo filtro de account_id
                metadata_results = vector_service.qdrant_client.search(
                    collection_name=metadata_collection_name,
                    query_vector=query_embedding,
                    query_filter=account_filter,  # Usar query_filter em vez de filter
                    limit=1,  # Apenas um resultado, pois só há um documento de metadados por account_id
                    score_threshold=score_threshold
                )
            except Exception as e:
                logger.warning(f"Failed to search company metadata: {e}")
                metadata_results = []

            # Extrair regras dos resultados
            relevant_rules = []

            # Adicionar metadados da empresa se forem relevantes para a consulta
            if metadata_results and len(metadata_results) > 0:
                metadata_result = metadata_results[0]
                metadata = metadata_result.payload.get("metadata", {})

                # Criar uma regra virtual para os metadados da empresa
                relevant_rules.append({
                    "rule_id": 0,  # ID especial para metadados da empresa
                    "name": "Informações Gerais da Empresa",
                    "description": "Metadados gerais da empresa, incluindo horários de funcionamento e políticas de atendimento",
                    "type": "company_metadata",
                    "priority": 1,
                    "is_temporary": False,
                    "rule_data": metadata,
                    "similarity_score": metadata_result.score
                })

            # Adicionar regras específicas
            for result in rules_results:
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

            # Ordenar por pontuação de similaridade
            relevant_rules.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Limitar o número de resultados
            return relevant_rules[:limit]

        except Exception as e:
            logger.error(f"Failed to search business rules: {e}")
            return []




    async def sync_support_documents_with_data(
        self,
        account_id: str,
        business_rule_id: int,
        documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Sincroniza documentos de suporte específicos com o sistema de IA.

        Args:
            account_id: ID da conta
            business_rule_id: ID da regra de negócio
            documents: Lista de documentos de suporte

        Returns:
            Resultado da sincronização
        """
        try:
            # Obter serviço de vetorização
            vector_service = await get_vector_service()
            collection_name = "support_documents"  # Coleção compartilhada para todos os tenants

            # Garantir que a coleção existe
            try:
                await vector_service.ensure_collection_exists(collection_name)
            except Exception as e:
                logger.error(f"Failed to ensure collection exists: {e}")
                # Tentar criar a coleção diretamente se o método falhar
                try:
                    vector_service.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
                    )
                    # Criar índice para account_id
                    vector_service.qdrant_client.create_payload_index(
                        collection_name=collection_name,
                        field_name="account_id",
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                    logger.info(f"Created collection {collection_name} directly")
                except Exception as create_error:
                    logger.error(f"Failed to create collection directly: {create_error}")
                    # Continuar mesmo se falhar a criação da coleção

            # Processar cada documento
            synced_docs = []
            for doc in documents:
                doc_id = doc.get("id")
                doc_name = doc.get("name")
                doc_type = doc.get("document_type")
                doc_content = doc.get("content")

                if not doc_id or not doc_name or not doc_content:
                    logger.warning(f"Skipping document with missing data: {doc}")
                    continue

                # Importar o agente de documentos de suporte
                from odoo_api.embedding_agents.business_rules import get_support_document_agent

                # Obter a área de negócio da empresa
                business_area = await self._get_business_area(account_id)

                # Obter o agente de documentos de suporte
                support_doc_agent = await get_support_document_agent()

                # Processar o documento usando o agente
                document_data = {
                    "id": doc_id,
                    "name": doc_name,
                    "document_type": doc_type,
                    "content": doc_content
                }

                # Texto original para armazenamento
                original_text = f"""Documento de Suporte ao Cliente

Nome: {doc_name}
Tipo: {doc_type}

Conteúdo:
{doc_content}
"""

                # Processar texto do documento usando o agente
                try:
                    processed_text = await support_doc_agent.process_data(document_data, business_area)
                    logger.info(f"Processed document {doc_id} using support document agent")
                except Exception as agent_error:
                    logger.error(f"Failed to process document with agent: {agent_error}")
                    # Usar o texto original como fallback
                    processed_text = original_text

                # Gerar embedding do texto processado
                try:
                    embedding = await vector_service.generate_embedding(processed_text)

                    # Gerar um ID único para o documento usando UUID
                    import uuid
                    document_id = str(uuid.uuid4())

                    # Armazenar no Qdrant
                    vector_service.qdrant_client.upsert(
                        collection_name=collection_name,
                        points=[
                            models.PointStruct(
                                id=document_id,  # ID baseado no account_id e doc_id
                                vector=embedding,
                                payload={
                                    "account_id": account_id,  # Campo crucial para filtragem por tenant
                                    "business_rule_id": business_rule_id,
                                    "document_id": doc_id,
                                    "name": doc_name,
                                    "document_type": doc_type,
                                    "content": doc_content,
                                    "original_text": original_text,
                                    "processed_text": processed_text,
                                    "ai_processed": original_text != processed_text,  # Indica se o documento foi processado pelo agente
                                    "last_updated": datetime.now().isoformat()
                                }
                            )
                        ],
                    )
                    logger.info(f"Stored support document in Qdrant: {doc_name} (ID: {doc_id})")
                    synced_docs.append(str(doc_id))
                except Exception as e:
                    logger.error(f"Failed to generate embedding or store document in Qdrant: {e}")
                    # Continuar com o próximo documento

            logger.info(f"Synchronized {len(synced_docs)} support documents for account {account_id}")
            return {
                "success": True,
                "synced_docs": synced_docs,
                "total": len(synced_docs)
            }

        except Exception as e:
            logger.error(f"Failed to sync support documents: {e}")
            logger.exception("Detailed traceback:")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_processed_support_document(self, account_id: str, document_id: int) -> Dict[str, Any]:
        """
        Obtém um documento de suporte processado pelo sistema de IA.

        Args:
            account_id: ID da conta
            document_id: ID do documento

        Returns:
            Documento processado
        """
        try:
            # Obter serviço de vetorização
            vector_service = await get_vector_service()
            collection_name = "support_documents"  # Coleção compartilhada para todos os tenants

            # Filtrar por account_id e document_id
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    ),
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(
                            value=document_id
                        )
                    )
                ]
            )

            # Buscar documento no Qdrant
            points = vector_service.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
                limit=1,
                with_payload=True,
                with_vectors=False,
            )[0]

            if not points:
                logger.warning(f"Document {document_id} not found for account {account_id}")
                return {
                    "found": False,
                    "message": "Document not found"
                }

            # Extrair dados do documento
            document = points[0].payload

            # Construir resposta
            return {
                "found": True,
                "document": {
                    "id": document.get("document_id"),
                    "name": document.get("name"),
                    "document_type": document.get("document_type"),
                    "original_content": document.get("content"),
                    "original_text": document.get("original_text"),
                    "processed_text": document.get("processed_text"),
                    "ai_processed": document.get("ai_processed", False),
                    "last_updated": document.get("last_updated")
                }
            }

        except Exception as e:
            logger.error(f"Failed to get processed support document: {e}")
            logger.exception("Detailed traceback:")
            return {
                "found": False,
                "error": str(e)
            }

    async def get_all_processed_support_documents(self, account_id: str) -> Dict[str, Any]:
        """
        Obtém todos os documentos de suporte processados pelo sistema de IA para uma conta.

        Args:
            account_id: ID da conta

        Returns:
            Lista de documentos processados
        """
        try:
            # Obter serviço de vetorização
            vector_service = await get_vector_service()
            collection_name = "support_documents"  # Coleção compartilhada para todos os tenants

            # Filtrar por account_id
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            )

            # Buscar documentos no Qdrant
            points = vector_service.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
                limit=100,  # Limite razoável para documentos
                with_payload=True,
                with_vectors=False,
            )[0]

            if not points:
                logger.warning(f"No support documents found for account {account_id}")
                return {
                    "found": False,
                    "message": "No support documents found"
                }

            # Extrair dados dos documentos
            documents = []
            for point in points:
                document = point.payload
                documents.append({
                    "id": document.get("document_id"),
                    "name": document.get("name"),
                    "document_type": document.get("document_type"),
                    "description": document.get("description", ""),
                    "processed_text": document.get("processed_text"),
                    "ai_processed": document.get("ai_processed", False),
                    "last_updated": document.get("last_updated")
                })

            # Construir resposta
            return {
                "found": True,
                "documents": documents,
                "total": len(documents)
            }

        except Exception as e:
            logger.error(f"Failed to get all processed support documents: {e}")
            logger.exception("Detailed traceback:")
            return {
                "found": False,
                "error": str(e)
            }

    async def get_processed_company_metadata(self, account_id: str) -> Dict[str, Any]:
        """
        Obtém os metadados da empresa processados pelo sistema de IA.

        Args:
            account_id: ID da conta

        Returns:
            Metadados processados
        """
        try:
            # Obter serviço de vetorização
            vector_service = await get_vector_service()
            collection_name = "company_metadata"  # Coleção compartilhada para todos os tenants

            # Filtrar por account_id
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            )

            # Buscar metadados no Qdrant
            points = vector_service.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
                limit=1,
                with_payload=True,
                with_vectors=False,
            )[0]

            if not points:
                logger.warning(f"Company metadata not found for account {account_id}")
                return {
                    "found": False,
                    "message": "Company metadata not found"
                }

            # Extrair dados dos metadados
            metadata = points[0].payload

            # Construir resposta
            return {
                "found": True,
                "metadata": {
                    "company_info": metadata.get("metadata", {}).get("company_info", {}),
                    "business_hours": metadata.get("metadata", {}).get("business_hours", {}),
                    "online_channels": metadata.get("metadata", {}).get("online_channels", {}),
                    "customer_service": metadata.get("metadata", {}).get("customer_service", {}),
                    "promotions": metadata.get("metadata", {}).get("promotions", {}),
                    "original_text": metadata.get("original_text", ""),
                    "processed_text": metadata.get("processed_text", ""),
                    "ai_processed": metadata.get("ai_processed", False),
                    "last_updated": metadata.get("last_updated")
                }
            }

        except Exception as e:
            logger.error(f"Failed to get processed company metadata: {e}")
            logger.exception("Detailed traceback:")
            return {
                "found": False,
                "error": str(e)
            }

    async def get_processed_service_config(self, account_id: str) -> Dict[str, Any]:
        """
        Obtém as configurações de atendimento processadas pelo sistema de IA.

        Args:
            account_id: ID da conta

        Returns:
            Configurações de atendimento processadas
        """
        try:
            # Obter os metadados da empresa, que incluem as configurações de atendimento
            metadata_result = await self.get_processed_company_metadata(account_id)

            if not metadata_result.get("found", False):
                return {
                    "found": False,
                    "message": "Service configurations not found"
                }

            # Extrair apenas as configurações de atendimento
            metadata = metadata_result.get("metadata", {})
            customer_service = metadata.get("customer_service", {})
            business_hours = metadata.get("business_hours", {})
            online_channels = metadata.get("online_channels", {})

            # Construir resposta específica para configurações de atendimento
            return {
                "found": True,
                "service_config": {
                    "customer_service": customer_service,
                    "business_hours": business_hours,
                    "online_channels": online_channels,
                    "last_updated": metadata.get("last_updated")
                }
            }

        except Exception as e:
            logger.error(f"Failed to get processed service config: {e}")
            logger.exception("Detailed traceback:")
            return {
                "found": False,
                "error": str(e)
            }

    async def get_processed_scheduling_rules(self, account_id: str) -> Dict[str, Any]:
        """
        Obtém as regras de agendamento processadas pelo sistema de IA.

        Args:
            account_id: ID da conta

        Returns:
            Regras de agendamento processadas
        """
        try:
            # Obter serviço de vetorização
            vector_service = await get_vector_service()
            collection_name = "business_rules"  # Coleção compartilhada para todos os tenants

            # Filtrar por account_id e tipo de regra (agendamento)
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    ),
                    models.FieldCondition(
                        key="type",
                        match=models.MatchValue(
                            value="scheduling"
                        )
                    )
                ]
            )

            # Buscar regras no Qdrant
            points = vector_service.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
                limit=50,  # Limite razoável para regras
                with_payload=True,
                with_vectors=False,
            )[0]

            if not points:
                logger.warning(f"No scheduling rules found for account {account_id}")
                return {
                    "found": False,
                    "message": "No scheduling rules found"
                }

            # Extrair dados das regras
            rules = []
            for point in points:
                rule = point.payload
                rules.append({
                    "id": rule.get("rule_id"),
                    "name": rule.get("name"),
                    "description": rule.get("description", ""),
                    "priority": rule.get("priority"),
                    "is_temporary": rule.get("is_temporary", False),
                    "start_date": rule.get("start_date"),
                    "end_date": rule.get("end_date"),
                    "rule_data": rule.get("rule_data", {}),
                    "processed_text": rule.get("processed_text"),
                    "last_updated": rule.get("last_updated")
                })

            # Construir resposta
            return {
                "found": True,
                "scheduling_rules": rules,
                "total": len(rules)
            }

        except Exception as e:
            logger.error(f"Failed to get processed scheduling rules: {e}")
            logger.exception("Detailed traceback:")
            return {
                "found": False,
                "error": str(e)
            }

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
