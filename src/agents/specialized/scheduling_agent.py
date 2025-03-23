"""
Agente de agendamento adaptável para diferentes domínios de negócio.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from crewai import Agent
from src.api.erp import OdooClient
from src.core.domain.domain_manager import DomainManager
from src.core.memory import MemorySystem
from src.core.data_proxy_agent import DataProxyAgent

logger = logging.getLogger(__name__)


class SchedulingAgent(AdaptableAgent):
    """
    Agente de agendamento adaptável para diferentes domínios de negócio.
    
    Especializado em processar consultas relacionadas a agendamentos, horários
    disponíveis e serviços, adaptando-se ao domínio de negócio ativo.
    """
    
    def get_agent_type(self) -> str:
        """
        Obtém o tipo do agente.
        
        Returns:
            str: Tipo do agente
        """
        return "scheduling"
    
    def initialize(self):
        """
        Inicializa o agente de agendamento.
        """
        super().initialize()
        
        # Obtém configuração do ERP
        erp_config = self.config.get("erp", {})
        
        # Cria cliente Odoo
        try:
            self.erp_client = OdooClient(erp_config)
        except Exception as e:
            logger.error(f"Não foi possível criar cliente Odoo: {str(e)}")
            self.erp_client = None
    
    def get_services(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Obtém a lista de serviços disponíveis.
        
        Args:
            category: Categoria específica (opcional)
            
        Returns:
            List[Dict[str, Any]]: Lista de serviços
        """
        # Verifica se há plugins específicos para serviços
        domain_name = self.domain_manager.active_domain_name
        services_plugin = f"{domain_name}_services"
        
        if self.plugin_manager.has_plugin(services_plugin):
            # Usa o plugin específico do domínio para serviços
            return self.execute_plugin(
                services_plugin, 
                "get_services", 
                category=category
            )
        
        # Caso não haja plugin específico, usa as regras de negócio
        services_rules = self.get_business_rules("services")
        
        if category and category in services_rules:
            return services_rules[category]
        
        # Combina todas as categorias
        all_services = []
        for cat, services in services_rules.items():
            if isinstance(services, list):
                all_services.extend(services)
        
        return all_services
    
    def get_available_slots(self, service_id: str, date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        """
        Obtém os horários disponíveis para um serviço.
        
        Args:
            service_id: ID do serviço
            date_from: Data inicial (opcional, padrão: hoje)
            date_to: Data final (opcional, padrão: 7 dias a partir de hoje)
            
        Returns:
            List[Dict[str, Any]]: Lista de horários disponíveis
        """
        # Define datas padrão se não fornecidas
        if not date_from:
            date_from = datetime.now().strftime("%Y-%m-%d")
        
        if not date_to:
            date_to = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Verifica se há plugins específicos para agendamento
        domain_name = self.domain_manager.active_domain_name
        scheduling_plugin = f"{domain_name}_scheduling"
        
        if self.plugin_manager.has_plugin(scheduling_plugin):
            # Usa o plugin específico do domínio para agendamento
            return self.execute_plugin(
                scheduling_plugin, 
                "get_available_slots", 
                service_id=service_id,
                date_from=date_from,
                date_to=date_to
            )
        
        # Caso não haja plugin específico, usa o cliente ERP
        if self.erp_client:
            return self.erp_client.get_available_slots(service_id, date_from, date_to)
        
        return []
    
    def create_appointment(self, customer_id: str, service_id: str, datetime_slot: str, **kwargs) -> Dict[str, Any]:
        """
        Cria um novo agendamento.
        
        Args:
            customer_id: ID do cliente
            service_id: ID do serviço
            datetime_slot: Data e hora do agendamento (formato: YYYY-MM-DD HH:MM:SS)
            **kwargs: Parâmetros adicionais do agendamento
            
        Returns:
            Dict[str, Any]: Agendamento criado
        """
        # Verifica se há plugins específicos para agendamento
        domain_name = self.domain_manager.active_domain_name
        scheduling_plugin = f"{domain_name}_scheduling"
        
        if self.plugin_manager.has_plugin(scheduling_plugin):
            # Usa o plugin específico do domínio para agendamento
            return self.execute_plugin(
                scheduling_plugin, 
                "create_appointment", 
                customer_id=customer_id,
                service_id=service_id,
                datetime_slot=datetime_slot,
                **kwargs
            )
        
        # Caso não haja plugin específico, usa o cliente ERP
        if self.erp_client:
            appointment_data = {
                "customer_id": customer_id,
                "service_id": service_id,
                "datetime": datetime_slot,
                **kwargs
            }
            
            return self.erp_client.create_appointment(appointment_data)
        
        return {"error": "Cliente ERP não disponível"}
    
    def reschedule_appointment(self, appointment_id: str, new_datetime_slot: str) -> Dict[str, Any]:
        """
        Reagenda um agendamento existente.
        
        Args:
            appointment_id: ID do agendamento
            new_datetime_slot: Nova data e hora do agendamento (formato: YYYY-MM-DD HH:MM:SS)
            
        Returns:
            Dict[str, Any]: Agendamento atualizado
        """
        # Verifica se há plugins específicos para agendamento
        domain_name = self.domain_manager.active_domain_name
        scheduling_plugin = f"{domain_name}_scheduling"
        
        if self.plugin_manager.has_plugin(scheduling_plugin):
            # Usa o plugin específico do domínio para agendamento
            return self.execute_plugin(
                scheduling_plugin, 
                "reschedule_appointment", 
                appointment_id=appointment_id,
                new_datetime_slot=new_datetime_slot
            )
        
        # Caso não haja plugin específico, usa o cliente ERP
        if self.erp_client:
            # Obtém o agendamento atual
            appointment = self.erp_client.get_appointment(appointment_id)
            
            if "error" in appointment:
                return appointment
            
            # Atualiza a data e hora
            appointment_data = appointment.copy()
            appointment_data["datetime"] = new_datetime_slot
            
            return self.erp_client.update_appointment(appointment_id, appointment_data)
        
        return {"error": "Cliente ERP não disponível"}
