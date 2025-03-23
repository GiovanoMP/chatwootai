#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste integrado do fluxo de mensagens no sistema ChatwootAI.

Este script testa o fluxo completo de processamento de mensagens:
1. Webhook recebe uma mensagem do Chatwoot
2. Webhook encaminha a mensagem para o HubCrew
3. HubCrew processa e roteia a mensagem para a crew apropriada
4. Crew funcional (ex: SalesCrew) processa a mensagem
5. Resposta é enviada de volta para o Chatwoot

Uso:
    python test_message_flow_integrated.py
"""

import sys
import os
import json
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test_message_flow")

# Adiciona o diretório raiz ao PATH para importações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa os componentes necessários
from src.core.hub import HubCrew
from src.core.memory import MemorySystem
from src.core.data_service_hub import DataServiceHub
from src.crews.sales_crew import SalesCrew
from src.webhook.webhook_handler import ChatwootWebhookHandler


class TestMessageFlow:
    """Classe para testar o fluxo de mensagens no sistema ChatwootAI."""

    def __init__(self):
        """Inicializa o ambiente de teste."""
        # Cria instâncias dos componentes centrais
        self.memory_system = MemorySystem()
        self.data_service_hub = DataServiceHub()
        
        # Cria o HubCrew (componente central da arquitetura hub-and-spoke)
        self.hub_crew = HubCrew(
            memory_system=self.memory_system,
            data_service_hub=self.data_service_hub
        )
        
        # Cria o webhook handler
        self.webhook_handler = ChatwootWebhookHandler(
            hub_crew=self.hub_crew,
            config={
                "chatwoot_api_key": "test_api_key",
                "chatwoot_base_url": "http://localhost:3000",
                "chatwoot_account_id": 1
            }
        )
        
        # Substitui o método de envio de respostas para o Chatwoot
        # para evitar chamadas reais à API durante o teste
        self.webhook_handler._send_reply_to_chatwoot = self._mock_send_reply_to_chatwoot
        
        # Armazena as respostas enviadas para o Chatwoot para verificação
        self.sent_responses = []

    async def _mock_send_reply_to_chatwoot(self, conversation_id: str, content: str, 
                                    private: bool = False, message_type: str = "outgoing") -> Dict[str, Any]:
        """
        Versão de mock do método de envio de respostas para o Chatwoot.
        
        Esta versão apenas registra a resposta que seria enviada sem fazer chamadas reais.
        
        Args:
            conversation_id: ID da conversa
            content: Conteúdo da mensagem
            private: Se a mensagem é privada
            message_type: Tipo da mensagem
            
        Returns:
            Dict com status de sucesso
        """
        logger.info(f"[MOCK] Enviando resposta para Chatwoot: {content[:50]}...")
        
        # Armazena a resposta para verificação posterior
        self.sent_responses.append({
            "conversation_id": conversation_id,
            "content": content,
            "private": private,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "success"}

    def create_mock_webhook_data(self, message_content: str) -> Dict[str, Any]:
        """
        Cria dados simulados de um webhook do Chatwoot.
        
        Args:
            message_content: Conteúdo da mensagem
            
        Returns:
            Dict com dados do webhook simulado
        """
        conversation_id = "12345"
        contact_id = "67890"
        
        return {
            "event": "message_created",
            "message": {
                "id": 42,
                "content": message_content,
                "message_type": 0,  # 0 = incoming (do cliente)
                "content_type": "text",
                "created_at": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "inbox_id": 1,
                "sender": {
                    "id": contact_id,
                    "type": "contact"
                }
            },
            "conversation": {
                "id": conversation_id,
                "inbox_id": 1,
                "contact_id": contact_id,
                "status": "open"
            },
            "contact": {
                "id": contact_id,
                "name": "Cliente Teste",
                "email": "cliente@teste.com",
                "phone_number": "+5511987654321"
            }
        }

    async def test_product_inquiry(self):
        """Testa o fluxo de uma consulta sobre produtos."""
        logger.info("======= TESTE: Consulta sobre Produtos =======")
        
        # Cria um webhook simulando uma pergunta sobre produtos
        webhook_data = self.create_mock_webhook_data("Vocês têm creme para as mãos?")
        
        # Processa o webhook
        result = await self.webhook_handler.process_webhook(webhook_data)
        
        # Verifica se a resposta foi gerada e enviada
        if self.sent_responses:
            logger.info(f"Resposta enviada: {self.sent_responses[-1]['content']}")
        else:
            logger.warning("Nenhuma resposta foi enviada!")
        
        logger.info(f"Resultado do processamento: {result}")
        return result

    async def test_pricing_inquiry(self):
        """Testa o fluxo de uma consulta sobre preços."""
        logger.info("======= TESTE: Consulta sobre Preços =======")
        
        # Cria um webhook simulando uma pergunta sobre preços
        webhook_data = self.create_mock_webhook_data("Quanto custa o protetor solar?")
        
        # Processa o webhook
        result = await self.webhook_handler.process_webhook(webhook_data)
        
        # Verifica se a resposta foi gerada e enviada
        if self.sent_responses:
            logger.info(f"Resposta enviada: {self.sent_responses[-1]['content']}")
        else:
            logger.warning("Nenhuma resposta foi enviada!")
        
        logger.info(f"Resultado do processamento: {result}")
        return result
    
    async def test_greeting(self):
        """Testa o fluxo de uma saudação simples."""
        logger.info("======= TESTE: Saudação Simples =======")
        
        # Cria um webhook simulando uma saudação
        webhook_data = self.create_mock_webhook_data("Olá, bom dia!")
        
        # Processa o webhook
        result = await self.webhook_handler.process_webhook(webhook_data)
        
        # Verifica se a resposta foi gerada e enviada
        if self.sent_responses:
            logger.info(f"Resposta enviada: {self.sent_responses[-1]['content']}")
        else:
            logger.warning("Nenhuma resposta foi enviada!")
        
        logger.info(f"Resultado do processamento: {result}")
        return result

    async def run_all_tests(self):
        """Executa todos os testes em sequência."""
        logger.info("Iniciando testes de fluxo de mensagens...")
        
        # Inicializa uma conversa fictícia
        self.hub_crew.register_conversation("12345", "67890")
        
        # Executa os testes
        await self.test_greeting()
        await self.test_product_inquiry()
        await self.test_pricing_inquiry()
        
        # Finaliza a conversa
        self.hub_crew.finalize_conversation("12345")
        
        logger.info(f"Total de respostas enviadas: {len(self.sent_responses)}")
        logger.info("Testes concluídos!")


async def main():
    """Função principal."""
    test = TestMessageFlow()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
