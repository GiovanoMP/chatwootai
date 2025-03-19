"""
Script para testar a integração com o Chatwoot.

Este script simula o recebimento de uma mensagem do Chatwoot e testa
o processamento dessa mensagem pelo sistema Hub-and-Spoke.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar os componentes necessários
from unittest.mock import MagicMock

# Criar mocks para os componentes que podem não estar disponíveis
class MockMemorySystem:
    def __init__(self):
        self.contexts = {}
    
    def get_conversation_context(self, conversation_id):
        return self.contexts.get(conversation_id, {})
    
    def update_conversation_context(self, conversation_id, context):
        self.contexts[conversation_id] = context
        return context

class MockVectorTool:
    def search(self, query, **kwargs):
        return [{"content": "Resultado simulado para: " + query, "score": 0.95}]

class MockDBTool:
    def search(self, query, **kwargs):
        return [{"id": 1, "name": "Resultado simulado", "description": "Descrição simulada"}]

class MockCacheTool:
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value, ttl=None):
        self.cache[key] = value

# Criar um mock para o HubCrew
class MockHubCrew:
    def __init__(self, memory_system, vector_tool, db_tool, cache_tool):
        self.memory_system = memory_system
        self.vector_tool = vector_tool
        self.db_tool = db_tool
        self.cache_tool = cache_tool
        
    def process_message(self, message, conversation_id, channel_type):
        # Simular o processamento baseado no conteúdo da mensagem
        content = message['content'].lower()
        
        if 'produto' in content or 'comprar' in content or 'preço' in content:
            crew = "Sales"
            confidence = 0.9
            reasoning = "A mensagem contém perguntas sobre produtos ou compras"
        elif 'problema' in content or 'ajuda' in content or 'suporte' in content:
            crew = "Support"
            confidence = 0.85
            reasoning = "A mensagem indica um problema que precisa de suporte"
        elif 'agendar' in content or 'horário' in content or 'marcar' in content:
            crew = "Scheduling"
            confidence = 0.8
            reasoning = "A mensagem está relacionada a agendamento"
        else:
            crew = "General"
            confidence = 0.6
            reasoning = "Mensagem genérica sem indicação clara de intenção"
        
        # Simular o contexto e o resultado
        context = self.memory_system.get_conversation_context(conversation_id) or {}
        context['messages'] = context.get('messages', []) + [message]
        context['last_message'] = message
        context['channel_type'] = channel_type
        self.memory_system.update_conversation_context(conversation_id, context)
        
        return {
            "routing": {
                "crew": crew,
                "confidence": confidence,
                "reasoning": reasoning
            },
            "context": context,
            "conversation_id": conversation_id,
            "message_id": message.get("id")
        }

def create_mock_message(content: str, sender_name: str = "Cliente Teste") -> Dict[str, Any]:
    """
    Cria uma mensagem simulada no formato que seria recebido do Chatwoot.
    
    Args:
        content: Conteúdo da mensagem
        sender_name: Nome do remetente
        
    Returns:
        Mensagem simulada
    """
    return {
        "id": f"msg_{datetime.now().timestamp()}",
        "content": content,
        "sender": {
            "id": "client123",
            "name": sender_name,
            "email": "cliente@teste.com"
        },
        "created_at": datetime.now().isoformat(),
        "is_user": True
    }

def test_message_processing():
    """
    Testa o processamento de uma mensagem pelo HubCrew.
    """
    logger.info("Iniciando teste de integração com Chatwoot")
    
    try:
        # Inicializar componentes com mocks
        logger.info("Inicializando componentes com mocks...")
        memory_system = MockMemorySystem()
        vector_tool = MockVectorTool()
        db_tool = MockDBTool()
        cache_tool = MockCacheTool()
        
        # Criar o HubCrew
        logger.info("Criando MockHubCrew...")
        hub_crew = MockHubCrew(
            memory_system=memory_system,
            vector_tool=vector_tool,
            db_tool=db_tool,
            cache_tool=cache_tool
        )
        
        # Criar mensagens de teste
        test_messages = [
            create_mock_message("Olá, gostaria de saber mais sobre seus produtos de beleza"),
            create_mock_message("Estou com um problema no meu pedido #12345"),
            create_mock_message("Quero agendar uma consulta para amanhã"),
            create_mock_message("Qual o horário de funcionamento da loja?")
        ]
        
        # O MockHubCrew já tem o método process_message implementado
        
        # Processar cada mensagem
        for i, message in enumerate(test_messages):
            logger.info(f"Processando mensagem de teste {i+1}: {message['content']}")
            
            # Gerar um ID de conversa único
            conversation_id = f"conv_{i+1}"
            
            # Processar a mensagem usando o mock
            result = hub_crew.process_message(
                message=message,
                conversation_id=conversation_id,
                channel_type="whatsapp"
            )
            
            # Exibir o resultado
            logger.info(f"Resultado do processamento:")
            logger.info(f"  - Mensagem: {message['content']}")
            logger.info(f"  - Roteamento: {result['routing']['crew']}")
            logger.info(f"  - Confiança: {result['routing']['confidence']}")
            logger.info(f"  - Raciocínio: {result['routing']['reasoning']}")
            logger.info("-" * 80)
        
        logger.info("Teste de integração concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o teste de integração: {e}", exc_info=True)

if __name__ == "__main__":
    test_message_processing()
