"""
Agente de embedding para metadados da empresa.

Este módulo implementa um agente para processamento de metadados da empresa
antes da geração de embeddings.
"""

import logging
from typing import Dict, Any, Optional

from odoo_api.core.interfaces.embedding_agent import EmbeddingAgent
from odoo_api.core.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

class CompanyMetadataEmbeddingAgent(EmbeddingAgent):
    """
    Agente para processamento de metadados da empresa para embeddings.

    Este agente utiliza um LLM para estruturar e enriquecer os metadados brutos
    da empresa antes de enviá-los para o serviço de embeddings,
    melhorando a qualidade dos vetores gerados.
    """

    async def process_data(
        self,
        data: Dict[str, Any],
        business_area: Optional[str] = None
    ) -> str:
        """
        Processa os metadados da empresa para vetorização.

        Args:
            data: Metadados brutos da empresa
            business_area: Área de negócio da empresa (opcional)

        Returns:
            Texto enriquecido pronto para vetorização
        """
        # Construir o prompt para o agente
        system_prompt = """
        Você é um especialista em processamento de informações empresariais para sistemas de IA.
        Sua tarefa é transformar os metadados brutos de uma empresa em um texto rico e contextualizado
        para vetorização, seguindo estas diretrizes:

        1. Mantenha-se estritamente aos fatos presentes nos dados
        2. Não invente informações ou características
        3. Expanda abreviações e explique termos técnicos quando necessário
        4. Organize as informações em formato claro e estruturado
        5. Priorize informações que seriam úteis para responder consultas de clientes
        6. Crie um texto fluido e natural que capture a essência da empresa
        7. Inclua detalhes sobre horários de funcionamento, canais online, valores da empresa, etc.
        8. Se os dados forem insuficientes, mantenha-se minimalista - não preencha lacunas com suposições

        Formate o texto final como se estivesse descrevendo a empresa para um novo funcionário,
        incluindo todas as informações relevantes sobre a empresa, seus valores, horários, 
        canais de comunicação e estilo de atendimento.
        """

        # Adicionar contexto da área de negócio, se disponível
        if business_area:
            system_prompt += f"\nEsta empresa pertence à área de negócio: {business_area}. Considere o contexto desta indústria."

        # Preparar os dados da empresa em formato legível
        company_data = self._format_company_data(data)

        # Chamar o LLM para processar os dados
        user_prompt = f"Processe os seguintes metadados da empresa para vetorização:\n\n{company_data}"

        openai_service = await get_openai_service()
        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1500,  # Tokens suficientes para metadados mais longos
            temperature=0.2  # Baixa temperatura para respostas mais determinísticas
        )

        return response.strip()

    def _format_company_data(self, metadata: Dict[str, Any]) -> str:
        """
        Formata os metadados da empresa em texto legível.

        Args:
            metadata: Metadados da empresa

        Returns:
            Texto formatado
        """
        # Extrair informações básicas da empresa
        company_info = metadata.get('company_info', {})
        business_hours = metadata.get('business_hours', {})
        online_channels = metadata.get('online_channels', {})
        customer_service = metadata.get('customer_service', {})
        promotions = metadata.get('promotions', {})

        # Formatar informações básicas
        formatted_text = f"""
        ## Informações da Empresa
        Nome: {company_info.get('company_name', 'N/A')}
        Descrição: {company_info.get('description', 'N/A')}
        Valores da Empresa: {company_info.get('company_values', 'N/A')}
        Área de Negócio: {company_info.get('business_area', 'N/A')}
        """

        # Adicionar endereço se disponível
        if 'address' in company_info:
            address = company_info.get('address', {})
            formatted_text += f"""
            ## Endereço
            Rua: {address.get('street', 'N/A')}
            Complemento: {address.get('street2', 'N/A')}
            Cidade: {address.get('city', 'N/A')}
            Estado: {address.get('state', 'N/A')}
            CEP: {address.get('zip', 'N/A')}
            País: {address.get('country', 'Brasil')}
            """

        # Formatar horários de funcionamento
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
        ## Horários de Funcionamento
        Dias: {days_text}
        Horário: {business_hours.get('start_time', 'N/A')} às {business_hours.get('end_time', 'N/A')}
        """
        
        if business_hours.get('has_lunch_break'):
            formatted_text += f"Horário de Almoço: {business_hours.get('lunch_break_start', 'N/A')} às {business_hours.get('lunch_break_end', 'N/A')}\n"

        # Formatar canais online
        formatted_text += "\n## Canais Online\n"
        formatted_text += f"Website: {online_channels.get('website', 'N/A')}\n"
        formatted_text += f"Facebook: {online_channels.get('facebook_url', 'N/A')}\n"
        formatted_text += f"Instagram: {online_channels.get('instagram_url', 'N/A')}\n"
        formatted_text += f"Mencionar site ao finalizar conversa: {'Sim' if online_channels.get('mention_website_at_end') else 'Não'}\n"
        formatted_text += f"Mencionar Facebook ao finalizar conversa: {'Sim' if online_channels.get('mention_facebook_at_end') else 'Não'}\n"
        formatted_text += f"Mencionar Instagram ao finalizar conversa: {'Sim' if online_channels.get('mention_instagram_at_end') else 'Não'}\n"

        # Formatar informações de atendimento ao cliente
        formatted_text += "\n## Atendimento ao Cliente\n"
        formatted_text += f"Mensagem de Saudação: {customer_service.get('greeting_message', 'N/A')}\n"
        formatted_text += f"Estilo de Comunicação: {customer_service.get('communication_style', 'N/A')}\n"
        formatted_text += f"Uso de Emojis: {customer_service.get('emoji_usage', 'N/A')}\n"

        # Formatar informações sobre promoções
        formatted_text += "\n## Promoções\n"
        formatted_text += f"Informar promoções no início da conversa: {'Sim' if promotions.get('inform_at_start') else 'Não'}\n"

        return formatted_text


# Singleton para o agente
_company_metadata_agent_instance = None

async def get_company_metadata_agent() -> CompanyMetadataEmbeddingAgent:
    """
    Obtém uma instância do agente de embeddings para metadados da empresa.

    Returns:
        Instância do agente de embeddings
    """
    global _company_metadata_agent_instance

    if _company_metadata_agent_instance is None:
        _company_metadata_agent_instance = CompanyMetadataEmbeddingAgent()

    return _company_metadata_agent_instance
