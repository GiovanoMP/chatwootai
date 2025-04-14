"""
Agente de embedding para regras de negócio.

Este módulo implementa um agente para processamento de regras de negócio
antes da geração de embeddings.
"""

import json
import logging
from typing import Dict, Any, Optional

from odoo_api.core.interfaces.embedding_agent import EmbeddingAgent
from odoo_api.core.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

class BusinessRulesEmbeddingAgent(EmbeddingAgent):
    """
    Agente para processamento de regras de negócio para embeddings.
    
    Este agente utiliza um LLM para estruturar e enriquecer os dados brutos
    de regras de negócio antes de enviá-los para o serviço de embeddings,
    melhorando a qualidade dos vetores gerados.
    """
    
    async def process_data(
        self, 
        data: Dict[str, Any], 
        business_area: Optional[str] = None
    ) -> str:
        """
        Processa uma regra de negócio para vetorização.
        
        Args:
            data: Dados brutos da regra
            business_area: Área de negócio da empresa (opcional)
            
        Returns:
            Texto enriquecido pronto para vetorização
        """
        # Construir o prompt para o agente
        system_prompt = """
        Você é um especialista em processamento de dados para sistemas de IA.
        Sua tarefa é transformar os dados brutos de regras de negócio em um texto rico e contextualizado
        para vetorização, seguindo estas diretrizes:
        
        1. Mantenha-se estritamente aos fatos presentes nos dados
        2. Não invente informações ou características
        3. Expanda abreviações e explique termos técnicos quando necessário
        4. Organize as informações em formato claro e estruturado
        5. Priorize informações que seriam úteis para responder consultas de clientes
        6. Se os dados forem insuficientes, mantenha-se minimalista - não preencha lacunas com suposições
        
        Formate o texto final de forma que capture a essência da regra de negócio.
        """
        
        # Adicionar contexto da área de negócio, se disponível
        if business_area:
            system_prompt += f"\nEsta regra pertence à área de negócio: {business_area}. Considere o contexto desta indústria."
        
        # Preparar os dados da regra em formato legível
        rule_content = self._format_rule_data(data)
        
        # Chamar o LLM para processar os dados
        user_prompt = f"Processe os seguintes dados de regra de negócio para vetorização:\n\n{rule_content}"
        
        openai_service = await get_openai_service()
        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1000,
            temperature=0.2  # Baixa temperatura para respostas mais determinísticas
        )
        
        return response.strip()
    
    def _format_rule_data(self, rule_data: Dict[str, Any]) -> str:
        """
        Formata os dados da regra em texto legível.
        
        Args:
            rule_data: Dados da regra
            
        Returns:
            Texto formatado
        """
        formatted_text = f"""
        Nome da regra: {rule_data.get('name', 'N/A')}
        Descrição: {rule_data.get('description', 'N/A')}
        Tipo: {rule_data.get('type', 'N/A')}
        """
        
        # Adicionar dados específicos da regra
        rule_specific_data = rule_data.get('rule_data', {})
        if rule_specific_data:
            formatted_text += f"Dados específicos:\n{json.dumps(rule_specific_data, ensure_ascii=False, indent=2)}\n"
        
        # Adicionar informações de temporalidade
        if rule_data.get('is_temporary'):
            formatted_text += f"""
            Regra temporária válida de {rule_data.get('start_date')} até {rule_data.get('end_date')}
            """
        
        return formatted_text


# Singleton para o agente
_business_rules_agent_instance = None

async def get_business_rules_agent() -> BusinessRulesEmbeddingAgent:
    """
    Obtém uma instância do agente de embeddings para regras de negócio.
    
    Returns:
        Instância do agente de embeddings
    """
    global _business_rules_agent_instance
    
    if _business_rules_agent_instance is None:
        _business_rules_agent_instance = BusinessRulesEmbeddingAgent()
    
    return _business_rules_agent_instance
