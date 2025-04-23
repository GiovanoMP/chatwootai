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
        Sua tarefa é transformar os dados brutos de documentos de suporte ao cliente em um formato estruturado JSON
        para facilitar a análise por agentes de IA, seguindo estas diretrizes RIGOROSAS:

        1. NUNCA invente informações ou características que não estejam explicitamente presentes nos dados
        2. Mantenha-se ESTRITAMENTE aos fatos presentes nos dados originais
        3. Expanda abreviações e explique termos técnicos quando necessário, mas sem adicionar informações não presentes
        4. Organize as informações em formato estruturado JSON
        5. Se o documento contiver perguntas e respostas, organize-as em formato de FAQ no JSON
        6. Se o documento for uma política ou procedimento, estruture-o em seções claras no JSON
        7. Priorize informações que seriam úteis para responder consultas de clientes
        8. Se os dados forem insuficientes, mantenha-se minimalista - NÃO preencha lacunas com suposições
        9. Identifique padrões e estruturas no documento para facilitar a análise por agentes de IA
        10. Extraia entidades, datas, valores numéricos e outros dados estruturados quando presentes

        IMPORTANTE: Sua resposta DEVE seguir EXATAMENTE este formato:
        1. Primeiro, um bloco de código JSON válido entre delimitadores ```json e ```
        2. Depois, uma versão textual enriquecida do documento

        O JSON DEVE ser válido e seguir exatamente a estrutura fornecida no exemplo. Não adicione comentários dentro do JSON.
        """

        # Adicionar contexto da área de negócio, se disponível
        if business_area:
            system_prompt += f"\nEste documento pertence à área de negócio: {business_area}. Considere o contexto desta indústria, mas NÃO adicione informações específicas do setor que não estejam no documento original."

        # Preparar os dados do documento em formato legível
        document_content = self._format_document_data(data)

        # Chamar o LLM para processar os dados
        user_prompt = f"""Processe o seguinte documento de suporte ao cliente para vetorização:

{document_content}

Estruture sua resposta em duas partes:

PARTE 1 - JSON ESTRUTURADO:
```json
{{
  "document_metadata": {{
    "title": "Título descritivo do documento",
    "document_type": "Tipo do documento (FAQ, Política, Procedimento, etc.)",
    "audience": "Público-alvo do documento",
    "complexity": "Baixa/Média/Alta",
    "keywords": ["palavra1", "palavra2", "palavra3", "..."]
  }},
  "content_summary": "Breve resumo do conteúdo do documento",
  "structured_content": {{
    "sections": [
      {{
        "title": "Título da seção 1",
        "content": "Conteúdo da seção 1"
      }},
      {{
        "title": "Título da seção 2",
        "content": "Conteúdo da seção 2"
      }}
    ]
  }},
  "entities": {
    "products": ["produto1", "produto2", "..."],
    "services": ["serviço1", "serviço2", "..."],
    "dates": ["data1", "data2", "..."],
    "values": ["valor1", "valor2", "..."]
  },
  "faq_items": [
    {{
      "question": "Pergunta 1",
      "answer": "Resposta 1"
    }},
    {{
      "question": "Pergunta 2",
      "answer": "Resposta 2"
    }}
  ]
}}
```

PARTE 2 - TEXTO ENRIQUECIDO:
[Versão textual enriquecida do documento, organizada em seções com títulos e subtítulos]

LEMBRE-SE: Não invente NENHUMA informação que não esteja presente no documento original. Se algum campo não puder ser preenchido com informações do documento, deixe-o como array vazio [] ou string vazia "".
"""

        openai_service = await get_openai_service()
        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2500,  # Tokens suficientes para documentos mais longos e JSON complexo
            temperature=0.1  # Temperatura muito baixa para respostas mais determinísticas e consistentes
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
        Documento de Suporte ao Cliente

        Nome: {document_data.get('name', 'N/A')}
        Tipo: {document_data.get('document_type', 'N/A')}

        Conteúdo:
        {document_data.get('content', '')}
        """

        # Adicionar descrição se disponível
        if 'description' in document_data and document_data['description']:
            formatted_text += f"\nDescrição: {document_data['description']}\n"

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
