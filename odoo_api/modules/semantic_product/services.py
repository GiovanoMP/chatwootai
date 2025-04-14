# -*- coding: utf-8 -*-

"""
Serviços para o módulo Semantic Product.
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import ValidationError, NotFoundError, OdooOperationError
from odoo_api.core.odoo_connector import OdooConnector, OdooConnectorFactory
from odoo_api.services.cache_service import get_cache_service
from odoo_api.services.vector_service import get_vector_service
from odoo_api.modules.semantic_product.schemas import (
    ProductDescriptionOptions,
    ProductDescriptionResponse,
    ProductSyncResponse,
    ProductSearchResult,
    ProductSearchResponse,
)

logger = logging.getLogger(__name__)

class SemanticProductService:
    """Serviço para o módulo Semantic Product."""
    
    async def get_product_metadata(
        self, odoo: OdooConnector, product_id: int
    ) -> Dict[str, Any]:
        """
        Obtém metadados de um produto.
        
        Args:
            odoo: Conector Odoo
            product_id: ID do produto
        
        Returns:
            Metadados do produto
        
        Raises:
            NotFoundError: Se o produto não for encontrado
        """
        try:
            # Obter dados básicos do produto
            product_data = await odoo.execute_kw(
                "product.template",
                "read",
                [[product_id]],
                {"fields": ["name", "categ_id", "description_sale", "description", "list_price", "default_code"]},
            )
            
            if not product_data:
                raise NotFoundError(f"Product {product_id} not found")
            
            product_data = product_data[0]
            
            # Obter nome da categoria
            category = {}
            if product_data.get("categ_id"):
                category = await odoo.execute_kw(
                    "product.category",
                    "read",
                    [product_data["categ_id"][0]],
                    {"fields": ["name"]},
                )
                category = category[0] if category else {}
            
            # Obter atributos e valores
            attribute_lines = await odoo.execute_kw(
                "product.template.attribute.line",
                "search_read",
                [[["product_tmpl_id", "=", product_id]]],
                {"fields": ["attribute_id", "value_ids"]},
            )
            
            attributes = []
            for attr_line in attribute_lines:
                attr_values = []
                if attr_line.get("value_ids"):
                    attr_values = await odoo.execute_kw(
                        "product.attribute.value",
                        "read",
                        [attr_line["value_ids"]],
                        {"fields": ["name"]},
                    )
                    attr_values = [v["name"] for v in attr_values]
                
                attributes.append({
                    "name": attr_line["attribute_id"][1],
                    "values": attr_values,
                })
            
            # Obter campos de descrição semântica
            semantic_fields = await odoo.execute_kw(
                "product.template",
                "read",
                [[product_id]],
                {"fields": ["semantic_description", "key_features", "use_cases", "ai_generated_description", "semantic_description_verified"]},
            )
            
            semantic_fields = semantic_fields[0] if semantic_fields else {}
            
            # Preparar metadados
            metadata = {
                "id": product_id,
                "name": product_data.get("name", ""),
                "default_code": product_data.get("default_code", ""),
                "category": category.get("name", ""),
                "list_price": product_data.get("list_price", 0.0),
                "description_sale": product_data.get("description_sale", ""),
                "description": product_data.get("description", ""),
                "attributes": attributes,
                "semantic_description": semantic_fields.get("semantic_description", ""),
                "key_features": semantic_fields.get("key_features", ""),
                "use_cases": semantic_fields.get("use_cases", ""),
                "ai_generated_description": semantic_fields.get("ai_generated_description", ""),
                "verified": semantic_fields.get("semantic_description_verified", False),
            }
            
            return metadata
        
        except NotFoundError:
            raise
        
        except Exception as e:
            logger.error(f"Failed to get product metadata: {e}")
            raise OdooOperationError(f"Failed to get product metadata: {e}")
    
    async def generate_product_description(
        self,
        account_id: str,
        product_id: int,
        options: ProductDescriptionOptions = None,
    ) -> ProductDescriptionResponse:
        """
        Gera uma descrição semântica para um produto.
        
        Args:
            account_id: ID da conta
            product_id: ID do produto
            options: Opções para geração de descrição
        
        Returns:
            Descrição gerada
        
        Raises:
            NotFoundError: Se o produto não for encontrado
            ValidationError: Se os parâmetros forem inválidos
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Obter metadados do produto
            metadata = await self.get_product_metadata(odoo, product_id)
            
            # Verificar cache
            cache = await get_cache_service()
            cache_key = f"{account_id}:product_description:{product_id}"
            cached_description = await cache.get(cache_key)
            
            if cached_description:
                return ProductDescriptionResponse(
                    product_id=product_id,
                    description=cached_description.get("description", ""),
                    key_features=cached_description.get("key_features", []),
                    use_cases=cached_description.get("use_cases", []),
                )
            
            # Configurar opções
            if options is None:
                options = ProductDescriptionOptions()
            
            # Preparar prompt para o modelo
            prompt = self._build_description_prompt(metadata, options)
            
            # Gerar descrição via OpenAI API
            async with httpx.AsyncClient(timeout=settings.TIMEOUT_DEFAULT) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "You are a professional product description writer."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                    },
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extrair descrição
                description_text = data["choices"][0]["message"]["content"]
                
                # Processar resposta
                description, key_features, use_cases = self._parse_description_response(description_text)
                
                # Armazenar em cache
                await cache.set(
                    cache_key,
                    {
                        "description": description,
                        "key_features": key_features,
                        "use_cases": use_cases,
                    },
                    ttl=86400,  # 24 horas
                )
                
                return ProductDescriptionResponse(
                    product_id=product_id,
                    description=description,
                    key_features=key_features,
                    use_cases=use_cases,
                )
        
        except NotFoundError:
            raise
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while generating description: {e}")
            raise ValidationError(f"Failed to generate description: {e}")
        
        except Exception as e:
            logger.error(f"Failed to generate product description: {e}")
            raise ValidationError(f"Failed to generate product description: {e}")
    
    def _build_description_prompt(
        self, metadata: Dict[str, Any], options: ProductDescriptionOptions
    ) -> str:
        """
        Constrói o prompt para geração de descrição.
        
        Args:
            metadata: Metadados do produto
            options: Opções para geração de descrição
        
        Returns:
            Prompt para o modelo
        """
        prompt = f"""
        Please write a compelling product description for the following product:
        
        Product Name: {metadata['name']}
        Product Code: {metadata['default_code']}
        Category: {metadata['category']}
        Price: {metadata['list_price']}
        
        Existing Short Description: {metadata['description_sale']}
        Existing Full Description: {metadata['description']}
        
        Attributes:
        """
        
        for attr in metadata["attributes"]:
            prompt += f"- {attr['name']}: {', '.join(attr['values'])}\n"
        
        prompt += f"\nTone: {options.tone}\n\n"
        
        prompt += """
        Please format your response as follows:
        
        DESCRIPTION:
        [Write a compelling product description here]
        
        """
        
        if options.include_features:
            prompt += """
            KEY FEATURES:
            - [Feature 1]
            - [Feature 2]
            - [Feature 3]
            - [Feature 4]
            - [Feature 5]
            
            """
        
        if options.include_use_cases:
            prompt += """
            USE CASES:
            - [Use Case 1]
            - [Use Case 2]
            - [Use Case 3]
            
            """
        
        return prompt
    
    def _parse_description_response(self, response_text: str) -> tuple:
        """
        Processa a resposta do modelo.
        
        Args:
            response_text: Texto da resposta
        
        Returns:
            Tupla (descrição, características, casos de uso)
        """
        description = ""
        key_features = []
        use_cases = []
        
        # Extrair descrição
        if "DESCRIPTION:" in response_text:
            description_parts = response_text.split("DESCRIPTION:")
            if len(description_parts) > 1:
                description_text = description_parts[1].strip()
                if "KEY FEATURES:" in description_text:
                    description = description_text.split("KEY FEATURES:")[0].strip()
                elif "USE CASES:" in description_text:
                    description = description_text.split("USE CASES:")[0].strip()
                else:
                    description = description_text
        
        # Extrair características
        if "KEY FEATURES:" in response_text:
            features_parts = response_text.split("KEY FEATURES:")
            if len(features_parts) > 1:
                features_text = features_parts[1].strip()
                if "USE CASES:" in features_text:
                    features_text = features_text.split("USE CASES:")[0].strip()
                
                for line in features_text.split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        feature = line[1:].strip()
                        if feature:
                            key_features.append(feature)
        
        # Extrair casos de uso
        if "USE CASES:" in response_text:
            use_cases_parts = response_text.split("USE CASES:")
            if len(use_cases_parts) > 1:
                use_cases_text = use_cases_parts[1].strip()
                
                for line in use_cases_text.split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        use_case = line[1:].strip()
                        if use_case:
                            use_cases.append(use_case)
        
        return description, key_features, use_cases
    
    async def sync_product_to_vector_db(
        self,
        account_id: str,
        product_id: int,
        description: Optional[str] = None,
        skip_odoo_update: bool = False,
    ) -> ProductSyncResponse:
        """
        Sincroniza um produto com o banco de dados vetorial.
        
        Args:
            account_id: ID da conta
            product_id: ID do produto
            description: Descrição do produto (opcional)
            skip_odoo_update: Pular atualização do status no Odoo
        
        Returns:
            Resposta da sincronização
        
        Raises:
            NotFoundError: Se o produto não for encontrado
            ValidationError: Se os parâmetros forem inválidos
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Obter metadados do produto
            metadata = await self.get_product_metadata(odoo, product_id)
            
            # Usar descrição fornecida ou obter do produto
            if not description:
                if metadata["semantic_description"]:
                    description = metadata["semantic_description"]
                elif metadata["ai_generated_description"]:
                    description = metadata["ai_generated_description"]
                elif metadata["description"]:
                    description = metadata["description"]
                elif metadata["description_sale"]:
                    description = metadata["description_sale"]
                else:
                    description = metadata["name"]
            
            # Sincronizar com o banco de dados vetorial
            vector_service = await get_vector_service()
            vector_id = await vector_service.sync_product_to_vector_db(
                account_id=account_id,
                product_id=product_id,
                description=description,
                metadata={
                    "name": metadata["name"],
                    "default_code": metadata["default_code"],
                    "category_id": metadata["category"],
                    "price": metadata["list_price"],
                },
            )
            
            # Atualizar status no Odoo
            if not skip_odoo_update:
                await odoo.execute_kw(
                    "product.template",
                    "write",
                    [[product_id], {"semantic_description_verified": True}],
                )
            
            # Retornar resposta
            return ProductSyncResponse(
                product_id=product_id,
                vector_id=vector_id,
                sync_status="completed",
                timestamp=datetime.now(),
            )
        
        except NotFoundError:
            raise
        
        except Exception as e:
            logger.error(f"Failed to sync product to vector DB: {e}")
            raise ValidationError(f"Failed to sync product to vector DB: {e}")
    
    async def search_products(
        self,
        account_id: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> ProductSearchResponse:
        """
        Realiza uma busca semântica de produtos.
        
        Args:
            account_id: ID da conta
            query: Consulta de busca
            limit: Limite de resultados
            filters: Filtros adicionais
        
        Returns:
            Resultados da busca
        
        Raises:
            ValidationError: Se os parâmetros forem inválidos
        """
        try:
            # Realizar busca vetorial
            vector_service = await get_vector_service()
            vector_results = await vector_service.search_products(
                account_id=account_id,
                query=query,
                limit=limit,
                filters=filters,
            )
            
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Obter detalhes completos dos produtos
            product_ids = [result["product_id"] for result in vector_results]
            
            if not product_ids:
                return ProductSearchResponse(results=[], total=0)
            
            products = await odoo.execute_kw(
                "product.template",
                "read",
                [product_ids],
                {"fields": ["name", "description", "list_price", "categ_id"]},
            )
            
            # Mapear produtos por ID
            products_map = {product["id"]: product for product in products}
            
            # Construir resultados
            results = []
            for result in vector_results:
                product_id = result["product_id"]
                if product_id in products_map:
                    product = products_map[product_id]
                    results.append(
                        ProductSearchResult(
                            product_id=product_id,
                            name=product["name"],
                            description=product.get("description", ""),
                            score=result["score"],
                            price=product.get("list_price", 0.0),
                            category_id=product.get("categ_id", [False, ""])[0] if product.get("categ_id") else None,
                        )
                    )
            
            return ProductSearchResponse(
                results=results,
                total=len(results),
            )
        
        except Exception as e:
            logger.error(f"Failed to search products: {e}")
            raise ValidationError(f"Failed to search products: {e}")


# Instância global do serviço
semantic_product_service = SemanticProductService()

# Função para obter o serviço
def get_semantic_product_service() -> SemanticProductService:
    """
    Obtém o serviço de produtos semânticos.
    
    Returns:
        Instância do serviço
    """
    return semantic_product_service
