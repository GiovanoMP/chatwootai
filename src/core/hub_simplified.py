#!/usr/bin/env python3
"""
Hub simplificado para a arquitetura baseada em domínios.

Este módulo implementa uma versão simplificada do HubCrew, focada apenas em:
1. Identificar o domínio e account_id corretos para cada mensagem
2. Obter ou criar a crew apropriada para esse domínio/account_id
3. Redirecionar a mensagem para essa crew
4. Retornar a resposta

Na nova arquitetura, cada domínio/account_id tem uma única crew, eliminando
a necessidade de roteamento entre múltiplas crews funcionais.
"""

import logging
from typing import Dict, Any, Optional
from src.core.cache.agent_cache import RedisAgentCache
from src.core.data_proxy_agent import DataProxyAgent
from src.core.domain.domain_manager import DomainManager
from src.core.crews.crew_factory import CrewFactory, get_crew_factory
# Usando o sistema de memória integrado do CrewAI em vez de um MemorySystem personalizado

# Configurar logging
logger = logging.getLogger(__name__)

class HubCrew:
    """
    Implementação simplificada da HubCrew para a arquitetura baseada em domínios.

    Esta classe gerencia o fluxo de mensagens entre canais de comunicação e crews de domínio,
    identificando o domínio/account_id correto e direcionando a mensagem para a crew apropriada.

    Na nova arquitetura, cada domínio/account_id tem uma única crew, simplificando o fluxo de dados
    e reduzindo a complexidade do sistema.
    """

    def __init__(self,
                 data_proxy_agent: Optional[DataProxyAgent] = None,
                 crew_factory: Optional[CrewFactory] = None,
                 domain_manager: Optional[DomainManager] = None,
                 agent_cache: Optional[RedisAgentCache] = None):
        """
        Initialize the hub crew.

        Args:
            data_proxy_agent: Agent for data access across different services
            crew_factory: Factory for creating domain-specific crews
            domain_manager: Manager for multi-tenant domains
            agent_cache: Cache for agent responses (optional)
        """
        # Armazenar atributos necessários
        self.data_proxy_agent = data_proxy_agent
        self.domain_manager = domain_manager
        self.agent_cache = agent_cache

        # Inicializar ou armazenar o crew_factory
        if crew_factory:
            self.crew_factory = crew_factory
        else:
            # Criar uma nova instância do CrewFactory se não for fornecida
            self.crew_factory = get_crew_factory(
                data_proxy_agent=data_proxy_agent,
                domain_manager=domain_manager
            )

        # Cache de crews para evitar recriação desnecessária
        self.crew_cache = {}

    async def process_message(self,
                       message: Dict[str, Any],
                       conversation_id: str,
                       channel_type: str,
                       functional_crews: Dict[str, Any] = None,  # Mantido para compatibilidade
                       domain_name: str = None,
                       account_id: str = None) -> Dict[str, Any]:
        """
        Processa uma mensagem e a encaminha para a crew do domínio apropriado.

        Este é o ponto de entrada principal para o processamento de mensagens.
        Ele identifica o domínio/account_id correto e direciona a mensagem para a crew apropriada.

        Args:
            message: A mensagem a ser processada (conteúdo, informações do remetente, etc.)
            conversation_id: Identificador único da conversa
            channel_type: Canal de origem (WhatsApp, Instagram, etc.)
            functional_crews: Dicionário de crews funcionais disponíveis (mantido para compatibilidade)
            domain_name: Nome do domínio para a conversa
            account_id: ID interno da conta do cliente

        Returns:
            Resultado do processamento com mensagem, contexto e resposta
        """
        # Cria um contexto para a conversa
        # Na nova arquitetura, o CrewAI gerencia o contexto internamente
        context = {
            "channel_type": channel_type,
            "conversation_id": conversation_id,
            "interaction_count": 1  # Primeira interação
        }

        # Determinar o domínio para esta conversa
        # Prioridade: 1) domínio fornecido como parâmetro, 2) domínio no contexto, 3) domínio do cliente
        active_domain = None
        internal_account_id = None

        # 1. Verificar se o domínio foi fornecido como parâmetro
        if domain_name:
            active_domain = domain_name
            logger.info(f"Usando domínio fornecido como parâmetro: {domain_name}")

        # 1.1 Verificar se o account_id interno foi fornecido como parâmetro
        if account_id:
            internal_account_id = account_id
            logger.info(f"Usando account_id fornecido como parâmetro: {account_id}")

        # 2. Se não foi fornecido como parâmetro, verificar se está no contexto
        if not active_domain and "domain_name" in context:
            active_domain = context["domain_name"]
            logger.info(f"Usando domínio do contexto: {active_domain}")

        # 2.1 Verificar se o account_id está no contexto
        if not internal_account_id and "internal_account_id" in context:
            internal_account_id = context["internal_account_id"]
            logger.info(f"Usando account_id do contexto: {internal_account_id}")

        # 3. Se ainda não temos um domínio, tentar obter do DomainManager
        if not active_domain and self.domain_manager:
            # Tentar obter o domínio a partir do canal e outros metadados
            channel_info = {
                "channel_type": channel_type,
                "sender_id": message.get("sender_id"),
                "recipient_id": message.get("recipient_id")
            }

            domain_info = self.domain_manager.get_domain_for_channel(channel_info)
            if domain_info and "domain_name" in domain_info:
                active_domain = domain_info["domain_name"]
                logger.info(f"Domínio determinado pelo DomainManager: {active_domain}")

                # Se o DomainManager também retornou um account_id, usá-lo
                if not internal_account_id and "account_id" in domain_info:
                    internal_account_id = domain_info["account_id"]
                    logger.info(f"Account ID determinado pelo DomainManager: {internal_account_id}")

        # Se não tiver um domínio, isso é um erro
        if not active_domain:
            error_msg = "ERRO: Nenhum domínio determinado. Impossível processar a mensagem sem um domínio válido."
            logger.error(error_msg)
            return {
                "message": message,
                "context": context,
                "error": error_msg,
                "status": "error"
            }

        # Se não tiver um account_id interno, isso é um erro crítico
        if not internal_account_id:
            error_msg = "ERRO CRÍTICO: Nenhum account_id interno encontrado. Impossível processar a mensagem sem um account_id válido."
            logger.error(error_msg)
            return {
                "message": message,
                "context": context,
                "error": error_msg,
                "status": "error"
            }

        # Adicionar o domínio e account_id ao contexto
        context["domain_name"] = active_domain
        context["internal_account_id"] = internal_account_id

        # Adicionamos a mensagem atual ao contexto
        # Na nova arquitetura, o CrewAI gerencia o histórico de mensagens internamente
        context["current_message"] = {
            "content": message.get("content", ""),
            "sender_id": message.get("sender_id", ""),
            "timestamp": message.get("timestamp", "")
        }

        # Obter a crew para o domínio/account_id
        try:
            # Criar a crew usando o CrewFactory
            logger.info(f"Obtendo crew para domínio {active_domain} e account_id {internal_account_id}")

            # Na nova arquitetura, o crew_id é sempre "domain_crew"
            crew_id = "domain_crew"

            # Chave para o cache
            cache_key = f"{active_domain}:{internal_account_id}:{crew_id}"

            # Verificar se já existe no cache
            if cache_key in self.crew_cache:
                crew = self.crew_cache[cache_key]
                logger.info(f"Usando crew do cache para o domínio {active_domain} e account_id {internal_account_id}")
            else:
                # Obter ou criar a crew
                crew = self.crew_factory.get_crew_for_domain(crew_id, active_domain, internal_account_id)

                # Armazenar no cache
                if crew:
                    self.crew_cache[cache_key] = crew
                    logger.info(f"Crew criada e armazenada no cache para o domínio {active_domain} e account_id {internal_account_id}")

            if not crew:
                error_msg = f"Não foi possível obter a crew para o domínio {active_domain} e account_id {internal_account_id}"
                logger.error(error_msg)
                return {
                    "message": message,
                    "context": context,
                    "response": None,
                    "domain_name": active_domain,
                    "account_id": internal_account_id,
                    "error": error_msg,
                    "status": "error"
                }

            # Processar a mensagem com a crew do domínio
            try:
                # As crews esperam um método process(message, context)
                response = await crew.process(message, context)

                # Adiciona metadata sobre o processamento
                if isinstance(response, dict):
                    response["hub_metadata"] = {
                        "domain_name": active_domain,
                        "account_id": internal_account_id,
                        "processing_successful": True
                    }
                else:
                    # Se o resultado não for um dicionário, encapsula-o
                    response = {
                        "result": response,
                        "hub_metadata": {
                            "domain_name": active_domain,
                            "account_id": internal_account_id,
                            "processing_successful": True
                        }
                    }

                return response

            except Exception as e:
                logger.error(f"Erro ao processar mensagem na crew do domínio {active_domain}: {e}")
                return {
                    "message": message,
                    "context": context,
                    "response": None,
                    "domain_name": active_domain,
                    "account_id": internal_account_id,
                    "error": str(e),
                    "status": "error"
                }

        except Exception as e:
            error_msg = f"Erro ao obter crew para domínio {active_domain} e account_id {internal_account_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "message": message,
                "context": context,
                "response": None,
                "domain_name": active_domain,
                "account_id": internal_account_id,
                "error": error_msg,
                "status": "error"
            }

    async def finalize_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Finaliza uma conversa, liberando recursos.

        Na nova arquitetura, o CrewAI gerencia o contexto internamente,
        então este método apenas retorna um status de sucesso.

        Args:
            conversation_id: ID da conversa a ser finalizada

        Returns:
            Resultado da finalização
        """
        try:
            # Na nova arquitetura, não precisamos fazer nada especial para finalizar a conversa
            # O CrewAI gerencia o contexto internamente

            return {
                "conversation_id": conversation_id,
                "status": "resolved",
                "success": True
            }

        except Exception as e:
            logger.error(f"Erro ao finalizar conversa {conversation_id}: {str(e)}")
            return {
                "conversation_id": conversation_id,
                "status": "error",
                "success": False,
                "error": str(e)
            }
