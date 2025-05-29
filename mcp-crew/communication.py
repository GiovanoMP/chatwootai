"""
Protocolo de Comunicação para o MCP-Crew.

Este módulo é responsável pela comunicação entre agentes e sistemas, incluindo:
- Definição de protocolos de mensagens
- Roteamento de mensagens entre agentes
- Comunicação com MCPs externos
- Gerenciamento de filas de mensagens
"""

import asyncio
import json
import logging
import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union

from ..utils.logging import get_logger
from ..utils.serialization import serialize_message, deserialize_message

logger = get_logger(__name__)

class MessageType(Enum):
    """Tipos de mensagens no sistema."""
    COMMAND = "command"       # Comando para execução
    QUERY = "query"           # Consulta de informação
    RESPONSE = "response"     # Resposta a um comando ou consulta
    EVENT = "event"           # Notificação de evento
    ERROR = "error"           # Notificação de erro
    HEARTBEAT = "heartbeat"   # Mensagem de verificação de vida


class Message:
    """
    Representa uma mensagem no sistema MCP-Crew.
    
    Atributos:
        id (str): Identificador único da mensagem
        type (MessageType): Tipo da mensagem
        sender_id (str): ID do remetente
        recipient_id (Optional[str]): ID do destinatário (None para broadcast)
        content (Dict): Conteúdo da mensagem
        timestamp (float): Timestamp da mensagem
        correlation_id (Optional[str]): ID de correlação para respostas
        metadata (Dict): Metadados adicionais
    """
    
    def __init__(
        self,
        message_type: MessageType,
        sender_id: str,
        content: Dict[str, Any],
        recipient_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa uma nova mensagem.
        
        Args:
            message_type: Tipo da mensagem
            sender_id: ID do remetente
            content: Conteúdo da mensagem
            recipient_id: ID do destinatário (None para broadcast)
            correlation_id: ID de correlação para respostas
            metadata: Metadados adicionais
        """
        self.id = str(uuid.uuid4())
        self.type = message_type
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.timestamp = time.time()
        self.correlation_id = correlation_id
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a mensagem para um dicionário.
        
        Returns:
            Dicionário representando a mensagem
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Cria uma mensagem a partir de um dicionário.
        
        Args:
            data: Dicionário contendo os dados da mensagem
            
        Returns:
            Instância de Message
        """
        message = cls(
            message_type=MessageType(data["type"]),
            sender_id=data["sender_id"],
            content=data["content"],
            recipient_id=data.get("recipient_id"),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {})
        )
        message.id = data["id"]
        message.timestamp = data["timestamp"]
        return message
    
    def create_response(self, content: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> 'Message':
        """
        Cria uma mensagem de resposta para esta mensagem.
        
        Args:
            content: Conteúdo da resposta
            metadata: Metadados adicionais
            
        Returns:
            Mensagem de resposta
        """
        return Message(
            message_type=MessageType.RESPONSE,
            sender_id=self.recipient_id or "system",
            content=content,
            recipient_id=self.sender_id,
            correlation_id=self.id,
            metadata=metadata
        )
    
    def create_error_response(self, error_message: str, error_code: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> 'Message':
        """
        Cria uma mensagem de erro em resposta a esta mensagem.
        
        Args:
            error_message: Mensagem de erro
            error_code: Código de erro
            metadata: Metadados adicionais
            
        Returns:
            Mensagem de erro
        """
        return Message(
            message_type=MessageType.ERROR,
            sender_id=self.recipient_id or "system",
            content={
                "error_message": error_message,
                "error_code": error_code,
                "original_message_id": self.id
            },
            recipient_id=self.sender_id,
            correlation_id=self.id,
            metadata=metadata
        )


class MessageHandler:
    """
    Manipulador de mensagens para processamento de mensagens recebidas.
    
    Esta classe define a interface para manipuladores de mensagens
    que podem ser registrados no CommunicationProtocol.
    """
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """
        Processa uma mensagem recebida.
        
        Args:
            message: Mensagem a ser processada
            
        Returns:
            Mensagem de resposta ou None
        """
        raise NotImplementedError("Subclasses devem implementar handle_message")


class CommunicationProtocol:
    """
    Protocolo de comunicação para o MCP-Crew.
    
    Responsável por gerenciar a comunicação entre agentes e sistemas,
    incluindo roteamento de mensagens, filas e callbacks.
    """
    
    def __init__(self):
        """Inicializa o protocolo de comunicação."""
        self.message_handlers: Dict[str, List[MessageHandler]] = {}
        self.response_callbacks: Dict[str, Callable[[Message], None]] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.broadcast_subscribers: List[str] = []
        
        logger.info("CommunicationProtocol inicializado")
    
    def register_handler(self, entity_id: str, handler: MessageHandler) -> None:
        """
        Registra um manipulador de mensagens para uma entidade.
        
        Args:
            entity_id: ID da entidade (agente, sistema, etc.)
            handler: Manipulador de mensagens
        """
        if entity_id not in self.message_handlers:
            self.message_handlers[entity_id] = []
        
        self.message_handlers[entity_id].append(handler)
        logger.debug(f"Manipulador registrado para {entity_id}: {handler.__class__.__name__}")
    
    def unregister_handler(self, entity_id: str, handler: MessageHandler) -> bool:
        """
        Remove um manipulador de mensagens.
        
        Args:
            entity_id: ID da entidade
            handler: Manipulador a ser removido
            
        Returns:
            True se o manipulador foi removido, False caso contrário
        """
        if entity_id in self.message_handlers and handler in self.message_handlers[entity_id]:
            self.message_handlers[entity_id].remove(handler)
            logger.debug(f"Manipulador removido de {entity_id}: {handler.__class__.__name__}")
            return True
        return False
    
    def subscribe_to_broadcasts(self, entity_id: str) -> None:
        """
        Inscreve uma entidade para receber mensagens de broadcast.
        
        Args:
            entity_id: ID da entidade
        """
        if entity_id not in self.broadcast_subscribers:
            self.broadcast_subscribers.append(entity_id)
            logger.debug(f"Entidade inscrita para broadcasts: {entity_id}")
    
    def unsubscribe_from_broadcasts(self, entity_id: str) -> None:
        """
        Cancela a inscrição de uma entidade para mensagens de broadcast.
        
        Args:
            entity_id: ID da entidade
        """
        if entity_id in self.broadcast_subscribers:
            self.broadcast_subscribers.remove(entity_id)
            logger.debug(f"Entidade desinscrita de broadcasts: {entity_id}")
    
    async def send_message(
        self,
        message: Message,
        response_callback: Optional[Callable[[Message], None]] = None,
        timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Envia uma mensagem e opcionalmente aguarda resposta.
        
        Args:
            message: Mensagem a ser enviada
            response_callback: Callback para resposta assíncrona
            timeout: Timeout para aguardar resposta (None para não aguardar)
            
        Returns:
            Mensagem de resposta ou None se não houver resposta ou timeout
        """
        # Registra callback para resposta, se fornecido
        if response_callback:
            self.response_callbacks[message.id] = response_callback
        
        # Broadcast (sem destinatário específico)
        if message.recipient_id is None:
            return await self._handle_broadcast(message)
        
        # Mensagem direcionada
        return await self._handle_directed_message(message, timeout)
    
    async def _handle_broadcast(self, message: Message) -> None:
        """
        Processa uma mensagem de broadcast.
        
        Args:
            message: Mensagem de broadcast
        """
        logger.debug(f"Enviando broadcast de {message.sender_id}: {message.type.value}")
        
        tasks = []
        for entity_id in self.broadcast_subscribers:
            if entity_id != message.sender_id:  # Não envia para o remetente
                # Cria uma cópia da mensagem com destinatário específico
                directed_message = Message(
                    message_type=message.type,
                    sender_id=message.sender_id,
                    content=message.content,
                    recipient_id=entity_id,
                    correlation_id=message.correlation_id,
                    metadata=message.metadata
                )
                
                # Processa a mensagem de forma assíncrona
                tasks.append(self._handle_directed_message(directed_message, None))
        
        # Aguarda todas as tarefas completarem
        if tasks:
            await asyncio.gather(*tasks)
    
    async def _handle_directed_message(self, message: Message, timeout: Optional[float]) -> Optional[Message]:
        """
        Processa uma mensagem direcionada a um destinatário específico.
        
        Args:
            message: Mensagem direcionada
            timeout: Timeout para aguardar resposta
            
        Returns:
            Mensagem de resposta ou None
        """
        recipient_id = message.recipient_id
        logger.debug(f"Enviando mensagem de {message.sender_id} para {recipient_id}: {message.type.value}")
        
        # Verifica se o destinatário tem uma fila de mensagens
        if recipient_id not in self.message_queues:
            self.message_queues[recipient_id] = asyncio.Queue()
        
        # Coloca a mensagem na fila do destinatário
        await self.message_queues[recipient_id].put(message)
        
        # Se não há timeout, não aguarda resposta
        if timeout is None:
            return None
        
        # Cria uma future para aguardar a resposta
        response_future = asyncio.Future()
        
        # Registra um callback para definir o resultado da future
        def set_response(response: Message) -> None:
            if not response_future.done():
                response_future.set_result(response)
        
        # Registra o callback para a resposta
        self.response_callbacks[message.id] = set_response
        
        try:
            # Aguarda a resposta com timeout
            return await asyncio.wait_for(response_future, timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout aguardando resposta para mensagem {message.id}")
            # Remove o callback
            self.response_callbacks.pop(message.id, None)
            return None
    
    async def process_messages(self, entity_id: str) -> None:
        """
        Processa mensagens na fila de uma entidade.
        
        Este método deve ser chamado em um loop para processar
        continuamente as mensagens recebidas.
        
        Args:
            entity_id: ID da entidade
        """
        # Cria a fila se não existir
        if entity_id not in self.message_queues:
            self.message_queues[entity_id] = asyncio.Queue()
        
        queue = self.message_queues[entity_id]
        
        # Obtém a próxima mensagem da fila
        message = await queue.get()
        
        try:
            # Processa a mensagem com os manipuladores registrados
            if entity_id in self.message_handlers:
                for handler in self.message_handlers[entity_id]:
                    try:
                        response = await handler.handle_message(message)
                        if response:
                            # Se há uma resposta, envia de volta ao remetente
                            await self.send_message(response)
                    except Exception as e:
                        logger.error(f"Erro ao processar mensagem {message.id} com {handler.__class__.__name__}: {e}")
                        # Envia resposta de erro
                        error_response = message.create_error_response(
                            error_message=f"Erro ao processar mensagem: {str(e)}",
                            error_code="PROCESSING_ERROR"
                        )
                        await self.send_message(error_response)
        finally:
            # Marca a tarefa como concluída
            queue.task_done()
    
    async def handle_response(self, response: Message) -> None:
        """
        Processa uma mensagem de resposta.
        
        Args:
            response: Mensagem de resposta
        """
        # Verifica se é uma resposta (deve ter correlation_id)
        if not response.correlation_id:
            logger.warning(f"Mensagem de resposta sem correlation_id: {response.id}")
            return
        
        # Verifica se há um callback registrado para esta resposta
        if response.correlation_id in self.response_callbacks:
            callback = self.response_callbacks.pop(response.correlation_id)
            try:
                callback(response)
            except Exception as e:
                logger.error(f"Erro ao executar callback para resposta {response.id}: {e}")
        else:
            logger.debug(f"Nenhum callback registrado para resposta {response.id} (correlation_id: {response.correlation_id})")
    
    def create_message(
        self,
        sender_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        recipient_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Cria uma nova mensagem.
        
        Args:
            sender_id: ID do remetente
            message_type: Tipo da mensagem
            content: Conteúdo da mensagem
            recipient_id: ID do destinatário (None para broadcast)
            correlation_id: ID de correlação para respostas
            metadata: Metadados adicionais
            
        Returns:
            Nova mensagem
        """
        return Message(
            message_type=message_type,
            sender_id=sender_id,
            content=content,
            recipient_id=recipie
(Content truncated due to size limit. Use line ranges to read in chunks)