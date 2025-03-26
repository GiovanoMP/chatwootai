#!/usr/bin/env python3
"""
Simulador de Webhook do Chatwoot

Este módulo simula o envio de eventos do Chatwoot para o sistema ChatwootAI.
Permite testar o fluxo completo do sistema sem depender de uma instância real do Chatwoot.

Exemplos de uso:
    # Simular uma mensagem de cliente
    simulator = ChatwootSimulator()
    response = simulator.send_message("Olá, vocês têm creme para as mãos?")
    
    # Simular uma conversa completa
    simulator.start_conversation()
    simulator.send_message("Olá, vocês têm creme para as mãos?")
    simulator.send_message("Qual o preço?")
    simulator.end_conversation()
"""

import json
import uuid
import requests
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatwoot_simulator")

class ChatwootSimulator:
    """
    Simulador de Webhook do Chatwoot para testes de integração.
    """
    
    def __init__(
        self, 
        webhook_url: str = "http://localhost:8000/webhook",
        account_id: int = 1,
        inbox_id: int = 1,
        user_id: int = 1
    ):
        """
        Inicializa o simulador.
        
        Args:
            webhook_url: URL do webhook do ChatwootAI
            account_id: ID da conta do Chatwoot
            inbox_id: ID da caixa de entrada do Chatwoot
            user_id: ID do usuário do Chatwoot
        """
        self.webhook_url = webhook_url
        self.account_id = account_id
        self.inbox_id = inbox_id
        self.user_id = user_id
        
        # Estado da conversa atual
        self.conversation_id = None
        self.contact_id = None
        self.messages = []
        
        logger.info(f"Simulador inicializado - Webhook URL: {webhook_url}")
    
    def start_conversation(
        self, 
        contact_name: str = "Cliente Teste",
        contact_email: str = "cliente.teste@example.com",
        contact_phone: str = "+5511999999999",
        source_id: str = "whatsapp"
    ) -> Dict[str, Any]:
        """
        Inicia uma nova conversa.
        
        Args:
            contact_name: Nome do contato
            contact_email: Email do contato
            contact_phone: Telefone do contato
            source_id: Origem da conversa (whatsapp, website, etc)
            
        Returns:
            Dict[str, Any]: Resposta do webhook
        """
        # Gerar IDs únicos para a conversa e o contato
        self.conversation_id = str(uuid.uuid4())
        self.contact_id = str(uuid.uuid4())
        self.messages = []
        
        # Criar evento de criação de contato
        contact_created_event = self._create_contact_event(
            contact_name, contact_email, contact_phone
        )
        
        # Criar evento de criação de conversa
        conversation_created_event = self._create_conversation_event(source_id)
        
        # Enviar eventos
        contact_response = self._send_webhook_event(contact_created_event)
        time.sleep(0.5)  # Pequeno delay para simular tempo real
        conversation_response = self._send_webhook_event(conversation_created_event)
        
        logger.info(f"Conversa iniciada - ID: {self.conversation_id}")
        
        return {
            "contact_response": contact_response,
            "conversation_response": conversation_response
        }
    
    def send_message(
        self, 
        content: str,
        message_type: str = "incoming",
        content_type: str = "text",
        content_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envia uma mensagem na conversa atual.
        
        Args:
            content: Conteúdo da mensagem
            message_type: Tipo da mensagem (incoming, outgoing)
            content_type: Tipo do conteúdo (text, image, etc)
            content_attributes: Atributos adicionais do conteúdo
            
        Returns:
            Dict[str, Any]: Resposta do webhook
        """
        # Se não houver conversa ativa, iniciar uma
        if not self.conversation_id:
            self.start_conversation()
        
        # Gerar ID único para a mensagem
        message_id = str(uuid.uuid4())
        
        # Criar evento de mensagem
        message_event = self._create_message_event(
            content, message_id, message_type, content_type, content_attributes
        )
        
        # Enviar evento
        response = self._send_webhook_event(message_event)
        
        # Armazenar mensagem
        self.messages.append({
            "id": message_id,
            "content": content,
            "message_type": message_type,
            "created_at": datetime.now().isoformat()
        })
        
        logger.info(f"Mensagem enviada - ID: {message_id}, Conteúdo: {content[:50]}...")
        
        return response
    
    def end_conversation(self, status: str = "resolved") -> Dict[str, Any]:
        """
        Encerra a conversa atual.
        
        Args:
            status: Status final da conversa (resolved, pending, open)
            
        Returns:
            Dict[str, Any]: Resposta do webhook
        """
        if not self.conversation_id:
            logger.warning("Tentativa de encerrar conversa inexistente")
            return {"error": "No active conversation"}
        
        # Criar evento de alteração de status
        status_event = self._create_status_change_event(status)
        
        # Enviar evento
        response = self._send_webhook_event(status_event)
        
        logger.info(f"Conversa encerrada - ID: {self.conversation_id}, Status: {status}")
        
        # Limpar estado
        conversation_id = self.conversation_id
        self.conversation_id = None
        self.contact_id = None
        self.messages = []
        
        return response
    
    def _create_contact_event(
        self, 
        name: str, 
        email: str, 
        phone: str
    ) -> Dict[str, Any]:
        """
        Cria um evento de criação de contato.
        
        Args:
            name: Nome do contato
            email: Email do contato
            phone: Telefone do contato
            
        Returns:
            Dict[str, Any]: Evento de criação de contato
        """
        return {
            "event": "contact_created",
            "id": self.contact_id,
            "created_at": datetime.now().isoformat(),
            "account": {
                "id": self.account_id,
                "name": "Conta Teste"
            },
            "contact": {
                "id": self.contact_id,
                "name": name,
                "email": email,
                "phone_number": phone,
                "identifier": phone,
                "additional_attributes": {},
                "custom_attributes": {}
            }
        }
    
    def _create_conversation_event(self, source_id: str) -> Dict[str, Any]:
        """
        Cria um evento de criação de conversa.
        
        Args:
            source_id: Origem da conversa (whatsapp, website, etc)
            
        Returns:
            Dict[str, Any]: Evento de criação de conversa
        """
        return {
            "event": "conversation_created",
            "id": self.conversation_id,
            "created_at": datetime.now().isoformat(),
            "account": {
                "id": self.account_id,
                "name": "Conta Teste"
            },
            "inbox": {
                "id": self.inbox_id,
                "name": "Caixa de Entrada Teste"
            },
            "conversation": {
                "id": self.conversation_id,
                "status": "open",
                "contact_inbox": {
                    "source_id": source_id
                },
                "contact": {
                    "id": self.contact_id
                },
                "assignee": None,
                "meta": {
                    "sender": {
                        "id": self.contact_id,
                        "type": "contact"
                    }
                }
            }
        }
    
    def _create_message_event(
        self, 
        content: str,
        message_id: str,
        message_type: str,
        content_type: str,
        content_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Cria um evento de mensagem.
        
        Args:
            content: Conteúdo da mensagem
            message_id: ID da mensagem
            message_type: Tipo da mensagem (incoming, outgoing)
            content_type: Tipo do conteúdo (text, image, etc)
            content_attributes: Atributos adicionais do conteúdo
            
        Returns:
            Dict[str, Any]: Evento de mensagem
        """
        sender_type = "contact" if message_type == "incoming" else "user"
        sender_id = self.contact_id if message_type == "incoming" else self.user_id
        
        return {
            "event": "message_created",
            "id": message_id,
            "created_at": datetime.now().isoformat(),
            "account": {
                "id": self.account_id,
                "name": "Conta Teste"
            },
            "inbox": {
                "id": self.inbox_id,
                "name": "Caixa de Entrada Teste"
            },
            "conversation": {
                "id": self.conversation_id,
                "status": "open",
                "contact_inbox": {
                    "source_id": "whatsapp"
                },
                "contact": {
                    "id": self.contact_id
                }
            },
            "message": {
                "id": message_id,
                "content": content,
                "message_type": message_type,
                "content_type": content_type,
                "content_attributes": content_attributes or {},
                "sender": {
                    "id": sender_id,
                    "type": sender_type
                },
                "created_at": datetime.now().isoformat()
            },
            "sender": {
                "id": sender_id,
                "type": sender_type
            }
        }
    
    def _create_status_change_event(self, status: str) -> Dict[str, Any]:
        """
        Cria um evento de alteração de status da conversa.
        
        Args:
            status: Novo status da conversa
            
        Returns:
            Dict[str, Any]: Evento de alteração de status
        """
        return {
            "event": "conversation_status_changed",
            "id": self.conversation_id,
            "created_at": datetime.now().isoformat(),
            "account": {
                "id": self.account_id,
                "name": "Conta Teste"
            },
            "inbox": {
                "id": self.inbox_id,
                "name": "Caixa de Entrada Teste"
            },
            "conversation": {
                "id": self.conversation_id,
                "status": status,
                "contact_inbox": {
                    "source_id": "whatsapp"
                },
                "contact": {
                    "id": self.contact_id
                }
            }
        }
    
    def _send_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envia um evento para o webhook.
        
        Args:
            event: Evento a ser enviado
            
        Returns:
            Dict[str, Any]: Resposta do webhook
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=event,
                headers={"Content-Type": "application/json"}
            )
            
            # Registrar resposta
            logger.debug(f"Resposta do webhook - Status: {response.status_code}, Corpo: {response.text[:100]}...")
            
            return {
                "status_code": response.status_code,
                "response": response.text,
                "event": event
            }
        except Exception as e:
            logger.error(f"Erro ao enviar evento para webhook: {str(e)}")
            return {
                "error": str(e),
                "event": event
            }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Obtém o histórico da conversa atual.
        
        Returns:
            List[Dict[str, Any]]: Histórico de mensagens
        """
        return self.messages


if __name__ == "__main__":
    # Exemplo de uso
    simulator = ChatwootSimulator()
    
    # Iniciar conversa
    simulator.start_conversation()
    
    # Enviar mensagens
    simulator.send_message("Olá, vocês têm creme para as mãos?")
    time.sleep(2)  # Aguardar resposta
    
    simulator.send_message("Qual o preço?")
    time.sleep(2)  # Aguardar resposta
    
    # Encerrar conversa
    simulator.end_conversation()
