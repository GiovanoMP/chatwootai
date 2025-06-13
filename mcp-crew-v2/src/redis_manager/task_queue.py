"""
Sistema de Filas de Tarefas usando Redis para o MCP-Crew v2.

Implementa métodos para enfileirar e processar tarefas assíncronas.
"""

import json
import logging
import threading
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from src.redis_manager.redis_manager import redis_manager, DataType

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Prioridades para tarefas."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2

class TaskStatus(Enum):
    """Status possíveis para tarefas."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task:
    """Representa uma tarefa a ser processada."""
    
    def __init__(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = 3
    ):
        self.id = str(uuid.uuid4())
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created_at = time.time()
        self.updated_at = time.time()
        self.max_retries = max_retries
        self.retry_count = 0
        self.result = None
        self.error = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte a tarefa para dicionário."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "result": self.result,
            "error": self.error
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Cria uma tarefa a partir de um dicionário."""
        task = cls(
            task_type=data["task_type"],
            payload=data["payload"],
            priority=TaskPriority(data["priority"]),
            max_retries=data["max_retries"]
        )
        task.id = data["id"]
        task.status = TaskStatus(data["status"])
        task.created_at = data["created_at"]
        task.updated_at = data["updated_at"]
        task.retry_count = data["retry_count"]
        task.result = data.get("result")
        task.error = data.get("error")
        return task

class TaskQueue:
    """Gerencia filas de tarefas usando Redis."""
    
    def __init__(self, tenant_id: str, queue_name: str = "default"):
        """
        Inicializa a fila de tarefas.
        
        Args:
            tenant_id: ID do tenant (account_id)
            queue_name: Nome da fila
        """
        self.tenant_id = tenant_id
        self.queue_name = queue_name
        self.processing = False
        self.task_handlers = {}
        
    def enqueue(self, task: Task, ttl: int = 86400) -> bool:
        """
        Adiciona uma tarefa à fila.
        
        Args:
            task: Tarefa a ser adicionada
            ttl: Tempo de vida da tarefa em segundos (1 dia padrão)
            
        Returns:
            bool: True se adicionada com sucesso
        """
        try:
            # Chave para a lista de tarefas pendentes
            queue_key = f"queue:{self.queue_name}:{task.priority.value}"
            
            # Armazenar detalhes da tarefa
            task_stored = redis_manager.set(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=f"task:{task.id}",
                value=task.to_dict(),
                ttl=ttl
            )
            
            if not task_stored:
                return False
                
            # Adicionar ID da tarefa à fila de prioridade
            result = redis_manager.client.lpush(
                f"{redis_manager.prefix}:{self.tenant_id}:{DataType.QUERY_RESULT}:{queue_key}",
                task.id
            )
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Erro ao enfileirar tarefa: {e}")
            return False
    
    def register_handler(self, task_type: str, handler: Callable[[Task], Any]) -> None:
        """
        Registra um handler para um tipo específico de tarefa.
        
        Args:
            task_type: Tipo de tarefa
            handler: Função que processa a tarefa
        """
        self.task_handlers[task_type] = handler
        logger.debug(f"Handler registrado para tarefas do tipo '{task_type}'")
    
    def start_worker(self, polling_interval: float = 1.0) -> None:
        """
        Inicia um worker para processar tarefas.
        
        Args:
            polling_interval: Intervalo de polling em segundos
        """
        if self.processing:
            logger.warning("Worker já está em execução")
            return
            
        self.processing = True
        thread = threading.Thread(target=self._worker_loop, args=(polling_interval,), daemon=True)
        thread.start()
        logger.info(f"Worker iniciado para fila '{self.queue_name}'")
    
    def stop_worker(self) -> None:
        """Para o worker."""
        self.processing = False
        logger.info(f"Worker parado para fila '{self.queue_name}'")
    
    def _worker_loop(self, polling_interval: float) -> None:
        """
        Loop principal do worker.
        
        Args:
            polling_interval: Intervalo de polling em segundos
        """
        while self.processing:
            try:
                # Verificar tarefas por ordem de prioridade
                for priority in sorted([p.value for p in TaskPriority], reverse=True):
                    queue_key = f"queue:{self.queue_name}:{priority}"
                    
                    # Obter próxima tarefa da fila
                    task_id = redis_manager.client.rpop(
                        f"{redis_manager.prefix}:{self.tenant_id}:{DataType.QUERY_RESULT}:{queue_key}"
                    )
                    
                    if task_id:
                        self._process_task(task_id)
                        break
                        
                # Aguardar próximo ciclo
                time.sleep(polling_interval)
                
            except Exception as e:
                logger.error(f"Erro no loop do worker: {e}")
                time.sleep(polling_interval)
    
    def _process_task(self, task_id: str) -> None:
        """
        Processa uma tarefa.
        
        Args:
            task_id: ID da tarefa
        """
        try:
            # Recuperar detalhes da tarefa
            task_data = redis_manager.get(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=f"task:{task_id}"
            )
            
            if not task_data:
                logger.warning(f"Tarefa {task_id} não encontrada")
                return
                
            # Criar objeto Task
            task = Task.from_dict(task_data)
            
            # Atualizar status
            task.status = TaskStatus.PROCESSING
            task.updated_at = time.time()
            
            # Salvar status atualizado
            redis_manager.set(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=f"task:{task.id}",
                value=task.to_dict()
            )
            
            # Verificar se há handler para o tipo de tarefa
            if task.task_type not in self.task_handlers:
                logger.error(f"Nenhum handler registrado para tarefas do tipo '{task.task_type}'")
                task.status = TaskStatus.FAILED
                task.error = "Handler não encontrado"
                
            else:
                try:
                    # Executar handler
                    handler = self.task_handlers[task.task_type]
                    result = handler(task)
                    
                    # Atualizar tarefa com sucesso
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    
                except Exception as e:
                    logger.error(f"Erro ao processar tarefa {task.id}: {e}")
                    
                    # Verificar se deve tentar novamente
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        task.status = TaskStatus.PENDING
                        task.error = f"Tentativa {task.retry_count}/{task.max_retries} falhou: {str(e)}"
                        
                        # Recolocar na fila
                        queue_key = f"queue:{self.queue_name}:{task.priority.value}"
                        redis_manager.client.lpush(
                            f"{redis_manager.prefix}:{self.tenant_id}:{DataType.QUERY_RESULT}:{queue_key}",
                            task.id
                        )
                    else:
                        # Marcar como falha definitiva
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
            
            # Atualizar tarefa no Redis
            task.updated_at = time.time()
            redis_manager.set(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=f"task:{task.id}",
                value=task.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar tarefa {task_id}: {e}")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Recupera uma tarefa pelo ID.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Task: Objeto Task ou None se não encontrada
        """
        try:
            task_data = redis_manager.get(
                tenant_id=self.tenant_id,
                data_type=DataType.QUERY_RESULT,
                identifier=f"task:{task_id}"
            )
            
            if task_data:
                return Task.from_dict(task_data)
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar tarefa {task_id}: {e}")
            return None
