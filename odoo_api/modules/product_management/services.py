# -*- coding: utf-8 -*-

"""
Serviços para o módulo Product Management.
"""

import logging
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import ValidationError, NotFoundError, OdooOperationError
from odoo_api.core.odoo_connector import OdooConnector, OdooConnectorFactory
from odoo_api.services.cache_service import get_cache_service
from odoo_api.services.vector_service import get_vector_service
from odoo_api.modules.semantic_product.services import get_semantic_product_service
from odoo_api.modules.product_management.schemas import (
    ProductBatchSyncOptions,
    ProductSyncResult,
    ProductBatchSyncResponse,
    PriceAdjustment,
    PriceUpdateResult,
    PriceUpdateResponse,
    SyncStatus,
    SyncStatusResponse,
    ProductFilter,
    ProductInfo,
    ProductListResponse,
)

logger = logging.getLogger(__name__)

class ProductManagementService:
    """Serviço para o módulo Product Management."""
    
    async def sync_products_batch(
        self,
        account_id: str,
        product_ids: List[int],
        options: ProductBatchSyncOptions = None,
    ) -> ProductBatchSyncResponse:
        """
        Sincroniza múltiplos produtos com o banco de dados vetorial.
        
        Args:
            account_id: ID da conta
            product_ids: Lista de IDs de produtos
            options: Opções para sincronização
        
        Returns:
            Resposta da sincronização em massa
        
        Raises:
            ValidationError: Se os parâmetros forem inválidos
        """
        try:
            # Usar opções padrão se não fornecidas
            if options is None:
                options = ProductBatchSyncOptions()
            
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Verificar se os produtos existem
            existing_products = await odoo.execute_kw(
                "product.template",
                "search_read",
                [[["id", "in", product_ids]]],
                {"fields": ["id", "name"]},
            )
            
            existing_ids = [p["id"] for p in existing_products]
            missing_ids = [pid for pid in product_ids if pid not in existing_ids]
            
            if missing_ids:
                logger.warning(f"Produtos não encontrados: {missing_ids}")
            
            # Preparar resultados
            results = []
            successful = 0
            failed = 0
            
            # Gerar ID do job
            job_id = str(uuid.uuid4())
            
            # Obter serviço de produtos semânticos
            semantic_product_service = get_semantic_product_service()
            
            # Processar cada produto
            for product_id in existing_ids:
                try:
                    # Sincronizar produto
                    sync_result = await semantic_product_service.sync_product_to_vector_db(
                        account_id=account_id,
                        product_id=product_id,
                        description=None,  # Usar descrição existente
                        skip_odoo_update=options.skip_odoo_update,
                    )
                    
                    # Adicionar resultado
                    results.append(
                        ProductSyncResult(
                            product_id=product_id,
                            status="completed",
                            vector_id=sync_result.vector_id,
                        )
                    )
                    
                    successful += 1
                
                except Exception as e:
                    logger.error(f"Falha ao sincronizar produto {product_id}: {e}")
                    
                    # Adicionar resultado de falha
                    results.append(
                        ProductSyncResult(
                            product_id=product_id,
                            status="failed",
                            error=str(e),
                        )
                    )
                    
                    failed += 1
            
            # Adicionar produtos não encontrados como falhas
            for product_id in missing_ids:
                results.append(
                    ProductSyncResult(
                        product_id=product_id,
                        status="failed",
                        error="Produto não encontrado",
                    )
                )
                
                failed += 1
            
            # Retornar resposta
            return ProductBatchSyncResponse(
                total=len(product_ids),
                successful=successful,
                failed=failed,
                results=results,
                job_id=job_id,
            )
        
        except Exception as e:
            logger.error(f"Falha na sincronização em massa: {e}")
            raise ValidationError(f"Falha na sincronização em massa: {e}")
    
    async def update_prices_batch(
        self,
        account_id: str,
        product_ids: List[int],
        adjustment: PriceAdjustment,
    ) -> PriceUpdateResponse:
        """
        Atualiza preços de múltiplos produtos.
        
        Args:
            account_id: ID da conta
            product_ids: Lista de IDs de produtos
            adjustment: Ajuste de preço a ser aplicado
        
        Returns:
            Resposta da atualização de preços
        
        Raises:
            ValidationError: Se os parâmetros forem inválidos
        """
        try:
            # Validar tipo de ajuste
            if adjustment.type not in ["percentage", "fixed"]:
                raise ValidationError("Tipo de ajuste inválido. Use 'percentage' ou 'fixed'.")
            
            # Validar campo de preço
            if adjustment.field not in ["list_price", "ai_price"]:
                raise ValidationError("Campo de preço inválido. Use 'list_price' ou 'ai_price'.")
            
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Obter preços atuais
            current_prices = await odoo.execute_kw(
                "product.template",
                "search_read",
                [[["id", "in", product_ids]]],
                {"fields": ["id", "name", "list_price", "ai_price"]},
            )
            
            # Mapear produtos por ID
            products_map = {p["id"]: p for p in current_prices}
            
            # Preparar resultados
            results = []
            successful = 0
            failed = 0
            
            # Processar cada produto
            for product_id in product_ids:
                try:
                    if product_id not in products_map:
                        raise NotFoundError(f"Produto {product_id} não encontrado")
                    
                    product = products_map[product_id]
                    
                    # Obter preço atual
                    current_price = product.get(adjustment.field, 0.0)
                    
                    # Calcular novo preço
                    new_price = current_price
                    if adjustment.type == "percentage":
                        # Ajuste percentual (ex: -10% = multiplicar por 0.9)
                        factor = 1 + (adjustment.value / 100)
                        new_price = current_price * factor
                    else:  # fixed
                        # Ajuste fixo (ex: +5 = adicionar 5)
                        new_price = current_price + adjustment.value
                    
                    # Garantir que o preço não seja negativo
                    new_price = max(0.0, new_price)
                    
                    # Arredondar para 2 casas decimais
                    new_price = round(new_price, 2)
                    
                    # Atualizar preço no Odoo
                    await odoo.execute_kw(
                        "product.template",
                        "write",
                        [[product_id], {adjustment.field: new_price}],
                    )
                    
                    # Adicionar resultado
                    results.append(
                        PriceUpdateResult(
                            product_id=product_id,
                            old_price=current_price,
                            new_price=new_price,
                        )
                    )
                    
                    successful += 1
                
                except Exception as e:
                    logger.error(f"Falha ao atualizar preço do produto {product_id}: {e}")
                    
                    # Adicionar resultado de falha
                    results.append(
                        PriceUpdateResult(
                            product_id=product_id,
                            old_price=products_map.get(product_id, {}).get(adjustment.field, 0.0),
                            new_price=0.0,
                            error=str(e),
                        )
                    )
                    
                    failed += 1
            
            # Retornar resposta
            return PriceUpdateResponse(
                total=len(product_ids),
                successful=successful,
                failed=failed,
                results=results,
            )
        
        except Exception as e:
            logger.error(f"Falha na atualização de preços em massa: {e}")
            raise ValidationError(f"Falha na atualização de preços em massa: {e}")
    
    async def get_sync_status(
        self,
        account_id: str,
        product_ids: Optional[List[int]] = None,
    ) -> SyncStatusResponse:
        """
        Verifica o status de sincronização de produtos.
        
        Args:
            account_id: ID da conta
            product_ids: Lista de IDs de produtos (opcional, se None verifica todos)
        
        Returns:
            Status de sincronização dos produtos
        
        Raises:
            ValidationError: Se os parâmetros forem inválidos
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Construir domínio de busca
            domain = []
            if product_ids:
                domain.append(["id", "in", product_ids])
            
            # Obter produtos
            products = await odoo.execute_kw(
                "product.template",
                "search_read",
                [domain],
                {"fields": ["id", "name", "semantic_description_verified"]},
            )
            
            # Obter serviço de cache
            cache = await get_cache_service()
            
            # Preparar resultados
            results = []
            synced = 0
            not_synced = 0
            
            # Verificar status de cada produto
            for product in products:
                product_id = product["id"]
                
                # Verificar se o produto está sincronizado
                is_synced = product.get("semantic_description_verified", False)
                
                # Obter data da última sincronização do cache
                cache_key = f"{account_id}:product_sync:{product_id}"
                sync_data = await cache.get(cache_key)
                
                last_sync = None
                vector_id = None
                
                if sync_data:
                    last_sync = datetime.fromisoformat(sync_data.get("timestamp", ""))
                    vector_id = sync_data.get("vector_id")
                
                # Determinar status
                status = "synced" if is_synced else "not_synced"
                
                # Adicionar resultado
                results.append(
                    SyncStatus(
                        product_id=product_id,
                        sync_status=status,
                        last_sync=last_sync,
                        vector_id=vector_id,
                    )
                )
                
                # Contar status
                if status == "synced":
                    synced += 1
                else:
                    not_synced += 1
            
            # Retornar resposta
            return SyncStatusResponse(
                total=len(products),
                synced=synced,
                not_synced=not_synced,
                products=results,
            )
        
        except Exception as e:
            logger.error(f"Falha ao verificar status de sincronização: {e}")
            raise ValidationError(f"Falha ao verificar status de sincronização: {e}")
    
    async def list_products(
        self,
        account_id: str,
        filter: Optional[ProductFilter] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "name",
        order_dir: str = "asc",
    ) -> ProductListResponse:
        """
        Lista produtos com filtros.
        
        Args:
            account_id: ID da conta
            filter: Filtro para produtos
            limit: Limite de resultados
            offset: Offset para paginação
            order_by: Campo para ordenação
            order_dir: Direção da ordenação (asc, desc)
        
        Returns:
            Lista de produtos
        
        Raises:
            ValidationError: Se os parâmetros forem inválidos
        """
        try:
            # Validar parâmetros
            if limit < 1 or limit > 1000:
                raise ValidationError("Limite deve estar entre 1 e 1000")
            
            if offset < 0:
                raise ValidationError("Offset deve ser não-negativo")
            
            if order_dir not in ["asc", "desc"]:
                raise ValidationError("Direção de ordenação deve ser 'asc' ou 'desc'")
            
            # Validar campo de ordenação
            valid_order_fields = ["name", "default_code", "list_price", "ai_price", "create_date"]
            if order_by not in valid_order_fields:
                raise ValidationError(f"Campo de ordenação inválido. Use um dos seguintes: {', '.join(valid_order_fields)}")
            
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Construir domínio de busca
            domain = []
            
            if filter:
                if filter.category_ids:
                    domain.append(["categ_id", "in", filter.category_ids])
                
                if filter.price_range and len(filter.price_range) == 2:
                    min_price, max_price = filter.price_range
                    domain.append(["list_price", ">=", min_price])
                    domain.append(["list_price", "<=", max_price])
                
                if filter.sync_status:
                    if filter.sync_status == "synced":
                        domain.append(["semantic_description_verified", "=", True])
                    elif filter.sync_status == "not_synced":
                        domain.append(["semantic_description_verified", "=", False])
                
                if filter.search_term:
                    domain.append("|")
                    domain.append(["name", "ilike", filter.search_term])
                    domain.append(["default_code", "ilike", filter.search_term])
            
            # Contar total de produtos
            total_count = await odoo.execute_kw(
                "product.template",
                "search_count",
                [domain],
            )
            
            # Construir ordenação
            order = f"{order_by} {order_dir}"
            
            # Obter produtos
            products = await odoo.execute_kw(
                "product.template",
                "search_read",
                [domain],
                {
                    "fields": [
                        "id", "name", "default_code", "list_price", "ai_price",
                        "categ_id", "semantic_description_verified"
                    ],
                    "limit": limit,
                    "offset": offset,
                    "order": order,
                },
            )
            
            # Preparar resultados
            results = []
            
            for product in products:
                # Obter categoria
                category_id = None
                category_name = None
                
                if product.get("categ_id"):
                    category_id = product["categ_id"][0]
                    category_name = product["categ_id"][1]
                
                # Determinar status de sincronização
                sync_status = "synced" if product.get("semantic_description_verified", False) else "not_synced"
                
                # Adicionar resultado
                results.append(
                    ProductInfo(
                        product_id=product["id"],
                        name=product["name"],
                        default_code=product.get("default_code", ""),
                        list_price=product.get("list_price", 0.0),
                        ai_price=product.get("ai_price", 0.0),
                        category_id=category_id,
                        category_name=category_name,
                        sync_status=sync_status,
                        last_sync=None,  # Não temos essa informação aqui
                    )
                )
            
            # Retornar resposta
            return ProductListResponse(
                total=total_count,
                limit=limit,
                offset=offset,
                products=results,
            )
        
        except Exception as e:
            logger.error(f"Falha ao listar produtos: {e}")
            raise ValidationError(f"Falha ao listar produtos: {e}")


# Instância global do serviço
product_management_service = ProductManagementService()

# Função para obter o serviço
def get_product_management_service() -> ProductManagementService:
    """
    Obtém o serviço de gerenciamento de produtos.
    
    Returns:
        Instância do serviço
    """
    return product_management_service
