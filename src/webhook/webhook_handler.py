"""
Webhook Handler para o ChatwootAI.

Este módulo implementa o handler do webhook do Chatwoot, processando as mensagens
recebidas e encaminhando-as para o sistema de agentes.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import traceback

from src.core.hub import HubCrew
from src.core.memory import MemorySystem
from src.core.data_service_hub import DataServiceHub
from src.api.chatwoot.client import ChatwootClient
from src.core.domain import DomainManager
from src.plugins.core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)

class ChatwootWebhookHandler:
    """
    Handler para webhooks do Chatwoot.
    
    Esta classe é responsável por processar os webhooks do Chatwoot,
    normalizar as mensagens e encaminhá-las para o sistema de agentes.
    
    Fluxo de processamento:
    1. Recebe o webhook do Chatwoot
    2. Identifica o tipo de evento
    3. Extrai informações relevantes da mensagem
    4. Normaliza os dados para formato interno
    5. Encaminha para o HubCrew para processamento
    6. Retorna a resposta para o Chatwoot
    """
    
    def __init__(self, hub_crew: HubCrew = None, config: Dict[str, Any] = None):
        """
        Inicializa o handler de webhook.
        
        Args:
            hub_crew: Instância do HubCrew para processamento das mensagens (obrigatório)
            config: Configuração do handler
        """
        self.config = config or {}
        
        # Valida que o HubCrew foi fornecido (elemento central da arquitetura hub-and-spoke)
        if hub_crew is None:
            raise ValueError("hub_crew é obrigatório para o ChatwootWebhookHandler")
            
        # Define o HubCrew que será responsável pelo processamento das mensagens
        self.hub_crew = hub_crew
        
        # Inicializa o cliente do Chatwoot para envio de respostas
        self.chatwoot_client = ChatwootClient(
            base_url=self.config.get("chatwoot_base_url", ""),
            api_token=self.config.get("chatwoot_api_key", "")
        )
        
        # Estatísticas de processamento
        self.stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "response_time_avg": 0,
            "errors": 0
        }
    
    # Removidos os métodos _initialize_functional_crews e _register_crews
    # Na nova arquitetura hub-and-spoke, o HubCrew é responsável pela gestão das crews
    # O webhook handler apenas encaminha mensagens para o HubCrew
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um webhook do Chatwoot.
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        start_time = datetime.now()
        
        try:
            # Incrementa contador de mensagens recebidas
            self.stats["messages_received"] += 1
            
            # Obtém o tipo de evento
            event_type = webhook_data.get("event", "unknown")
            
            # Processa o evento de acordo com o tipo
            if event_type == "message_created":
                result = await self._process_message_created(webhook_data)
            elif event_type == "conversation_created":
                result = self._process_conversation_created(webhook_data)
            elif event_type == "conversation_status_changed":
                result = self._process_conversation_status_changed(webhook_data)
            else:
                logger.warning(f"Tipo de evento desconhecido: {event_type}")
                result = {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}
            
            # Calcula o tempo de processamento
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Atualiza estatísticas
            if result.get("status") != "ignored":
                self.stats["messages_processed"] += 1
                # Atualiza média de tempo de resposta
                n = self.stats["messages_processed"]
                old_avg = self.stats["response_time_avg"]
                self.stats["response_time_avg"] = ((n - 1) * old_avg + processing_time) / n
            
            # Adiciona informações de tempo ao resultado
            result["processing_time"] = f"{processing_time:.3f}s"
            result["stats"] = {
                "messages_received": self.stats["messages_received"],
                "messages_processed": self.stats["messages_processed"],
                "response_time_avg": f"{self.stats['response_time_avg']:.3f}s",
                "errors": self.stats["errors"]
            }
            
            return result
            
        except Exception as e:
            # Incrementa contador de erros
            self.stats["errors"] += 1
            
            # Registra o erro
            logger.error(f"Erro ao processar webhook: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Calcula o tempo de processamento
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Retorna informações sobre o erro
            return {
                "status": "error",
                "error": str(e),
                "processing_time": f"{processing_time:.3f}s"
            }
    
    async def _process_message_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de mensagem criada.
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        # Extrai informações relevantes
        message_data = webhook_data.get("message", {})
        conversation_data = webhook_data.get("conversation", {})
        
        # Verifica se a mensagem é de entrada (do cliente)
        message_type = message_data.get("message_type")
        if message_type != "incoming":
            logger.info(f"Ignorando mensagem não-recebida (tipo: {message_type})")
            return {"status": "ignored", "reason": "Not an incoming message"}
        
        # Obtém dados importantes
        conversation_id = str(conversation_data.get("id", ""))
        inbox_id = conversation_data.get("inbox_id")
        message_content = message_data.get("content", "")
        contact_data = webhook_data.get("contact", {})
        contact_id = str(contact_data.get("id", ""))
        
        # Identifica o tipo de canal com base no inbox_id
        # Isso deve ser configurado de acordo com o seu ambiente
        channel_mapping = self.config.get("channel_mapping", {})
        channel_type = channel_mapping.get(str(inbox_id), "whatsapp")
        
        # Log detalhado
        logger.info(f"Processando mensagem do canal {channel_type}")
        logger.info(f"Conversa: {conversation_id}, Contato: {contact_id}")
        logger.info(f"Conteúdo da mensagem: {message_content[:100]}...")
        
        # Normaliza a mensagem para o formato interno
        normalized_message = {
            "id": message_data.get("id", ""),
            "content": message_content,
            "sender_id": contact_id,
            "sender_type": "customer",
            "timestamp": message_data.get("created_at", datetime.now().isoformat()),
            "conversation_id": conversation_id,
            "channel_type": channel_type,
            "raw_data": message_data
        }
        
        # Processa a mensagem com o HubCrew
        try:
            logger.info("Encaminhando mensagem para processamento pelo HubCrew")
            
            # Verificar se o HubCrew já tem crews funcionais configuradas
            functional_crews = getattr(self.hub_crew, "_functional_crews", None)
            
            # Se não tiver, log de erro e retorno
            if not functional_crews:
                logger.error("HubCrew não tem crews funcionais configuradas")
                return {
                    "status": "error",
                    "error": "HubCrew não tem crews funcionais configuradas",
                    "conversation_id": conversation_id,
                    "has_response": True
                }
            
            # Processar a mensagem pelo HubCrew central (hub-and-spoke model)
            # Passando o dicionário de crews funcionais para processamento direto
            hub_result = await self.hub_crew.process_message(
                message=normalized_message,
                conversation_id=conversation_id,
                channel_type=channel_type,
                functional_crews=functional_crews  # Passamos as crews funcionais disponíveis
            )
            
            logger.info(f"Mensagem processada pelo HubCrew: {hub_result}")
            
            # Extrair informações relevantes do resultado
            routing = hub_result.get("routing", {})
            
            # Se temos uma resposta gerada pela crew funcional
            if hub_result.get("response"):
                response = hub_result["response"]
                
                # Enviar a resposta para o Chatwoot
                await self._send_reply_to_chatwoot(
                    conversation_id=conversation_id,
                    content=response.get("content", ""),
                    private=False,
                    message_type="outgoing"
                )
                
                logger.info(f"Resposta enviada para Chatwoot: {response.get('content', '')[:100]}...")
                
                return {
                    "status": "processed",
                    "crew": routing.get("crew", "unknown"),
                    "confidence": routing.get("confidence", 0),
                    "conversation_id": conversation_id,
                    "has_response": True
                }
            else:
                logger.warning("Nenhuma resposta gerada pela crew funcional")
                return {
                    "status": "processed_no_response",
                    "crew": routing.get("crew", "unknown"),
                    "confidence": routing.get("confidence", 0),
                    "conversation_id": conversation_id,
                    "has_response": False
                }
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com HubCrew: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Em caso de erro, enviamos uma resposta genérica
            try:
                error_message = "Desculpe, estou com dificuldades para processar sua mensagem no momento. Por favor, tente novamente mais tarde."
                await self._send_reply_to_chatwoot(
                    conversation_id=conversation_id,
                    content=error_message,
                    private=False,
                    message_type="outgoing"
                )
            except Exception as reply_error:
                logger.error(f"Erro ao enviar resposta de erro: {str(reply_error)}")
            
            return {
                "status": "error",
                "error": str(e),
                "conversation_id": conversation_id,
                "has_response": True
            }
    
    def _process_conversation_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de conversa criada.
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        conversation_data = webhook_data.get("conversation", {})
        conversation_id = str(conversation_data.get("id", ""))
        contact_data = webhook_data.get("contact", {})
        contact_id = str(contact_data.get("id", ""))
        
        logger.info(f"Nova conversa criada: {conversation_id}, Contato: {contact_id}")
        
        # Registra a nova conversa no sistema de memória através do HubCrew
        # seguindo a arquitetura hub-and-spoke
        try:
            # O HubCrew é o ponto central e tem acesso ao sistema de memória
            self.hub_crew.register_conversation(
                conversation_id=conversation_id,
                customer_id=contact_id
            )
            logger.info(f"Conversa {conversation_id} inicializada via HubCrew")
        except Exception as e:
            logger.error(f"Erro ao inicializar conversa: {str(e)}")
        
        return {
            "status": "processed",
            "conversation_id": conversation_id,
            "has_response": False
        }
    
    def _process_conversation_status_changed(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de status de conversa alterado.
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        conversation_data = webhook_data.get("conversation", {})
        conversation_id = str(conversation_data.get("id", ""))
        status = conversation_data.get("status", "")
        
        logger.info(f"Status da conversa {conversation_id} alterado para: {status}")
        
        # Se a conversa foi encerrada
        if status == "resolved":
            # Registra o encerramento da conversa via HubCrew
            try:
                # O HubCrew é o ponto central e tem acesso ao sistema de memória
                self.hub_crew.finalize_conversation(conversation_id)
                logger.info(f"Conversa {conversation_id} finalizada via HubCrew")
            except Exception as e:
                    logger.error(f"Erro ao finalizar conversa na memória: {str(e)}")
        
        return {
            "status": "processed",
            "conversation_id": conversation_id,
            "has_response": False
        }
    
    async def _send_reply_to_chatwoot(self, conversation_id: str, content: str, private: bool = False, message_type: str = "outgoing") -> Dict[str, Any]:
        """
        Envia uma resposta para o Chatwoot.
        
        Args:
            conversation_id: ID da conversa
            content: Conteúdo da mensagem
            private: Se a mensagem é privada (apenas para agentes)
            message_type: Tipo da mensagem
            
        Returns:
            Dict[str, Any]: Resposta da API do Chatwoot
        """
        try:
            # Envia a resposta para o Chatwoot
            response = await self.chatwoot_client.send_message(
                conversation_id=conversation_id,
                content=content,
                private=private,
                message_type=message_type
            )
            
            logger.info(f"Resposta enviada para conversa {conversation_id}")
            return response
        except Exception as e:
            logger.error(f"Erro ao enviar resposta para Chatwoot: {str(e)}")
            logger.error(traceback.format_exc())
            raise
