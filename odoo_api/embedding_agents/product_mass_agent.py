"""
Agente de embedding para processamento em massa de produtos.

Este módulo implementa um agente para processamento em massa de produtos
antes da geração de embeddings.
"""

import json
import logging
from typing import Dict, Any, Optional, List

from odoo_api.core.interfaces.embedding_agent import EmbeddingAgent
from odoo_api.core.services.openai_service import get_openai_service
from odoo_api.embedding_agents.product_description_agent import ProductDescriptionEmbeddingAgent

logger = logging.getLogger(__name__)

class ProductMassEmbeddingAgent(EmbeddingAgent):
    """
    Agente para processamento em massa de produtos para embeddings.
    
    Este agente utiliza um LLM para estruturar e enriquecer os dados brutos
    de produtos em massa antes de enviá-los para o serviço de embeddings,
    melhorando a qualidade dos vetores gerados.
    """
    
    def __init__(self):
        """Inicializa o agente de embedding para produtos em massa."""
        self.product_agent = ProductDescriptionEmbeddingAgent()
    
    async def process_data(
        self, 
        data: Dict[str, Any], 
        business_area: Optional[str] = None
    ) -> str:
        """
        Processa dados de produto para vetorização.
        
        Args:
            data: Dados brutos do produto
            business_area: Área de negócio da empresa (opcional)
            
        Returns:
            Texto enriquecido pronto para vetorização
        """
        # Delegar para o agente de produto individual
        return await self.product_agent.process_data(data, business_area)
    
    async def process_batch(
        self, 
        products: List[Dict[str, Any]], 
        business_area: Optional[str] = None,
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Processa um lote de produtos para vetorização.
        
        Args:
            products: Lista de produtos
            business_area: Área de negócio (opcional)
            batch_size: Tamanho do lote para processamento
            
        Returns:
            Lista de produtos com textos processados
        """
        results = []
        
        # Processar em lotes para evitar sobrecarga
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            batch_results = await self._process_batch_internal(batch, business_area)
            results.extend(batch_results)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}")
        
        return results
    
    async def _process_batch_internal(
        self, 
        products: List[Dict[str, Any]], 
        business_area: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Processa um lote interno de produtos para vetorização.
        
        Args:
            products: Lista de produtos
            business_area: Área de negócio (opcional)
            
        Returns:
            Lista de produtos com textos processados
        """
        # Construir o prompt para o agente
        system_prompt = """
        Você é um especialista em processamento de dados para sistemas de IA.
        Sua tarefa é transformar os dados brutos de produtos em textos ricos e contextualizados
        para vetorização, seguindo estas diretrizes:
        
        1. Destaque características técnicas de cada produto
        2. Inclua informações sobre materiais e dimensões
        3. Mencione casos de uso e benefícios principais
        4. Organize as informações de forma estruturada
        5. Mantenha-se fiel aos dados fornecidos, sem inventar características
        
        Formate cada texto final de forma que capture a essência do produto e suas características principais.
        Retorne os resultados em formato JSON, com o ID do produto como chave e o texto processado como valor.
        """
        
        # Adicionar contexto da área de negócio, se disponível
        if business_area:
            system_prompt += f"\nEstes produtos pertencem à área de negócio: {business_area}. Considere o contexto desta indústria."
        
        # Preparar os dados dos produtos em formato legível
        products_content = self._format_products_batch(products)
        
        # Chamar o LLM para processar os dados
        user_prompt = f"Processe os seguintes dados de produtos para vetorização:\n\n{products_content}"
        
        openai_service = await get_openai_service()
        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,  # Aumentar para acomodar múltiplos produtos
            temperature=0.2  # Baixa temperatura para respostas mais determinísticas
        )
        
        # Processar a resposta
        try:
            # Tentar extrair JSON da resposta
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                processed_data = json.loads(json_str)
                
                # Converter para o formato esperado
                results = []
                for product in products:
                    product_id = str(product.get('id', ''))
                    if product_id in processed_data:
                        results.append({
                            **product,
                            'processed_text': processed_data[product_id]
                        })
                    else:
                        # Processar individualmente se não estiver no lote
                        processed_text = await self.process_data(product, business_area)
                        results.append({
                            **product,
                            'processed_text': processed_text
                        })
                
                return results
            else:
                # Fallback: processar individualmente
                logger.warning("Failed to parse JSON response from batch processing, falling back to individual processing")
                return await self._process_individually(products, business_area)
        
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            # Fallback: processar individualmente
            return await self._process_individually(products, business_area)
    
    async def _process_individually(
        self, 
        products: List[Dict[str, Any]], 
        business_area: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Processa produtos individualmente.
        
        Args:
            products: Lista de produtos
            business_area: Área de negócio (opcional)
            
        Returns:
            Lista de produtos com textos processados
        """
        results = []
        for product in products:
            processed_text = await self.process_data(product, business_area)
            results.append({
                **product,
                'processed_text': processed_text
            })
        return results
    
    def _format_products_batch(self, products: List[Dict[str, Any]]) -> str:
        """
        Formata um lote de produtos em texto legível.
        
        Args:
            products: Lista de produtos
            
        Returns:
            Texto formatado
        """
        formatted_text = ""
        
        for i, product in enumerate(products):
            formatted_text += f"\n--- Produto {i+1} (ID: {product.get('id', 'N/A')}) ---\n"
            formatted_text += self.product_agent._format_product_data(product)
            formatted_text += "\n"
        
        return formatted_text


# Singleton para o agente
_product_mass_agent_instance = None

async def get_product_mass_agent() -> ProductMassEmbeddingAgent:
    """
    Obtém uma instância do agente de embeddings para produtos em massa.
    
    Returns:
        Instância do agente de embeddings
    """
    global _product_mass_agent_instance
    
    if _product_mass_agent_instance is None:
        _product_mass_agent_instance = ProductMassEmbeddingAgent()
    
    return _product_mass_agent_instance
