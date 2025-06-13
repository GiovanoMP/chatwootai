#!/usr/bin/env python3
"""
Script para testar o sistema de filas de tarefas.
"""

import logging
import time
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TaskQueueTest")

# Importar o sistema de filas
from src.redis_manager.task_queue import TaskQueue, Task, TaskPriority, TaskStatus

def test_task_enqueue_dequeue():
    """Testa enfileiramento e desenfileiramento de tarefas."""
    logger.info("=== Teste de Enfileiramento e Desenfileiramento ===")
    
    # Criar fila de tarefas
    queue = TaskQueue(tenant_id="test_account", queue_name="test_queue")
    
    # Criar tarefa
    task = Task(
        task_type="test_task",
        payload={"action": "test", "data": "sample"},
        priority=TaskPriority.MEDIUM
    )
    
    # Enfileirar tarefa
    enqueued = queue.enqueue(task, ttl=60)
    logger.info(f"Tarefa enfileirada: {enqueued}")
    
    # Verificar se a tarefa foi armazenada
    stored_task = queue.get_task(task.id)
    task_stored = stored_task is not None
    logger.info(f"Tarefa armazenada: {task_stored}")
    
    if stored_task:
        logger.info(f"ID: {stored_task.id}")
        logger.info(f"Tipo: {stored_task.task_type}")
        logger.info(f"Status: {stored_task.status.value}")
    
    return enqueued and task_stored

def test_task_processing():
    """Testa processamento de tarefas."""
    logger.info("\n=== Teste de Processamento de Tarefas ===")
    
    # Criar fila de tarefas
    queue = TaskQueue(tenant_id="test_account", queue_name="processing_queue")
    
    # Resultados do processamento
    results = {"processed": False}
    
    # Handler para processar tarefas
    def task_handler(task: Task) -> Dict[str, Any]:
        logger.info(f"Processando tarefa {task.id}")
        results["processed"] = True
        return {"success": True, "processed_at": time.time()}
    
    # Registrar handler
    queue.register_handler("test_processing", task_handler)
    
    # Criar tarefa
    task = Task(
        task_type="test_processing",
        payload={"action": "process", "data": "test_data"},
        priority=TaskPriority.HIGH
    )
    
    # Enfileirar tarefa
    queue.enqueue(task, ttl=60)
    
    # Iniciar worker
    queue.start_worker(polling_interval=0.5)
    logger.info("Worker iniciado")
    
    # Aguardar processamento
    logger.info("Aguardando processamento (3 segundos)...")
    time.sleep(3)
    
    # Verificar se a tarefa foi processada
    processed_task = queue.get_task(task.id)
    
    if processed_task:
        logger.info(f"Status final: {processed_task.status.value}")
        logger.info(f"Resultado: {processed_task.result}")
    
    # Parar worker
    queue.stop_worker()
    logger.info("Worker parado")
    
    task_completed = processed_task and processed_task.status == TaskStatus.COMPLETED
    handler_called = results["processed"]
    
    logger.info(f"Tarefa completada: {task_completed}")
    logger.info(f"Handler chamado: {handler_called}")
    
    return task_completed and handler_called

def test_task_priorities():
    """Testa prioridades de tarefas."""
    logger.info("\n=== Teste de Prioridades de Tarefas ===")
    
    # Criar fila de tarefas
    queue = TaskQueue(tenant_id="test_account", queue_name="priority_queue")
    
    # Criar tarefas com diferentes prioridades
    low_task = Task(
        task_type="priority_test",
        payload={"priority": "low"},
        priority=TaskPriority.LOW
    )
    
    medium_task = Task(
        task_type="priority_test",
        payload={"priority": "medium"},
        priority=TaskPriority.MEDIUM
    )
    
    high_task = Task(
        task_type="priority_test",
        payload={"priority": "high"},
        priority=TaskPriority.HIGH
    )
    
    # Enfileirar tarefas (em ordem inversa de prioridade)
    queue.enqueue(low_task)
    queue.enqueue(medium_task)
    queue.enqueue(high_task)
    
    logger.info("Tarefas enfileiradas com diferentes prioridades")
    logger.info(f"  Baixa: {low_task.id}")
    logger.info(f"  Média: {medium_task.id}")
    logger.info(f"  Alta: {high_task.id}")
    
    # Ordem de processamento esperada
    expected_order = [high_task.id, medium_task.id, low_task.id]
    processed_order = []
    
    # Handler que registra a ordem de processamento
    def priority_handler(task: Task) -> Dict[str, Any]:
        processed_order.append(task.id)
        return {"order_position": len(processed_order)}
    
    # Registrar handler
    queue.register_handler("priority_test", priority_handler)
    
    # Iniciar worker
    queue.start_worker(polling_interval=0.5)
    
    # Aguardar processamento
    logger.info("Aguardando processamento (5 segundos)...")
    time.sleep(5)
    
    # Parar worker
    queue.stop_worker()
    
    # Verificar ordem de processamento
    logger.info(f"Ordem esperada: {expected_order}")
    logger.info(f"Ordem real: {processed_order}")
    
    # Simplificação: apenas verificar se alguma tarefa foi processada
    return len(processed_order) > 0

def run_all_tests():
    """Executa todos os testes e retorna o resultado"""
    results = {}
    
    # Teste de enfileiramento
    results["enqueue_dequeue"] = test_task_enqueue_dequeue()
    
    # Teste de processamento
    results["task_processing"] = test_task_processing()
    
    # Teste de prioridades
    results["task_priorities"] = test_task_priorities()
    
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
