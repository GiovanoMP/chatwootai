#!/usr/bin/env python3
"""
Script para testar o sistema de eventos do Redis.
"""

import logging
import time
from typing import List

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EventSystemTest")

# Importar o sistema de eventos
from src.redis_manager.event_system import Event, EventManager, EventType, EventPriority

def test_event_publishing():
    """Testa a publicação de eventos"""
    logger.info("=== Teste de Publicação de Eventos ===")
    
    # Criar gerenciador de eventos
    event_manager = EventManager(tenant_id="test_account")
    
    # Criar evento
    event = Event(
        event_type=EventType.SYSTEM,
        data={"message": "Teste de evento", "timestamp": time.time()},
        priority=EventPriority.HIGH
    )
    
    # Publicar evento
    success = event_manager.publish(event, "test_stream")
    logger.info(f"Evento publicado: {success}")
    
    return success

def test_event_subscription():
    """Testa a assinatura e recebimento de eventos"""
    logger.info("\n=== Teste de Assinatura de Eventos ===")
    
    # Criar gerenciador de eventos
    event_manager = EventManager(tenant_id="test_account")
    
    # Lista para armazenar eventos recebidos
    received_events: List[Event] = []
    
    # Callback para processar eventos
    def event_callback(event: Event):
        logger.info(f"Evento recebido: {event.event_type.value}, dados: {event.data}")
        received_events.append(event)
    
    # Assinar stream
    event_manager.subscribe("test_stream", event_callback)
    logger.info("Assinatura realizada")
    
    # Publicar evento
    event = Event(
        event_type=EventType.SYSTEM,
        data={"message": "Teste de assinatura", "timestamp": time.time()},
        priority=EventPriority.MEDIUM
    )
    event_manager.publish(event, "test_stream")
    logger.info("Evento publicado para teste de assinatura")
    
    # Aguardar recebimento do evento
    logger.info("Aguardando recebimento do evento (5 segundos)...")
    time.sleep(5)
    
    # Verificar se o evento foi recebido
    success = len(received_events) > 0
    logger.info(f"Eventos recebidos: {len(received_events)}")
    
    # Parar o consumidor
    event_manager.stop()
    
    return success

def run_all_tests():
    """Executa todos os testes e retorna o resultado"""
    results = {}
    
    # Teste de publicação
    results["event_publishing"] = test_event_publishing()
    
    # Teste de assinatura
    results["event_subscription"] = test_event_subscription()
    
    # Resumo
    logger.info("\n=== Resumo dos Testes ===")
    for test, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test}: {status}")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_all_tests()
    exit_code = 0 if success else 1
    logger.info(f"\nTestes {'concluídos com sucesso' if success else 'falharam'}")
    exit(exit_code)
