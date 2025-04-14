"""
Agente de embedding para descrições de produtos.

Este módulo implementa um agente para processamento de descrições de produtos
antes da geração de embeddings.
"""

import json
import logging
from typing import Dict, Any, Optional, List

from odoo_api.core.interfaces.embedding_agent import EmbeddingAgent
from odoo_api.core.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

class ProductDescriptionEmbeddingAgent(EmbeddingAgent):
    """
    Agente para processamento de descrições de produtos para embeddings.
    
    Este agente utiliza um LLM para estruturar e enriquecer os dados brutos
    de produtos antes de enviá-los para o serviço de embeddings,
    melhorando a qualidade dos vetores gerados.
    """
    
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
        # Construir o prompt para o agente
        system_prompt = """
        Você é um especialista em processamento de dados para sistemas de IA.
        Sua tarefa é transformar os dados brutos de produtos em um texto rico e contextualizado
        para vetorização, seguindo estas diretrizes:
        
        1. Destaque características técnicas do produto
        2. Inclua informações sobre materiais e dimensões
        3. Mencione casos de uso e benefícios principais
        4. Organize as informações de forma estruturada
        5. Mantenha-se fiel aos dados fornecidos, sem inventar características
        
        Formate o texto final de forma que capture a essência do produto e suas características principais.
        """
        
        # Adicionar contexto da área de negócio, se disponível
        if business_area:
            system_prompt += f"\nEste produto pertence à área de negócio: {business_area}. Considere o contexto desta indústria."
        
        # Preparar os dados do produto em formato legível
        product_content = self._format_product_data(data)
        
        # Chamar o LLM para processar os dados
        user_prompt = f"Processe os seguintes dados de produto para vetorização:\n\n{product_content}"
        
        openai_service = await get_openai_service()
        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1000,
            temperature=0.2  # Baixa temperatura para respostas mais determinísticas
        )
        
        return response.strip()
    
    def _format_product_data(self, product_data: Dict[str, Any]) -> str:
        """
        Formata os dados do produto em texto legível.
        
        Args:
            product_data: Dados do produto
            
        Returns:
            Texto formatado
        """
        formatted_text = f"""
        Nome do produto: {product_data.get('name', 'N/A')}
        Descrição: {product_data.get('description', 'N/A')}
        Categoria: {product_data.get('categ_id', {}).get('name', 'N/A') if isinstance(product_data.get('categ_id'), dict) else product_data.get('categ_id', 'N/A')}
        Preço: {product_data.get('list_price', 'N/A')}
        """
        
        # Adicionar atributos do produto
        attributes = product_data.get('attribute_line_ids', [])
        if attributes:
            formatted_text += "Atributos:\n"
            for attr in attributes:
                attr_name = attr.get('attribute_id', {}).get('name', 'N/A') if isinstance(attr.get('attribute_id'), dict) else attr.get('attribute_id', 'N/A')
                values = [val.get('name', 'N/A') if isinstance(val, dict) else val for val in attr.get('value_ids', [])]
                formatted_text += f"- {attr_name}: {', '.join(values)}\n"
        
        # Adicionar especificações técnicas
        specs = product_data.get('product_spec_ids', [])
        if specs:
            formatted_text += "Especificações Técnicas:\n"
            for spec in specs:
                spec_name = spec.get('name', 'N/A')
                spec_value = spec.get('value', 'N/A')
                formatted_text += f"- {spec_name}: {spec_value}\n"
        
        # Adicionar tags
        tags = product_data.get('tag_ids', [])
        if tags:
            tag_names = [tag.get('name', 'N/A') if isinstance(tag, dict) else tag for tag in tags]
            formatted_text += f"Tags: {', '.join(tag_names)}\n"
        
        return formatted_text


# Singleton para o agente
_product_description_agent_instance = None

async def get_product_description_agent() -> ProductDescriptionEmbeddingAgent:
    """
    Obtém uma instância do agente de embeddings para descrições de produtos.
    
    Returns:
        Instância do agente de embeddings
    """
    global _product_description_agent_instance
    
    if _product_description_agent_instance is None:
        _product_description_agent_instance = ProductDescriptionEmbeddingAgent()
    
    return _product_description_agent_instance
