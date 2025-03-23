"""
Plugin de agendamento de tratamentos estéticos para o domínio de cosméticos.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

from src.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class TreatmentSchedulerPlugin(BasePlugin):
    """
    Plugin para agendamento de tratamentos estéticos baseado nas necessidades do cliente,
    disponibilidade de profissionais e regras de negócio específicas.
    """
    
    def initialize(self):
        """
        Inicializa o plugin carregando dados específicos de tratamentos estéticos.
        """
        self.treatment_types = self._load_treatment_types()
        self.professionals = self._load_professionals()
        self.business_rules = self._load_business_rules()
    
    def _load_treatment_types(self) -> List[Dict[str, Any]]:
        """
        Carrega os tipos de tratamentos disponíveis.
        Em uma implementação real, isso poderia vir de uma API ou banco de dados.
        
        Returns:
            List[Dict[str, Any]]: Lista de tipos de tratamentos
        """
        return [
            {
                "id": "t001",
                "name": "Limpeza de Pele",
                "description": "Procedimento de limpeza profunda da pele",
                "duration_minutes": 60,
                "price": 150.00,
                "suitable_for": ["normal", "oleosa", "mista", "acneica"],
                "addresses_concerns": ["acne", "oleosidade", "poros dilatados", "cravos"]
            },
            {
                "id": "t002",
                "name": "Peeling Químico",
                "description": "Esfoliação química para renovação celular",
                "duration_minutes": 45,
                "price": 180.00,
                "suitable_for": ["normal", "mista", "oleosa", "manchada"],
                "addresses_concerns": ["manchas", "textura irregular", "linhas finas", "acne"]
            },
            {
                "id": "t003",
                "name": "Hidratação Facial",
                "description": "Tratamento intensivo de hidratação facial",
                "duration_minutes": 30,
                "price": 120.00,
                "suitable_for": ["normal", "seca", "sensível", "desidratada"],
                "addresses_concerns": ["ressecamento", "desidratação", "sensibilidade"]
            },
            {
                "id": "t004",
                "name": "Massagem Modeladora",
                "description": "Massagem para modelar o corpo e reduzir medidas",
                "duration_minutes": 60,
                "price": 200.00,
                "suitable_for": ["todos"],
                "addresses_concerns": ["gordura localizada", "celulite", "retenção de líquidos"]
            },
            {
                "id": "t005",
                "name": "Drenagem Linfática",
                "description": "Massagem para estimular o sistema linfático",
                "duration_minutes": 60,
                "price": 180.00,
                "suitable_for": ["todos"],
                "addresses_concerns": ["retenção de líquidos", "inchaço", "circulação"]
            }
        ]
    
    def _load_professionals(self) -> List[Dict[str, Any]]:
        """
        Carrega os profissionais disponíveis.
        Em uma implementação real, isso poderia vir de uma API ou banco de dados.
        
        Returns:
            List[Dict[str, Any]]: Lista de profissionais
        """
        return [
            {
                "id": "p001",
                "name": "Ana Silva",
                "specialties": ["Limpeza de Pele", "Peeling Químico", "Hidratação Facial"],
                "availability": {
                    "monday": ["09:00-12:00", "14:00-18:00"],
                    "tuesday": ["09:00-12:00", "14:00-18:00"],
                    "wednesday": ["09:00-12:00", "14:00-18:00"],
                    "thursday": ["09:00-12:00", "14:00-18:00"],
                    "friday": ["09:00-12:00", "14:00-18:00"],
                    "saturday": ["09:00-13:00"],
                    "sunday": []
                }
            },
            {
                "id": "p002",
                "name": "Carlos Oliveira",
                "specialties": ["Massagem Modeladora", "Drenagem Linfática"],
                "availability": {
                    "monday": ["10:00-14:00", "15:00-19:00"],
                    "tuesday": ["10:00-14:00", "15:00-19:00"],
                    "wednesday": ["10:00-14:00", "15:00-19:00"],
                    "thursday": ["10:00-14:00", "15:00-19:00"],
                    "friday": ["10:00-14:00", "15:00-19:00"],
                    "saturday": ["10:00-14:00"],
                    "sunday": []
                }
            },
            {
                "id": "p003",
                "name": "Mariana Costa",
                "specialties": ["Limpeza de Pele", "Hidratação Facial", "Peeling Químico"],
                "availability": {
                    "monday": ["08:00-12:00", "13:00-17:00"],
                    "tuesday": ["08:00-12:00", "13:00-17:00"],
                    "wednesday": ["08:00-12:00", "13:00-17:00"],
                    "thursday": ["08:00-12:00", "13:00-17:00"],
                    "friday": ["08:00-12:00", "13:00-17:00"],
                    "saturday": ["08:00-12:00"],
                    "sunday": []
                }
            }
        ]
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """
        Carrega as regras de negócio para agendamento.
        Em uma implementação real, isso poderia vir de uma API ou banco de dados.
        
        Returns:
            Dict[str, Any]: Regras de negócio
        """
        return {
            "min_time_between_appointments": 15,  # minutos
            "max_appointments_per_day": 3,  # para o mesmo cliente
            "cancellation_policy": {
                "min_hours_before": 24,
                "fee_percentage": 30
            },
            "rescheduling_policy": {
                "max_reschedules": 2,
                "min_hours_before": 12
            }
        }
    
    def get_available_treatments(self, skin_type: str, concerns: List[str]) -> List[Dict[str, Any]]:
        """
        Obtém os tratamentos disponíveis adequados para o tipo de pele e preocupações do cliente.
        
        Args:
            skin_type: Tipo de pele do cliente
            concerns: Preocupações do cliente
            
        Returns:
            List[Dict[str, Any]]: Lista de tratamentos recomendados
        """
        suitable_treatments = []
        
        for treatment in self.treatment_types:
            # Verifica se o tratamento é adequado para o tipo de pele
            if skin_type in treatment["suitable_for"] or "todos" in treatment["suitable_for"]:
                # Verifica se o tratamento atende às preocupações do cliente
                if any(concern in treatment["addresses_concerns"] for concern in concerns):
                    suitable_treatments.append(treatment)
        
        # Ordena por relevância (número de preocupações atendidas)
        suitable_treatments.sort(
            key=lambda t: sum(1 for c in concerns if c in t["addresses_concerns"]),
            reverse=True
        )
        
        return suitable_treatments
    
    def get_available_slots(self, treatment_id: str, start_date: datetime, 
                           end_date: datetime) -> List[Dict[str, Any]]:
        """
        Obtém os horários disponíveis para um tratamento específico.
        
        Args:
            treatment_id: ID do tratamento
            start_date: Data inicial para busca
            end_date: Data final para busca
            
        Returns:
            List[Dict[str, Any]]: Lista de horários disponíveis
        """
        # Encontra o tratamento pelo ID
        treatment = next((t for t in self.treatment_types if t["id"] == treatment_id), None)
        if not treatment:
            logger.error(f"Tratamento não encontrado: {treatment_id}")
            return []
        
        # Duração do tratamento em minutos
        duration = treatment["duration_minutes"]
        
        # Encontra profissionais que realizam este tratamento
        qualified_professionals = [
            p for p in self.professionals 
            if treatment["name"] in p["specialties"]
        ]
        
        if not qualified_professionals:
            logger.warning(f"Nenhum profissional disponível para o tratamento: {treatment['name']}")
            return []
        
        # Calcula os slots disponíveis
        available_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            day_name = current_date.strftime("%A").lower()
            
            for professional in qualified_professionals:
                # Verifica disponibilidade do profissional neste dia
                if day_name in professional["availability"]:
                    day_slots = professional["availability"][day_name]
                    
                    for slot_range in day_slots:
                        start_str, end_str = slot_range.split("-")
                        slot_start = datetime.strptime(start_str, "%H:%M").replace(
                            year=current_date.year, 
                            month=current_date.month, 
                            day=current_date.day
                        )
                        slot_end = datetime.strptime(end_str, "%H:%M").replace(
                            year=current_date.year, 
                            month=current_date.month, 
                            day=current_date.day
                        )
                        
                        # Divide o período em slots com base na duração do tratamento
                        current_slot = slot_start
                        while current_slot + timedelta(minutes=duration) <= slot_end:
                            available_slots.append({
                                "date": current_slot.strftime("%Y-%m-%d"),
                                "time": current_slot.strftime("%H:%M"),
                                "professional_id": professional["id"],
                                "professional_name": professional["name"],
                                "treatment_id": treatment_id,
                                "treatment_name": treatment["name"],
                                "duration_minutes": duration
                            })
                            
                            # Avança para o próximo slot, considerando o intervalo entre agendamentos
                            current_slot += timedelta(
                                minutes=duration + self.business_rules["min_time_between_appointments"]
                            )
            
            # Avança para o próximo dia
            current_date += timedelta(days=1)
        
        return available_slots
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Executa uma ação do plugin de agendamento.
        
        Args:
            action: Ação a ser executada
            **kwargs: Parâmetros específicos da ação
            
        Returns:
            Any: Resultado da ação
        """
        if action == "get_treatments":
            return self.get_available_treatments(
                kwargs.get("skin_type", "normal"),
                kwargs.get("concerns", [])
            )
        
        elif action == "get_available_slots":
            return self.get_available_slots(
                kwargs.get("treatment_id"),
                kwargs.get("start_date"),
                kwargs.get("end_date")
            )
        
        elif action == "book_appointment":
            # Implementação simplificada do agendamento
            slot = kwargs.get("slot")
            customer_id = kwargs.get("customer_id")
            
            if not slot or not customer_id:
                logger.error("Dados insuficientes para agendamento")
                return {"success": False, "error": "Dados insuficientes para agendamento"}
            
            # Em uma implementação real, verificaria conflitos e salvaria no banco de dados
            return {
                "success": True,
                "appointment_id": f"app-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "details": {
                    "customer_id": customer_id,
                    "treatment_id": slot["treatment_id"],
                    "treatment_name": slot["treatment_name"],
                    "professional_id": slot["professional_id"],
                    "professional_name": slot["professional_name"],
                    "date": slot["date"],
                    "time": slot["time"],
                    "duration_minutes": slot["duration_minutes"]
                }
            }
        
        else:
            logger.error(f"Ação desconhecida: {action}")
            return {"success": False, "error": f"Ação desconhecida: {action}"}
