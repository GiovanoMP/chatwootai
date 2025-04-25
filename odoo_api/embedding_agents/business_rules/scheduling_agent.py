"""
Agente de embedding para regras de agendamento.

Este módulo implementa um agente para processamento de regras de agendamento
antes da geração de embeddings.
"""

import logging
from typing import Dict, Any, Optional

from odoo_api.core.interfaces.embedding_agent import EmbeddingAgent
from odoo_api.core.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

class SchedulingRulesEmbeddingAgent(EmbeddingAgent):
    """
    Agente para processamento de regras de agendamento para embeddings.

    Este agente utiliza um LLM para estruturar e enriquecer os dados brutos
    de regras de agendamento antes de enviá-los para o serviço de embeddings,
    melhorando a qualidade dos vetores gerados.
    """

    async def process_data(
        self,
        data: Dict[str, Any],
        business_area: Optional[str] = None
    ) -> str:
        """
        Processa regras de agendamento para vetorização.

        Args:
            data: Dados brutos da regra de agendamento
            business_area: Área de negócio da empresa (opcional)

        Returns:
            Texto enriquecido pronto para vetorização
        """
        # Construir o prompt para o agente
        system_prompt = """
        Você é um especialista em processamento de regras de agendamento para sistemas de IA.
        Sua tarefa é transformar os dados brutos de regras de agendamento em um texto rico e contextualizado
        para vetorização, seguindo estas diretrizes:

        1. Organize as informações em seções claras e bem estruturadas
        2. Expanda abreviações e termos técnicos para facilitar a compreensão
        3. Inclua variações de termos e sinônimos para melhorar a recuperação semântica
        4. Mantenha todas as informações originais, mas adicione contexto quando necessário
        5. Formate horários e datas de forma consistente e legível
        6. Estruture o texto para facilitar a busca por informações específicas
        7. Inclua uma seção PARTE 1 com dados estruturados em JSON e uma PARTE 2 com texto enriquecido
        8. Na PARTE 1, crie um JSON com os campos principais da regra de agendamento
        9. Na PARTE 2, crie um texto detalhado e contextualizado sobre a regra

        Seu objetivo é criar um texto que, quando vetorizado, permita que o sistema de IA:
        - Compreenda completamente as regras de agendamento
        - Responda perguntas sobre disponibilidade, duração e políticas
        - Auxilie usuários no processo de agendamento
        - Forneça informações precisas sobre horários, cancelamentos e reagendamentos
        """

        # Preparar os dados da regra em formato legível
        rule_data = self._format_scheduling_rule(data)

        # Chamar o LLM para processar os dados
        user_prompt = f"Processe a seguinte regra de agendamento para vetorização:\n\n{rule_data}"

        openai_service = await get_openai_service()
        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1500,  # Tokens suficientes para regras mais longas
            temperature=0.2  # Baixa temperatura para respostas mais determinísticas
        )

        return response.strip()

    def _format_scheduling_rule(self, rule: Dict[str, Any]) -> str:
        """
        Formata os dados da regra de agendamento em texto legível.

        Args:
            rule: Dados da regra de agendamento

        Returns:
            Texto formatado
        """
        # Extrair informações básicas
        name = rule.get('name', 'N/A')
        description = rule.get('description', 'N/A')
        service_type = rule.get('service_type', 'N/A')
        service_type_other = rule.get('service_type_other', '')
        
        # Se o tipo de serviço for "other", usar o valor personalizado
        if service_type == 'other' and service_type_other:
            service_type = service_type_other
            
        # Mapear tipos de serviço para nomes mais legíveis
        service_type_map = {
            'consultation': 'Consulta/Atendimento',
            'maintenance': 'Manutenção/Reparo',
            'delivery': 'Entrega',
            'installation': 'Instalação',
            'event': 'Evento'
        }
        
        service_type_display = service_type_map.get(service_type, service_type)
        
        # Formatar duração e intervalos
        duration = rule.get('duration', 0)
        duration_hours = int(duration)
        duration_minutes = int((duration - duration_hours) * 60)
        
        min_interval = rule.get('min_interval', 0)
        min_interval_hours = int(min_interval)
        min_interval_minutes = int((min_interval - min_interval_hours) * 60)
        
        # Formatar antecedência
        min_advance_time = rule.get('min_advance_time', 24)
        max_advance_time = rule.get('max_advance_time', 30)
        
        # Dias disponíveis
        days_available = []
        if rule.get('monday_available'):
            days_available.append('Segunda-feira')
        if rule.get('tuesday_available'):
            days_available.append('Terça-feira')
        if rule.get('wednesday_available'):
            days_available.append('Quarta-feira')
        if rule.get('thursday_available'):
            days_available.append('Quinta-feira')
        if rule.get('friday_available'):
            days_available.append('Sexta-feira')
        if rule.get('saturday_available'):
            days_available.append('Sábado')
        if rule.get('sunday_available'):
            days_available.append('Domingo')
            
        days_text = ', '.join(days_available) if days_available else 'Nenhum dia disponível'
        
        # Formatar horários
        def format_time(time_float):
            if not time_float:
                return "Não disponível"
            hours = int(time_float)
            minutes = int((time_float - hours) * 60)
            return f"{hours:02d}:{minutes:02d}"
        
        # Texto formatado
        formatted_text = f"""
        ## Regra de Agendamento: {name}
        
        Descrição: {description}
        
        ### Informações Básicas
        Tipo de Serviço: {service_type_display}
        Duração: {duration_hours}h {duration_minutes}min
        Intervalo Entre Atendimentos: {min_interval_hours}h {min_interval_minutes}min
        
        ### Antecedência para Agendamento
        Mínima: {min_advance_time} horas
        Máxima: {max_advance_time} dias
        
        ### Dias e Horários Disponíveis
        Dias disponíveis: {days_text}
        
        Horário de funcionamento (Segunda a Sexta):
        - Manhã: {format_time(rule.get('morning_start'))} às {format_time(rule.get('morning_end'))}
        - Tarde: {format_time(rule.get('afternoon_start'))} às {format_time(rule.get('afternoon_end'))}
        - Intervalo para almoço: {"Sim" if rule.get('has_lunch_break') else "Não"}
        
        Horário de funcionamento (Sábado):
        - Manhã: {format_time(rule.get('saturday_morning_start'))} às {format_time(rule.get('saturday_morning_end'))}
        - Tarde: {format_time(rule.get('saturday_afternoon_start'))} às {format_time(rule.get('saturday_afternoon_end'))}
        
        Horário de funcionamento (Domingo):
        - Manhã: {format_time(rule.get('sunday_morning_start'))} às {format_time(rule.get('sunday_morning_end'))}
        - Tarde: {format_time(rule.get('sunday_afternoon_start'))} às {format_time(rule.get('sunday_afternoon_end'))}
        
        ### Políticas
        Política de Cancelamento: {rule.get('cancellation_policy', 'N/A')}
        Política de Reagendamento: {rule.get('rescheduling_policy', 'N/A')}
        
        ### Informações Adicionais
        Informações Necessárias para Agendamento: {rule.get('required_information', 'N/A')}
        Instruções de Confirmação: {rule.get('confirmation_instructions', 'N/A')}
        """
        
        return formatted_text.strip()


# Função para obter uma instância do agente
async def get_scheduling_rules_agent() -> SchedulingRulesEmbeddingAgent:
    """
    Obtém uma instância do agente de embedding para regras de agendamento.
    
    Returns:
        Instância do agente
    """
    return SchedulingRulesEmbeddingAgent()
