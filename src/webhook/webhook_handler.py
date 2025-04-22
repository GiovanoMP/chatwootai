"""
Webhook Handler para o ChatwootAI.

Este módulo implementa o handler do webhook do Chatwoot, processando as mensagens
recebidas e encaminhando-as para o sistema de agentes.
"""

import logging
import json
import os
import yaml
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import traceback

from src.utils.encryption import credential_encryption

from src.core.hub import HubCrew
from src.core.data_service_hub import DataServiceHub
from odoo_api.integrations.chatwoot import ChatwootClient
from src.core.domain import DomainManager

logger = logging.getLogger(__name__)

class ChatwootWebhookHandler:
    """
    Handler para webhooks do Chatwoot e outros eventos.

    Esta classe é responsável por processar os webhooks do Chatwoot,
    normalizar as mensagens e encaminhá-las para o sistema de agentes.
    Também processa outros tipos de eventos, como sincronização de credenciais.

    Fluxo de processamento para Chatwoot:
    1. Recebe o webhook do Chatwoot
    2. Identifica o tipo de evento
    3. Extrai informações relevantes da mensagem
    4. Normaliza os dados para formato interno
    5. Encaminha para o HubCrew para processamento
    6. Retorna a resposta para o Chatwoot

    Fluxo de processamento para Credenciais:
    1. Recebe o evento de sincronização de credenciais
    2. Extrai as informações de account_id e credenciais
    3. Encaminha para o HubCrew para processamento
    4. Retorna o resultado da sincronização
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

            # Log único de processamento
            logger.info("Processando mensagem ID %s", webhook_data.get('id'))

            # Verifica se o webhook tem uma estrutura válida
            if not webhook_data:
                logger.warning("Webhook recebido sem dados")
                return {"status": "error", "reason": "Empty webhook data"}

            # Verifica se é um evento de credenciais
            if webhook_data.get('source') == 'credentials' or webhook_data.get('event') == 'credentials_sync':
                logger.info("Webhook identificado como evento de credenciais")
                return await self.process_credentials_event(webhook_data)

            # Obtém o tipo de evento
            event_type = webhook_data.get("event")

            # Registra as chaves principais do webhook para diagnóstico
            top_level_keys = list(webhook_data.keys())
            logger.info(f"Chaves do webhook: {top_level_keys}")

            # Se o tipo de evento for None ou vazio, tenta identificar o tipo de evento
            if not event_type:
                logger.info("Webhook recebido sem tipo de evento definido")

                # Tenta identificar o tipo de evento com base na estrutura
                if "message" in webhook_data:
                    message_id = webhook_data.get("message", {}).get("id", "unknown")
                    message_type = webhook_data.get("message", {}).get("message_type", "unknown")
                    logger.info(f"Webhook contém mensagem - ID: {message_id}, Tipo: {message_type}")

                    # Se parece ser uma mensagem, tratamos como message_created
                    if message_type:
                        logger.info(f"Tratando webhook sem tipo como 'message_created' com base na estrutura")
                        event_type = "message_created"

                if "conversation" in webhook_data and not event_type:
                    conversation_id = webhook_data.get("conversation", {}).get("id", "unknown")
                    logger.info(f"Webhook contém conversa - ID: {conversation_id}")

                    # Se parece ser uma atualização de conversa, tratamos como conversation_updated
                    if not event_type:
                        logger.info(f"Tratando webhook sem tipo como 'conversation_updated' com base na estrutura")
                        event_type = "conversation_updated"

                # Se ainda não conseguimos identificar o tipo, ignoramos
                if not event_type:
                    return {"status": "ignored", "reason": "Could not identify event type"}

            # Processa o evento de acordo com o tipo
            if event_type == "message_created":
                result = await self._process_message_created(webhook_data)
            elif event_type == "conversation_created":
                result = self._process_conversation_created(webhook_data)
            elif event_type == "conversation_status_changed":
                result = self._process_conversation_status_changed(webhook_data)
            elif event_type == "contact_updated":
                result = self._process_contact_updated(webhook_data)
            elif event_type == "contact_created":
                result = self._process_contact_created(webhook_data)
            elif event_type == "conversation_updated":
                result = self._process_conversation_updated(webhook_data)
            elif event_type == "message_updated":
                result = self._process_message_updated(webhook_data)
            elif event_type == "webwidget_triggered":
                result = self._process_webwidget_triggered(webhook_data)
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
        # Log completo da estrutura do webhook para diagnóstico
        logger.info(f"Webhook completo recebido: {json.dumps(webhook_data, indent=2)}")

        # Extrai informações relevantes
        message_data = webhook_data.get("message", {})
        conversation_data = webhook_data.get("conversation", {})

        # Registra a estrutura completa do evento para diagnóstico
        logger.debug(f"Estrutura do evento message_created: {json.dumps(webhook_data)[:500]}...")

        # Verifica se temos dados de mensagem
        if not message_data:
            logger.info(f"Evento message_created sem dados de mensagem")
            # Registra informações adicionais para diagnóstico
            account_id = webhook_data.get("account", {}).get("id", "unknown")
            logger.info(f"Detalhes do evento sem mensagem - account_id: {account_id}")

            # Tenta encontrar a mensagem em outros lugares da estrutura do webhook
            # Muitas vezes o Chatwoot pode enviar a mensagem em uma estrutura diferente
            messages = conversation_data.get("messages", [])
            if messages and len(messages) > 0:
                logger.info(f"Encontrada mensagem na lista de mensagens da conversa")
                message_data = messages[0]
                logger.info(f"Usando a primeira mensagem da lista: {json.dumps(message_data)}")
            else:
                # Tenta encontrar a mensagem no campo content diretamente na conversa
                content = conversation_data.get("content")
                if content:
                    logger.info(f"Encontrado conteúdo diretamente na conversa: {content}")
                    message_data = {"content": content, "message_type": "incoming"}
                else:
                    return {"status": "ignored", "reason": "No message data"}

        # Verifica se a mensagem tem conteúdo
        message_content = message_data.get("content")
        if not message_content:
            logger.info(f"Mensagem sem conteúdo - ID: {message_data.get('id', 'unknown')}")
            return {"status": "ignored", "reason": "Empty message content"}

        # Verifica o tipo da mensagem
        message_type = message_data.get("message_type")
        sender_type = message_data.get("sender_type", "unknown")
        sender_id = message_data.get("sender_id", "unknown")

        # Registra informações detalhadas sobre a mensagem
        logger.info(f"Mensagem recebida - tipo: {message_type}, sender: {sender_type}:{sender_id}, conteúdo: {message_content[:50]}...")

        # Verifica se a mensagem é do tipo 'incoming' (string) ou '0' (numérico)
        # O Chatwoot pode enviar o tipo como string "incoming" ou como número 0
        if message_type != "incoming" and message_type != 0 and str(message_type) != "0":
            logger.info(f"Ignorando mensagem não-recebida (tipo: {message_type}, sender_type: {sender_type}, sender_id: {sender_id})")
            return {"status": "ignored", "reason": "Not an incoming message"}

        logger.info(f"Processando mensagem recebida (tipo: {message_type}, sender_type: {sender_type}, sender_id: {sender_id})")

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

            # Na nova arquitetura, não dependemos mais de crews funcionais pré-configuradas
            # As crews são criadas dinamicamente pelo CrewFactory com base no domínio
            # determinado para a conversa

            # Verificar se temos acesso ao DomainManager e CrewFactory
            domain_manager = getattr(self.hub_crew, "domain_manager", None)
            crew_factory = getattr(self.hub_crew, "crew_factory", None)

            if not domain_manager or not crew_factory:
                logger.error("HubCrew não tem DomainManager ou CrewFactory configurados")
                return {
                    "status": "error",
                    "error": "Componentes essenciais não configurados no HubCrew",
                    "conversation_id": conversation_id,
                    "has_response": True
                }

            # Obter o account_id e inbox_id para determinar o domínio
            account_id = str(webhook_data.get("account", {}).get("id", ""))

            # Log detalhado para diagnóstico
            logger.info(f"Processando mensagem para account_id: {account_id}, inbox_id: {inbox_id}")

            # Determinar o domínio e o account_id interno com base no account_id do Chatwoot
            domain_name = None
            internal_account_id = None
            domain_manager = getattr(self.hub_crew, "domain_manager", None)

            if domain_manager and account_id:
                try:
                    # Obter o domínio
                    domain_name = domain_manager.get_domain_by_account_id(account_id)
                    if domain_name:
                        logger.info(f"Domínio determinado para account_id {account_id}: {domain_name}")
                    else:
                        logger.warning(f"Nenhum domínio encontrado para account_id {account_id}, usando padrão")

                    # Obter o account_id interno
                    internal_account_id = domain_manager.get_internal_account_id(account_id)
                    if internal_account_id:
                        logger.info(f"Account ID interno determinado: {internal_account_id}")
                        # Adicionar o account_id interno aos metadados da mensagem normalizada
                        normalized_message["internal_account_id"] = internal_account_id
                    else:
                        logger.warning(f"Nenhum account_id interno encontrado para account_id {account_id}")
                except Exception as e:
                    logger.error(f"Erro ao determinar domínio/account_id para account_id {account_id}: {str(e)}")

            # Processar a mensagem pelo HubCrew central (hub-and-spoke model)
            # Não precisamos mais passar as crews funcionais, pois elas serão criadas dinamicamente
            # pelo CrewFactory com base no domínio determinado para a conversa
            hub_result = await self.hub_crew.process_message(
                message=normalized_message,
                conversation_id=conversation_id,
                channel_type=channel_type,
                domain_name=domain_name,  # Passamos o domínio determinado pelo account_id
                account_id=internal_account_id  # Passamos o account_id interno
                # Removemos o parâmetro functional_crews, pois agora é responsabilidade do HubCrew
                # criar as crews dinamicamente usando o CrewFactory
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

        Na arquitetura otimizada, extraímos informações da empresa/account do webhook
        e as usamos para determinar o domínio antes de chamar o HubCrew, seguindo o
        princípio de "Responsabilidade Única" e evitando consultas desnecessárias.

        Args:
            webhook_data: Dados do webhook

        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        # Extrair informações básicas da conversa e contato
        conversation_data = webhook_data.get("conversation", {})
        conversation_id = str(conversation_data.get("id", ""))
        contact_data = webhook_data.get("contact", {})
        contact_id = str(contact_data.get("id", ""))

        # Extrair informações da empresa/account
        account_id = str(webhook_data.get("account", {}).get("id", ""))
        inbox_id = str(conversation_data.get("inbox_id", ""))

        logger.info(f"Nova conversa criada: {conversation_id}, Contato: {contact_id}, Account: {account_id}, Inbox: {inbox_id}")

        # Determinar o domínio com base nas informações da empresa/account
        domain_name = None

        # Obter o DomainManager para determinar o domínio
        from src.core.domain.domain_manager import DomainManager
        from src.core.domain.domain_registry import get_domain_registry

        domain_registry = get_domain_registry()
        domain_manager = DomainManager(redis_client=None, default_domain="cosmetics")

        # 1. Primeiro, tentar determinar o domínio a partir do account_id
        if account_id:
            try:
                # Usar o DomainManager para determinar o domínio
                domain_name = domain_manager.get_domain_by_account_id(account_id)

                if domain_name:
                    logger.info(f"Domínio determinado a partir do account_id via DomainManager: {domain_name}")
                else:
                    # Fallback para o método antigo
                    account_domain_mapping = self.config.get("account_domain_mapping", {})
                    domain_name = account_domain_mapping.get(account_id)

                    if domain_name:
                        logger.info(f"Domínio determinado a partir do account_id via configuração: {domain_name}")
            except Exception as e:
                logger.warning(f"Erro ao determinar domínio a partir do account_id: {str(e)}")

        # 2. Se não encontrou pelo account_id, tentar pelo inbox_id
        if not domain_name and inbox_id:
            try:
                # Consultar o mapeamento de inboxes para domínios
                inbox_domain_mapping = self.config.get("inbox_domain_mapping", {})
                domain_name = inbox_domain_mapping.get(inbox_id)

                if domain_name:
                    logger.info(f"Domínio determinado a partir do inbox_id: {domain_name}")
            except Exception as e:
                logger.warning(f"Erro ao determinar domínio a partir do inbox_id: {str(e)}")

        # 3. Se ainda não encontrou, tentar obter informações adicionais da API do Chatwoot
        if not domain_name and self.chatwoot_client:
            try:
                # Obter detalhes da account/inbox via API do Chatwoot
                if account_id and inbox_id:
                    try:
                        # Converter para inteiros conforme esperado pelo método get_inbox
                        account_id_int = int(account_id)
                        inbox_id_int = int(inbox_id)

                        # Obter detalhes do inbox
                        inbox_details = self.chatwoot_client.get_inbox(account_id_int, inbox_id_int)

                        # Extrair o domínio de metadados personalizados do inbox
                        if inbox_details and "meta" in inbox_details:
                            domain_name = inbox_details["meta"].get("domain")
                            if domain_name:
                                logger.info(f"Domínio determinado a partir dos metadados do inbox: {domain_name}")
                    except ValueError:
                        logger.warning(f"Erro ao converter account_id ou inbox_id para inteiro: {account_id}, {inbox_id}")
            except Exception as e:
                logger.warning(f"Erro ao consultar API do Chatwoot: {str(e)}")

        # Registrar a nova conversa no sistema de memória através do HubCrew
        # Agora passando o domínio já determinado
        try:
            # O HubCrew é o ponto central e tem acesso ao sistema de memória
            self.hub_crew.register_conversation(
                conversation_id=conversation_id,
                customer_id=contact_id,
                domain_name=domain_name  # Passamos o domínio já determinado
            )
            logger.info(f"Conversa {conversation_id} inicializada via HubCrew com domínio: {domain_name or 'padrão'}")
        except Exception as e:
            logger.error(f"Erro ao inicializar conversa: {str(e)}")

        return {
            "status": "processed",
            "conversation_id": conversation_id,
            "domain_name": domain_name,
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

    def _process_contact_updated(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de atualização de contato do Chatwoot.

        Este método é chamado quando um contato é atualizado no Chatwoot.
        Podemos usar esses dados para atualizar informações do cliente no nosso sistema.

        Args:
            webhook_data: Dados do webhook

        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        try:
            # Extrai informações do contato
            contact_data = webhook_data.get("contact", {})
            contact_id = contact_data.get("id", "")
            contact_name = contact_data.get("name", "")
            contact_email = contact_data.get("email", "")
            contact_phone = contact_data.get("phone_number", "")

            logger.info(f"Contato atualizado: {contact_id} - {contact_name}")

            # Aqui podemos implementar lógica para atualizar o contato no nosso sistema
            # Por exemplo, atualizar informações no banco de dados ou no sistema de memória

            return {
                "status": "processed",
                "contact_id": contact_id,
                "has_response": False
            }
        except Exception as e:
            logger.error(f"Erro ao processar atualização de contato: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _process_contact_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de criação de contato do Chatwoot.

        Este método é chamado quando um novo contato é criado no Chatwoot.
        Podemos usar esses dados para criar um novo cliente no nosso sistema.

        Args:
            webhook_data: Dados do webhook

        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        try:
            # Extrai informações do contato
            contact_data = webhook_data.get("contact", {})
            contact_id = contact_data.get("id", "")
            contact_name = contact_data.get("name", "")
            contact_email = contact_data.get("email", "")
            contact_phone = contact_data.get("phone_number", "")

            logger.info(f"Novo contato criado: {contact_id} - {contact_name}")

            # Aqui podemos implementar lógica para criar o contato no nosso sistema
            # Por exemplo, adicionar ao banco de dados ou ao sistema de memória

            return {
                "status": "processed",
                "contact_id": contact_id,
                "has_response": False
            }
        except Exception as e:
            logger.error(f"Erro ao processar criação de contato: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _process_conversation_updated(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de atualização de conversa do Chatwoot.

        Este método é chamado quando uma conversa é atualizada no Chatwoot.
        Podemos usar esses dados para atualizar o contexto da conversa no nosso sistema.

        Args:
            webhook_data: Dados do webhook

        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        try:
            # Extrai informações da conversa
            conversation_data = webhook_data.get("conversation", {})
            conversation_id = conversation_data.get("id", "")

            logger.info(f"Conversa atualizada: {conversation_id}")

            # Aqui podemos implementar lógica para atualizar a conversa no nosso sistema
            # Por exemplo, atualizar o contexto ou metadados da conversa

            return {
                "status": "processed",
                "conversation_id": conversation_id,
                "has_response": False
            }
        except Exception as e:
            logger.error(f"Erro ao processar atualização de conversa: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _process_message_updated(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de atualização de mensagem do Chatwoot.

        Este método é chamado quando uma mensagem é atualizada no Chatwoot.
        Podemos usar esses dados para atualizar o histórico de mensagens no nosso sistema.

        Args:
            webhook_data: Dados do webhook

        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        try:
            # Extrai informações da mensagem
            message_data = webhook_data.get("message", {})
            message_id = message_data.get("id", "")
            conversation_id = message_data.get("conversation_id", "")

            logger.info(f"Mensagem atualizada: {message_id} na conversa {conversation_id}")

            # Aqui podemos implementar lógica para atualizar a mensagem no nosso sistema
            # Por exemplo, atualizar o histórico de mensagens ou o contexto da conversa

            return {
                "status": "processed",
                "message_id": message_id,
                "conversation_id": conversation_id,
                "has_response": False
            }
        except Exception as e:
            logger.error(f"Erro ao processar atualização de mensagem: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _process_webwidget_triggered(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de acionamento do widget de chat do Chatwoot.

        Este método é chamado quando um usuário abre o widget de chat no site.
        Podemos usar esses dados para iniciar proativamente uma conversa ou preparar o contexto.

        Args:
            webhook_data: Dados do webhook

        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        try:
            # Extrai informações do evento
            website_token = webhook_data.get("website_token", "")
            source_url = webhook_data.get("source_url", "")

            logger.info(f"Widget de chat acionado: {website_token} na URL {source_url}")

            # Aqui podemos implementar lógica para preparar o sistema para uma nova conversa
            # Por exemplo, pré-carregar informações relevantes com base na URL da página

            return {
                "status": "processed",
                "website_token": website_token,
                "source_url": source_url,
                "has_response": False
            }
        except Exception as e:
            logger.error(f"Erro ao processar acionamento do widget: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def process_credentials_event(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento de sincronização de credenciais.

        Args:
            webhook_data: Dados do evento

        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        try:
            logger.info("Processando evento de sincronização de credenciais")

            # Extrair informações do evento
            account_id = webhook_data.get("account_id")
            credentials = webhook_data.get("credentials", {})
            token = webhook_data.get("token")

            # Validar dados obrigatórios
            if not account_id or not credentials:
                logger.warning("Evento de credenciais sem account_id ou credentials")
                return {"success": False, "error": "Dados incompletos: account_id e credentials são obrigatórios"}

            # Verificar token de autenticação
            if not token:
                logger.warning("Evento de credenciais sem token de autenticação")
                return {"success": False, "error": "Token de autenticação não fornecido"}

            # Verificar se o token corresponde ao token nas credenciais
            # Em um ambiente de produção, você deve verificar o token contra um armazenamento seguro
            # ou usar um mecanismo de autenticação mais robusto como JWT
            if token != credentials.get("token"):
                logger.warning("Token de autenticação inválido")
                self._log_credentials_access(account_id, "sync", False, "Token de autenticação inválido")
                return {"success": False, "error": "Token de autenticação inválido"}

            logger.info(f"Processando credenciais para account_id: {account_id}")

            # Verificar se o HubCrew está disponível
            if not self.hub_crew:
                logger.error("HubCrew não inicializado")
                return {"success": False, "error": "HubCrew não inicializado"}

            # Verificar se o DomainManager está disponível
            if not hasattr(self.hub_crew, 'domain_manager') or not self.hub_crew.domain_manager:
                logger.error("DomainManager não disponível no HubCrew")
                return {"success": False, "error": "DomainManager não disponível"}

            # Extrair informações das credenciais
            domain = credentials.get("domain", "default")
            name = credentials.get("name", "Cliente")

            # Usar caminho fixo para o diretório de configuração
            config_dir = os.path.join("config", "domains")
            domain_dir = os.path.join(config_dir, domain)
            if not os.path.exists(domain_dir):
                os.makedirs(domain_dir, exist_ok=True)

            # Verificar se o diretório do account_id existe
            account_dir = os.path.join(domain_dir, account_id)
            config_path = os.path.join(account_dir, "config.yaml")
            credentials_path = os.path.join(account_dir, "credentials.yaml")
            config = {}
            creds_config = {}

            # Garantir que o diretório existe para atualização
            if not os.path.exists(account_dir):
                os.makedirs(account_dir, exist_ok=True)

            # Verificar se o arquivo de configuração existe
            if os.path.exists(config_path):
                # Carregar configuração existente
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}

                # Verificar se o token no arquivo corresponde ao token enviado
                stored_token = None
                if "integrations" in config and "mcp" in config["integrations"] and "config" in config["integrations"]["mcp"]:
                    stored_token = config["integrations"]["mcp"]["config"].get("credential_ref")

                if stored_token and stored_token != token:
                    logger.warning(f"Token no arquivo ({stored_token}) não corresponde ao token enviado ({token})")
                    self._log_credentials_access(account_id, "sync", False, "Token no arquivo não corresponde ao token enviado")
                    return {"success": False, "error": "Token de autenticação não corresponde ao token armazenado"}
            else:
                # Criar um novo arquivo de configuração
                logger.info(f"Criando novo arquivo de configuração para {account_id}")

            # Verificar se o arquivo de credenciais existe
            if os.path.exists(credentials_path):
                # Carregar credenciais existentes
                with open(credentials_path, 'r') as f:
                    creds_config = yaml.safe_load(f) or {}
            else:
                # Criar um novo arquivo de credenciais
                logger.info(f"Criando novo arquivo de credenciais para {account_id}")
                # Inicializar com estrutura básica
                creds_config = {
                    "account_id": account_id,
                    "credentials": {}
                }

            # Atualizar configuração com as credenciais
            config.update({
                "account_id": account_id,
                "name": name,
                "description": f"Configuração para {name}",
            })

            # Atualizar ou criar seção de integrações
            if "integrations" not in config:
                config["integrations"] = {}

            # Função auxiliar para mesclar dicionários de forma recursiva
            def deep_merge(source, destination):
                """
                Mescla dois dicionários de forma recursiva.
                Valores não vazios em source sobrescrevem valores em destination.
                """
                for key, value in source.items():
                    if isinstance(value, dict):
                        # Obter o nó do destination ou criar um novo
                        node = destination.setdefault(key, {})
                        if isinstance(node, dict):
                            deep_merge(value, node)
                        else:
                            destination[key] = value
                    elif value is not None and value != "":
                        # Atualizar apenas se o valor não for vazio
                        destination[key] = value
                return destination

            # Preparar configuração MCP com apenas referências para credenciais sensíveis
            mcp_config = {
                "type": "odoo-mcp",
                "config": {}
            }

            # Adicionar apenas campos não vazios e não sensíveis
            if credentials.get("odoo_url"):
                mcp_config["config"]["url"] = credentials.get("odoo_url")
            if credentials.get("odoo_db"):
                mcp_config["config"]["db"] = credentials.get("odoo_db")
            if credentials.get("odoo_username"):
                mcp_config["config"]["username"] = credentials.get("odoo_username")
            if credentials.get("token"):
                mcp_config["config"]["credential_ref"] = credentials.get("token")  # Apenas referência, não a senha real

            # Atualizar configuração MCP usando mesclagem inteligente
            if "mcp" not in config["integrations"]:
                config["integrations"]["mcp"] = {}
            deep_merge(mcp_config, config["integrations"]["mcp"])

            # Preparar configuração Qdrant
            qdrant_config = {}
            if credentials.get("qdrant_collection"):
                qdrant_config["collection"] = credentials.get("qdrant_collection")
            else:
                qdrant_config["collection"] = f"business_rules_{account_id}"

            # Atualizar configuração Qdrant usando mesclagem inteligente
            if "qdrant" not in config["integrations"]:
                config["integrations"]["qdrant"] = {}
            deep_merge(qdrant_config, config["integrations"]["qdrant"])

            # Preparar configuração Redis
            redis_config = {}
            if credentials.get("redis_prefix"):
                redis_config["prefix"] = credentials.get("redis_prefix")
            else:
                redis_config["prefix"] = account_id

            # Atualizar configuração Redis usando mesclagem inteligente
            if "redis" not in config["integrations"]:
                config["integrations"]["redis"] = {}
            deep_merge(redis_config, config["integrations"]["redis"])

            # Adicionar configurações de redes sociais se fornecidas
            if any(key.startswith("facebook_") for key in credentials):
                facebook_config = {}
                if credentials.get("facebook_app_id"):
                    facebook_config["app_id"] = credentials.get("facebook_app_id")

                # Usar referências para credenciais sensíveis
                if credentials.get("facebook_app_secret"):
                    facebook_config["app_secret_ref"] = f"fb_secret_{account_id}"  # Referência, não o valor real

                if credentials.get("facebook_access_token"):
                    facebook_config["access_token_ref"] = f"fb_token_{account_id}"  # Referência, não o valor real

                # Atualizar configuração Facebook usando mesclagem inteligente
                if "facebook" not in config["integrations"]:
                    config["integrations"]["facebook"] = {}
                deep_merge(facebook_config, config["integrations"]["facebook"])

            if any(key.startswith("instagram_") for key in credentials):
                instagram_config = {}
                if credentials.get("instagram_client_id"):
                    instagram_config["client_id"] = credentials.get("instagram_client_id")

                # Usar referências para credenciais sensíveis
                if credentials.get("instagram_client_secret"):
                    instagram_config["client_secret_ref"] = f"ig_secret_{account_id}"  # Referência, não o valor real

                if credentials.get("instagram_access_token"):
                    instagram_config["access_token_ref"] = f"ig_token_{account_id}"  # Referência, não o valor real

                # Atualizar configuração Instagram usando mesclagem inteligente
                if "instagram" not in config["integrations"]:
                    config["integrations"]["instagram"] = {}
                deep_merge(instagram_config, config["integrations"]["instagram"])

            if any(key.startswith("mercado_livre_") for key in credentials):
                ml_config = {}
                if credentials.get("mercado_livre_app_id"):
                    ml_config["app_id"] = credentials.get("mercado_livre_app_id")

                # Usar referências para credenciais sensíveis
                if credentials.get("mercado_livre_client_secret"):
                    ml_config["client_secret_ref"] = f"ml_secret_{account_id}"  # Referência, não o valor real

                if credentials.get("mercado_livre_access_token"):
                    ml_config["access_token_ref"] = f"ml_token_{account_id}"  # Referência, não o valor real

                # Atualizar configuração Mercado Livre usando mesclagem inteligente
                if "mercado_livre" not in config["integrations"]:
                    config["integrations"]["mercado_livre"] = {}
                deep_merge(ml_config, config["integrations"]["mercado_livre"])

            # Processar credenciais sensíveis para o arquivo credentials.yaml
            # Inicializar a seção de credenciais se não existir
            if "credentials" not in creds_config:
                creds_config["credentials"] = {}

            # Adicionar credenciais sensíveis
            # Odoo
            if credentials.get("odoo_password"):
                # Criptografar a senha antes de salvar
                encrypted_password = credential_encryption.encrypt(credentials.get("odoo_password"))
                creds_config["credentials"][token] = encrypted_password
                logger.info(f"Senha criptografada salva para {account_id}")
            elif credentials.get("password"):  # Compatibilidade com versões anteriores
                # Criptografar a senha antes de salvar
                encrypted_password = credential_encryption.encrypt(credentials.get("password"))
                creds_config["credentials"][token] = encrypted_password
                logger.info(f"Senha (campo legado) criptografada salva para {account_id}")
            else:
                # Se não foi fornecida senha, usar o token como senha para desenvolvimento
                creds_config["credentials"][token] = token
                logger.warning(f"Nenhuma senha fornecida para {account_id}. Usando token como senha para desenvolvimento.")

            # Facebook
            if credentials.get("facebook_app_secret"):
                encrypted_secret = credential_encryption.encrypt(credentials.get("facebook_app_secret"))
                creds_config["credentials"][f"fb_secret_{account_id}"] = encrypted_secret
                logger.info(f"Facebook app secret criptografado salvo para {account_id}")
            if credentials.get("facebook_access_token"):
                encrypted_token = credential_encryption.encrypt(credentials.get("facebook_access_token"))
                creds_config["credentials"][f"fb_token_{account_id}"] = encrypted_token
                logger.info(f"Facebook access token criptografado salvo para {account_id}")

            # Instagram
            if credentials.get("instagram_client_secret"):
                encrypted_secret = credential_encryption.encrypt(credentials.get("instagram_client_secret"))
                creds_config["credentials"][f"ig_secret_{account_id}"] = encrypted_secret
                logger.info(f"Instagram client secret criptografado salvo para {account_id}")
            if credentials.get("instagram_access_token"):
                encrypted_token = credential_encryption.encrypt(credentials.get("instagram_access_token"))
                creds_config["credentials"][f"ig_token_{account_id}"] = encrypted_token
                logger.info(f"Instagram access token criptografado salvo para {account_id}")

            # Mercado Livre
            if credentials.get("mercado_livre_client_secret"):
                encrypted_secret = credential_encryption.encrypt(credentials.get("mercado_livre_client_secret"))
                creds_config["credentials"][f"ml_secret_{account_id}"] = encrypted_secret
                logger.info(f"Mercado Livre client secret criptografado salvo para {account_id}")
            if credentials.get("mercado_livre_access_token"):
                encrypted_token = credential_encryption.encrypt(credentials.get("mercado_livre_access_token"))
                creds_config["credentials"][f"ml_token_{account_id}"] = encrypted_token
                logger.info(f"Mercado Livre access token criptografado salvo para {account_id}")

            # Salvar configuração atualizada
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            # Salvar credenciais atualizadas
            with open(credentials_path, 'w') as f:
                yaml.dump(creds_config, f, default_flow_style=False)

            logger.info(f"Configuração YAML atualizada em {config_path}")
            logger.info(f"Credenciais YAML atualizadas em {credentials_path}")

            # Registrar o acesso
            self._log_credentials_access(account_id, "sync", True)

            return {
                "success": True,
                "message": "Credenciais sincronizadas com sucesso",
                "account_id": account_id,
                "config_path": config_path,
                "credentials_path": credentials_path
            }

        except Exception as e:
            logger.error(f"Erro ao processar evento de credenciais: {str(e)}")
            traceback.print_exc()
            self._log_credentials_access(account_id if 'account_id' in locals() else "unknown", "sync", False, str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def _log_credentials_access(self, account_id: str, operation: str, success: bool, error_message: Optional[str] = None, ip_address: Optional[str] = None):
        """
        Registra um acesso às credenciais.

        Args:
            account_id: ID da conta
            operation: Operação realizada (ex: sync, test)
            success: Se a operação foi bem-sucedida
            error_message: Mensagem de erro (se houver)
            ip_address: Endereço IP de onde o acesso foi feito
        """
        try:
            # Aqui você pode implementar o registro em um banco de dados, arquivo, etc.
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "account_id": account_id,
                "operation": operation,
                "success": success,
                "ip_address": ip_address,
                "error_message": error_message
            }

            # Exemplo: salvar em um arquivo de log
            os.makedirs("logs", exist_ok=True)
            log_path = os.path.join("logs", "credentials_access.log")
            with open(log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")

            logger.info(f"Acesso registrado: {operation} para {account_id} - Sucesso: {success}")

        except Exception as e:
            logger.error(f"Erro ao registrar acesso: {str(e)}")
