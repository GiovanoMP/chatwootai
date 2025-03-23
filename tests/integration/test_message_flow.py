"""
Teste de integração para o fluxo completo de mensagens na arquitetura hub-and-spoke.

Este teste simula todo o caminho de uma mensagem do cliente, iniciando no webhook do Chatwoot
e passando por todos os componentes do sistema até o retorno da resposta.

O fluxo completo testado é:
1. Chatwoot Webhook -> WebhookHandler
2. WebhookHandler -> HubCrew
3. HubCrew -> SalesCrew (via roteamento)
4. SalesCrew processa a mensagem com domínio adequado
5. Resposta retorna pelo caminho inverso até o cliente
"""

import json
import asyncio
import logging
import unittest
from unittest.mock import patch, MagicMock

# Configuração de logging para o teste
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importações dos componentes do sistema
from src.webhook.webhook_handler import ChatwootWebhookHandler
from src.core.hub import HubCrew
from src.core.memory import MemorySystem
from src.core.data_service_hub import DataServiceHub
from src.core.domain.domain_manager import DomainManager
from src.crews.sales_crew import SalesCrew
from src.plugins.core.plugin_manager import PluginManager


class TestMessageFlow(unittest.TestCase):
    """Testes para o fluxo completo de processamento de mensagens."""
    
    async def asyncSetUp(self):
        """Configuração assíncrona para o teste."""
        logger.info("Inicializando componentes do sistema para teste...")
        
        # 1. Inicializar o sistema de memória
        self.memory_system = MemorySystem()
        
        # 2. Inicializar o gerenciador de domínio
        self.domain_manager = DomainManager()
        
        # 3. Definir o domínio ativo como cosméticos
        # Em um ambiente real, isso seria determinado dinamicamente
        self.domain_manager.set_active_domain("cosmetics")
        logger.info(f"Domínio ativo definido como: {self.domain_manager.active_domain}")
        
        # 4. Inicializar o gerenciador de plugins
        self.plugin_manager = PluginManager(config={})
        
        # 5. Inicializar o hub central de serviços de dados
        self.data_service_hub = DataServiceHub()
        
        # 6. Inicializar o HubCrew que orquestrará o fluxo de mensagens
        self.hub_crew = HubCrew(
            memory_system=self.memory_system,
            data_service_hub=self.data_service_hub
        )
        
        # 7. Inicializar as crews funcionais necessárias
        self.sales_crew = SalesCrew(
            memory_system=self.memory_system,
            data_service_hub=self.data_service_hub,
            domain_manager=self.domain_manager,
            plugin_manager=self.plugin_manager
        )
        
        # 8. Conectar as crews funcionais ao HubCrew para roteamento
        # No ambiente real, isso seria feito no setup do sistema
        functional_crews = {
            "sales": self.sales_crew
        }
        # Adicionar ao dict do HubCrew para que possa rotear mensagens
        setattr(self.hub_crew, "_functional_crews", functional_crews)
        
        # 9. Inicializar o webhook handler que recebe as mensagens do Chatwoot
        self.webhook_handler = ChatwootWebhookHandler(
            hub_crew=self.hub_crew,
            config={"channel_mapping": {"1": "whatsapp"}}
        )
        
        logger.info("Componentes inicializados com sucesso!")
    
    async def asyncTearDown(self):
        """Limpeza após o teste."""
        logger.info("Limpando recursos após o teste...")
        # Limpar recursos, fechar conexões, etc.
    
    @patch('src.crews.sales_crew.SalesCrew.process')
    async def test_full_message_flow(self, mock_sales_process):
        """
        Testa o fluxo completo de processamento de mensagens.
        
        Este teste verifica se uma mensagem recebida no webhook é
        corretamente processada, roteada e respondida.
        """
        # Configurar o mock para retornar uma resposta simulada
        mock_response = {
            "response": {
                "content": "Sim, temos várias opções de cremes para as mãos na linha de cosméticos.",
                "type": "text",
                "timestamp": "2023-06-01T10:05:00Z"
            },
            "processing_info": {
                "crew_type": "sales",
                "domain": "cosmetics",
                "processing_time": "N/A"
            }
        }
        mock_sales_process.return_value = mock_response
        
        # Mensagem de teste simulando webhook do Chatwoot
        test_webhook = {
            "message": {
                "id": 12345,
                "content": "Você tem creme para as mãos?",
                "message_type": "incoming",
                "created_at": "2023-06-01T10:00:00Z"
            },
            "conversation": {
                "id": 67890,
                "inbox_id": 1
            },
            "contact": {
                "id": 54321,
                "name": "Cliente Teste"
            }
        }
        
        # 1. Processar a mensagem através do webhook handler
        logger.info("Iniciando processamento da mensagem de teste...")
        
        # Usar um mock para a função enviar resposta ao Chatwoot
        with patch.object(self.webhook_handler, '_send_reply_to_chatwoot', 
                         return_value=None) as mock_send_reply:
            
            # Processar a mensagem
            await self.webhook_handler.process_webhook(test_webhook)
            
            # 2. Verificar se a mensagem foi roteada para a SalesCrew
            mock_sales_process.assert_called_once()
            
            # 3. Verificar o conteúdo passado para o SalesCrew.process
            call_args = mock_sales_process.call_args_list[0][0]
            message_arg = call_args[0]
            
            # Verificar se a mensagem foi normalizada corretamente
            self.assertEqual(message_arg['content'], "Você tem creme para as mãos?")
            self.assertEqual(message_arg['sender_type'], "customer")
            
            # 4. Verificar se a resposta foi enviada de volta
            mock_send_reply.assert_called_once()
            reply_args = mock_send_reply.call_args_list[0][1]
            
            # Verificar o conteúdo da resposta
            self.assertEqual(reply_args['content'], mock_response['response']['content'])
            self.assertFalse(reply_args['private'])
            
            logger.info("Teste do fluxo de mensagens concluído com sucesso!")


async def run_tests():
    """Executar os testes assíncronos."""
    test = TestMessageFlow()
    await test.asyncSetUp()
    try:
        await test.test_full_message_flow()
    finally:
        await test.asyncTearDown()
    
    print("Todos os testes concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(run_tests())
