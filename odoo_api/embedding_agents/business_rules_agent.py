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

        # Adicionar informações básicas da empresa
        if 'company_name' in rule_specific_data or 'website' in rule_specific_data or 'description' in rule_specific_data or 'company_values' in rule_specific_data:
            formatted_text += "\nInformações da Empresa:\n"

            if 'company_name' in rule_specific_data and rule_specific_data['company_name']:
                formatted_text += f"Nome da empresa: {rule_specific_data['company_name']}\n"

            if 'website' in rule_specific_data and rule_specific_data['website']:
                formatted_text += f"Website: {rule_specific_data['website']}\n"

            if 'description' in rule_specific_data and rule_specific_data['description']:
                formatted_text += f"Descrição: {rule_specific_data['description']}\n"

            if 'company_values' in rule_specific_data and rule_specific_data['company_values']:
                formatted_text += f"Valores da empresa: {rule_specific_data['company_values']}\n"

            if 'business_area' in rule_specific_data and rule_specific_data['business_area']:
                area = rule_specific_data['business_area']
                if area == 'other' and 'business_area_other' in rule_specific_data:
                    area = rule_specific_data['business_area_other']
                formatted_text += f"Setor de atuação: {area}\n"

        # Adicionar informações de horário de funcionamento
        if 'days' in rule_specific_data:
            # Formatar informações de horário de funcionamento
            days_map = {
                0: "Segunda-feira",
                1: "Terça-feira",
                2: "Quarta-feira",
                3: "Quinta-feira",
                4: "Sexta-feira",
                5: "Sábado",
                6: "Domingo"
            }

            days = rule_specific_data.get('days', [])
            days_text = ", ".join([days_map.get(day, str(day)) for day in days])

            formatted_text += f"""
            \nInformações de Horário de Funcionamento:
            Dias de funcionamento: {days_text}
            """

            if 'start_time' in rule_specific_data and 'end_time' in rule_specific_data:
                formatted_text += f"Horário de funcionamento: {rule_specific_data.get('start_time')} até {rule_specific_data.get('end_time')}\n"

            if 5 in days and 'saturday_start_time' in rule_specific_data and 'saturday_end_time' in rule_specific_data:
                formatted_text += f"Horário de sábado: {rule_specific_data.get('saturday_start_time')} até {rule_specific_data.get('saturday_end_time')}\n"

            if rule_specific_data.get('has_lunch_break'):
                formatted_text += f"Intervalo de almoço: {rule_specific_data.get('lunch_break_start')} até {rule_specific_data.get('lunch_break_end')}\n"

        # Adicionar informações de atendimento ao cliente
        if 'greeting_message' in rule_specific_data or 'communication_style' in rule_specific_data or 'emoji_usage' in rule_specific_data:
            formatted_text += f"""
            \nInformações de Atendimento ao Cliente:
            """

            if 'greeting_message' in rule_specific_data and rule_specific_data['greeting_message']:
                formatted_text += f"Saudação: {rule_specific_data['greeting_message']}\n"

            if 'communication_style' in rule_specific_data:
                style_map = {
                    'formal': "Formal",
                    'casual': "Casual",
                    'friendly': "Amigável",
                    'technical': "Técnico"
                }
                style = style_map.get(rule_specific_data.get('communication_style'), rule_specific_data.get('communication_style'))
                formatted_text += f"Estilo de comunicação: {style}\n"

            if 'emoji_usage' in rule_specific_data:
                emoji_map = {
                    'none': "Não usar emojis",
                    'moderate': "Uso moderado de emojis",
                    'frequent': "Uso frequente de emojis"
                }
                emoji_usage = emoji_map.get(rule_specific_data.get('emoji_usage'), rule_specific_data.get('emoji_usage'))
                formatted_text += f"Uso de emojis: {emoji_usage}\n"

        elif rule_data.get('type') == 'delivery':
            # Formatar informações de entrega
            if 'min_days' in rule_specific_data and 'max_days' in rule_specific_data:
                formatted_text += f"Prazo de entrega: {rule_specific_data.get('min_days')} a {rule_specific_data.get('max_days')} dias\n"

            if 'free_shipping_min_value' in rule_specific_data:
                formatted_text += f"Frete grátis para compras acima de R$ {rule_specific_data.get('free_shipping_min_value')}\n"

            if 'excluded_regions' in rule_specific_data and rule_specific_data.get('excluded_regions'):
                regions = ", ".join(rule_specific_data.get('excluded_regions'))
                formatted_text += f"Regiões excluídas: {regions}\n"

        elif rule_data.get('type') == 'promotion':
            # Formatar informações de promoção
            if 'name' in rule_specific_data:
                formatted_text += f"Nome da promoção: {rule_specific_data.get('name')}\n"

            if 'description' in rule_specific_data:
                formatted_text += f"Descrição da promoção: {rule_specific_data.get('description')}\n"

            if 'discount_type' in rule_specific_data and 'discount_value' in rule_specific_data:
                discount_type = "percentual" if rule_specific_data.get('discount_type') == "percentage" else "fixo"
                formatted_text += f"Desconto {discount_type} de {rule_specific_data.get('discount_value')}\n"

            if 'coupon_code' in rule_specific_data:
                formatted_text += f"Código do cupom: {rule_specific_data.get('coupon_code')}\n"

        # Para outros tipos de regra ou dados adicionais, incluir como JSON
        if rule_specific_data and not any(rule_data.get('type') == t for t in ['schedule', 'business_hours', 'service', 'customer_service', 'delivery', 'promotion']):
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
