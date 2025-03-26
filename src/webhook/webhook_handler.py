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
            
            # Registra a estrutura completa do webhook para diagnóstico
            # Limita a 1000 caracteres para evitar logs muito grandes
            webhook_str = json.dumps(webhook_data, default=str)[:1000] if webhook_data else "None"
            logger.debug(f"Webhook recebido: {webhook_str}...")
            
            # Verifica se o webhook tem uma estrutura válida
            if not webhook_data:
                logger.warning("Webhook recebido sem dados")
                return {"status": "error", "reason": "Empty webhook data"}
                
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
        
        # Se a mensagem não for do tipo 'incoming', ignoramos
        if message_type != "incoming":
            logger.info(f"Ignorando mensagem não-recebida (tipo: {message_type}, sender_type: {sender_type}, sender_id: {sender_id})")
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
            
            # Na nova arquitetura, não dependemos mais de crews funcionais pré-configuradas
            # As crews são criadas dinamicamente pelo CrewFactory com base no domínio
            # determinado para a conversa
            
            # Verificar se temos acesso ao DomainManager e CrewFactory
            domain_manager = getattr(self.hub_crew, "_domain_manager", None)
            crew_factory = getattr(self.hub_crew, "_crew_factory", None)
            
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
            
            # Processar a mensagem pelo HubCrew central (hub-and-spoke model)
            # Não precisamos mais passar as crews funcionais, pois elas serão criadas dinamicamente
            # pelo CrewFactory com base no domínio determinado para a conversa
            hub_result = await self.hub_crew.process_message(
                message=normalized_message,
                conversation_id=conversation_id,
                channel_type=channel_type
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
        
        # 1. Primeiro, tentar determinar o domínio a partir do account_id
        if account_id:
            try:
                # Consultar o mapeamento de accounts para domínios
                # Este mapeamento pode ser armazenado na configuração ou em um serviço externo
                account_domain_mapping = self.config.get("account_domain_mapping", {})
                domain_name = account_domain_mapping.get(account_id)
                
                if domain_name:
                    logger.info(f"Domínio determinado a partir do account_id: {domain_name}")
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
