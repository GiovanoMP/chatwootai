"""
Agente de embedding para documentos de suporte ao cliente.

Este módulo implementa um agente para processamento de documentos de suporte
antes da geração de embeddings.
"""

import logging
from typing import Dict, Any, Optional

from odoo_api.core.interfaces.embedding_agent import EmbeddingAgent
from odoo_api.core.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

class SupportDocumentEmbeddingAgent(EmbeddingAgent):
    """
    Agente para processamento de documentos de suporte para embeddings.

    Este agente utiliza um LLM para estruturar e enriquecer os dados brutos
    de documentos de suporte antes de enviá-los para o serviço de embeddings,
    melhorando a qualidade dos vetores gerados.
    """

    async def process_data(
        self,
        data: Dict[str, Any],
        business_area: Optional[str] = None
    ) -> str:
        """
        Processa um documento de suporte para vetorização.

        Args:
            data: Dados brutos do documento
            business_area: Área de negócio da empresa (opcional)

        Returns:
            Texto enriquecido pronto para vetorização
        """
        # Construir o prompt para o agente
        system_prompt = """
        Você é um especialista em processamento de documentos para sistemas de IA.
        Sua tarefa é transformar os dados brutos de documentos de suporte ao cliente em um texto rico e contextualizado
        para vetorização, seguindo estas diretrizes:

        1. Mantenha-se estritamente aos fatos presentes nos dados
        2. Não invente informações ou características
        3. Expanda abreviações e explique termos técnicos quando necessário
        4. Organize as informações em formato claro e estruturado
        5. Se o documento contiver perguntas e respostas, organize-as em formato de FAQ
        6. Se o documento for uma política ou procedimento, estruture-o em seções claras
        7. Priorize informações que seriam úteis para responder consultas de clientes
        8. Se os dados forem insuficientes, mantenha-se minimalista - não preencha lacunas com suposições

        Formate o texto final de forma que capture a essência do documento de suporte.
        """

        # Adicionar contexto da área de negócio, se disponível
        if business_area:
            system_prompt += f"\nEste documento pertence à área de negócio: {business_area}. Considere o contexto desta indústria."

        # Preparar os dados do documento em formato legível
        document_content = self._format_document_data(data)

        # Chamar o LLM para processar os dados
        user_prompt = f"Processe o seguinte documento de suporte ao cliente para vetorização:\n\n{document_content}"

        openai_service = await get_openai_service()
        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1500,  # Tokens suficientes para documentos mais longos
            temperature=0.2  # Baixa temperatura para respostas mais determinísticas
        )

        return response.strip()

    def _format_document_data(self, document_data: Dict[str, Any]) -> str:
        """
        Formata os dados do documento em texto legível.

        Args:
            document_data: Dados do documento

        Returns:
            Texto formatado
        """
        formatted_text = f"""
        Nome do documento: {document_data.get('name', 'N/A')}
        Tipo de documento: {document_data.get('document_type', 'N/A')}
        """

        # Adicionar conteúdo do documento
        if 'content' in document_data and document_data['content']:
            formatted_text += f"\nConteúdo do documento:\n{document_data['content']}\n"

        return formatted_text


# Singleton para o agente
_support_document_agent_instance = None

async def get_support_document_agent() -> SupportDocumentEmbeddingAgent:
    """
    Obtém uma instância do agente de embeddings para documentos de suporte.

    Returns:
        Instância do agente de embeddings
    """
    global _support_document_agent_instance

    if _support_document_agent_instance is None:
        _support_document_agent_instance = SupportDocumentEmbeddingAgent()

    return _support_document_agent_instance
