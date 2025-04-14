"""
Testes unitários para o agente de embedding de regras de negócio.

Este módulo contém testes para verificar o funcionamento do agente de embedding
de regras de negócio.
"""

import asyncio
import os
import sys
import unittest
from typing import Dict, Any
from datetime import date

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from odoo_api.embedding_agents.business_rules_agent import get_business_rules_agent

class TestBusinessRulesAgent(unittest.TestCase):
    """Testes para o agente de embedding de regras de negócio."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.loop = asyncio.get_event_loop()
        
        # Dados de teste
        self.business_rule = {
            "id": 1,
            "name": "Horário de Funcionamento",
            "description": "Nossa loja funciona de segunda a sexta, das 9h às 18h, e aos sábados das 9h às 13h.",
            "type": "business_hours",
            "is_temporary": False,
            "rule_data": {
                "days": [0, 1, 2, 3, 4, 5],
                "start_time": "09:00",
                "end_time": "18:00",
                "saturday_hours": {
                    "start_time": "09:00",
                    "end_time": "13:00"
                }
            }
        }
        
        self.temporary_rule = {
            "id": 2,
            "name": "Promoção de Aniversário",
            "description": "Em comemoração ao aniversário da loja, todos os produtos estão com 20% de desconto durante o mês de julho.",
            "type": "promotion",
            "is_temporary": True,
            "start_date": date(2023, 7, 1),
            "end_date": date(2023, 7, 31),
            "rule_data": {
                "discount_percentage": 20,
                "products": "all"
            }
        }
    
    def test_format_rule_data(self):
        """Testar formatação de dados da regra."""
        async def _test():
            # Obter agente
            agent = await get_business_rules_agent()
            
            # Testar formatação de regra permanente
            formatted_text = agent._format_rule_data(self.business_rule)
            
            # Verificar se contém informações importantes
            self.assertIn("Horário de Funcionamento", formatted_text)
            self.assertIn("Nossa loja funciona", formatted_text)
            self.assertIn("business_hours", formatted_text)
            self.assertIn("days", formatted_text)
            self.assertIn("start_time", formatted_text)
            self.assertIn("end_time", formatted_text)
            
            # Testar formatação de regra temporária
            formatted_text = agent._format_rule_data(self.temporary_rule)
            
            # Verificar se contém informações importantes
            self.assertIn("Promoção de Aniversário", formatted_text)
            self.assertIn("20% de desconto", formatted_text)
            self.assertIn("promotion", formatted_text)
            self.assertIn("discount_percentage", formatted_text)
            self.assertIn("Regra temporária", formatted_text)
            self.assertIn("2023-07-01", formatted_text)
            self.assertIn("2023-07-31", formatted_text)
        
        self.loop.run_until_complete(_test())
    
    def test_process_data(self):
        """Testar processamento de dados da regra."""
        async def _test():
            # Obter agente
            agent = await get_business_rules_agent()
            
            # Testar processamento sem área de negócio
            processed_text = await agent.process_data(self.business_rule)
            
            # Verificar se contém informações importantes
            self.assertIn("Horário de Funcionamento", processed_text)
            self.assertIn("segunda a sexta", processed_text.lower())
            self.assertIn("09:00", processed_text)
            self.assertIn("sábados", processed_text.lower())
            
            # Testar processamento com área de negócio
            business_area = "varejo de móveis"
            processed_text_with_area = await agent.process_data(
                self.business_rule,
                business_area
            )
            
            # Verificar se contém informações importantes
            self.assertIn("Horário de Funcionamento", processed_text_with_area)
            self.assertIn("segunda", processed_text_with_area.lower())
            self.assertIn("09:00", processed_text_with_area)
            self.assertIn("sábados", processed_text_with_area.lower())
            
            # Verificar se o contexto da área de negócio foi considerado
            self.assertIn("móveis", processed_text_with_area.lower())
            self.assertIn("móveis", processed_text_with_area.lower())
            
            # Testar processamento de regra temporária
            processed_text = await agent.process_data(self.temporary_rule)
            
            # Verificar se contém informações importantes
            self.assertIn("Promoção de Aniversário", processed_text)
            self.assertIn("20%", processed_text)
            self.assertIn("julho", processed_text.lower())
            self.assertIn("válida", processed_text.lower())
        
        self.loop.run_until_complete(_test())

if __name__ == "__main__":
    unittest.main()
