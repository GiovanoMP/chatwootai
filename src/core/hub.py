#!/usr/bin/env python3
"""
Hub para o ChatwootAI

Este módulo implementa o Hub, responsável por direcionar mensagens para as crews
apropriadas com base no canal de origem.
"""

import logging
import pickle
import time
from typing import Dict, Any, Optional

from src.utils.redis_client import get_redis_client, get_aioredis_client
from src.core.config import get_config_registry
from src.core.crews.crew_factory import get_crew_factory

# Configurar logging
logger = logging.getLogger(__name__)

class Hub:
    """
    Hub para direcionar mensagens para crews específicas por canal.

    Esta classe é responsável por determinar o tipo de crew e canal apropriados
    para cada mensagem, e direcionar a mensagem para a crew correspondente.
    """

    def __init__(self, redis_client=None, config_registry=None, crew_factory=None):
        """
        Inicializa o hub.

        Args:
            redis_client: Cliente Redis opcional
            config_registry: Registro de configurações opcional
            crew_factory: Fábrica de crews opcional
        """
        self.redis_client = redis_client or get_redis_client()
        self.config_registry = config_registry or get_config_registry()
        self.crew_factory = crew_factory or get_crew_factory()
        self.redis_async_client = None  # Será inicializado sob demanda

        # Cache em memória para crews
        self.memory_cache = {}

        logger.info("Hub inicializado")

    async def _get_async_redis_client(self):
        """
        Obtém o cliente Redis assíncrono, inicializando-o se necessário.

        Returns:
            Cliente Redis assíncrono ou None se não for possível conectar
        """
        if self.redis_async_client is None:
            self.redis_async_client = await get_aioredis_client()
        return self.redis_async_client

    async def process_message(self,
                       message: Dict[str, Any],
                       conversation_id: str,
                       channel_type: str,
                       domain_name: str = None,
                       account_id: str = None) -> Dict[str, Any]:
        """
        Processa uma mensagem e a encaminha para a crew apropriada.

        Args:
            message: A mensagem a ser processada
            conversation_id: Identificador único da conversa
            channel_type: Canal de origem (WhatsApp, Instagram, etc.)
            domain_name: Nome do domínio para a conversa
            account_id: ID interno da conta do cliente

        Returns:
            Resultado do processamento
        """
        # Verificar se temos domínio e account_id
        if not domain_name or not account_id:
            error_msg = "ERRO: Domínio ou account_id não fornecidos. Impossível processar a mensagem."
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "error"
            }

        # Criar contexto para a conversa
        context = {
            "channel_type": channel_type,
            "conversation_id": conversation_id,
            "domain_name": domain_name,
            "account_id": account_id
        }

        # Determinar o tipo de crew e canal específico
        crew_type, specific_channel = self._determine_crew_type(message, channel_type)

        # Obter a crew apropriada
        try:
            crew = await self.get_crew(
                crew_type=crew_type,
                domain_name=domain_name,
                account_id=account_id,
                channel_type=specific_channel
            )

            # Processar a mensagem com a crew
            result = await crew.process(message, context)

            # Adicionar informações de roteamento ao resultado
            result["routing"] = {
                "crew_type": crew_type,
                "channel_type": specific_channel,
                "domain_name": domain_name,
                "account_id": account_id
            }

            return result

        except Exception as e:
            error_msg = f"Erro ao processar mensagem: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "error",
                "routing": {
                    "crew_type": crew_type,
                    "channel_type": specific_channel,
                    "domain_name": domain_name,
                    "account_id": account_id
                }
            }

    def _determine_crew_type(self, message: Dict[str, Any], channel_type: str) -> tuple:
        """
        Determina o tipo de crew e canal específico com base na origem da mensagem.

        Args:
            message: A mensagem a ser processada
            channel_type: Canal de origem (WhatsApp, Instagram, etc.)

        Returns:
            Tupla (tipo_de_crew, canal_específico)
        """
        # Por padrão, usar customer_service como tipo de crew
        crew_type = "customer_service"

        # Determinar o canal específico
        specific_channel = "default"

        # Se o canal for Chatwoot, determinar o canal específico
        if channel_type == "chatwoot":
            source_id = message.get("source_id", "").lower()

            if "whatsapp" in source_id:
                specific_channel = "whatsapp"
            elif "instagram" in source_id:
                specific_channel = "instagram"
            elif "facebook" in source_id:
                specific_channel = "facebook"
            elif "twitter" in source_id or "x" in source_id:
                specific_channel = "twitter"
            elif "telegram" in source_id:
                specific_channel = "telegram"
            elif "web" in source_id:
                specific_channel = "web"
            else:
                specific_channel = "default"

        # Se for um canal específico direto, usar esse canal
        elif channel_type in ["whatsapp", "instagram", "facebook", "twitter", "telegram", "web"]:
            specific_channel = channel_type

        # Se for um tipo de crew específico, usar esse tipo
        elif channel_type in ["analytics", "sales", "support"]:
            crew_type = channel_type
            specific_channel = "default"

        logger.info(f"Determinado tipo de crew: {crew_type}, canal específico: {specific_channel}")
        return crew_type, specific_channel

    async def get_crew(self, crew_type: str, domain_name: str, account_id: str, channel_type: str = None) -> Any:
        """
        Obtém uma crew para um domínio, account_id e canal específicos.

        Implementa uma estratégia de cache em camadas:
        1. Verificar cache em memória
        2. Verificar Redis
        3. Criar nova crew

        Args:
            crew_type: Tipo de crew (ex: "customer_service", "analytics")
            domain_name: Nome do domínio
            account_id: ID da conta
            channel_type: Tipo de canal (ex: "whatsapp", "instagram")

        Returns:
            Instância da crew
        """
        # Chave de cache
        cache_key = f"crew:{crew_type}:{channel_type or 'default'}:{domain_name}:{account_id}"

        # Camada 1: Cache em memória
        if cache_key in self.memory_cache:
            logger.debug(f"Crew encontrada em cache de memória: {cache_key}")
            return self.memory_cache[cache_key]

        # Camada 2: Cache Redis
        if self.redis_client:
            try:
                # Obter cliente Redis assíncrono
                redis_async = await self._get_async_redis_client()
                if redis_async:
                    crew_data = await redis_async.get(cache_key)
                    if crew_data:
                        try:
                            # Tentar carregar como JSON primeiro (novo formato)
                            import json
                            crew_info = json.loads(crew_data)
                            # Criar nova crew com as informações armazenadas
                            crew = await self.crew_factory.create_crew(
                                crew_type=crew_info.get("crew_type"),
                                domain_name=crew_info.get("domain_name"),
                                account_id=crew_info.get("account_id"),
                                channel_type=crew_info.get("channel_type")
                            )
                            # Atualizar cache em memória
                            self.memory_cache[cache_key] = crew
                            logger.debug(f"Crew encontrada em Redis (formato JSON): {cache_key}")
                            return crew
                        except Exception as json_error:
                            logger.warning(f"Erro ao carregar crew do Redis como JSON: {json_error}")
                            # Tentar carregar como pickle (formato antigo) - apenas para compatibilidade
                            try:
                                import pickle
                                crew = pickle.loads(crew_data.encode('latin1') if isinstance(crew_data, str) else crew_data)
                                # Atualizar cache em memória
                                self.memory_cache[cache_key] = crew
                                logger.debug(f"Crew encontrada em Redis (formato pickle): {cache_key}")
                                return crew
                            except Exception as pickle_error:
                                logger.warning(f"Erro ao carregar crew do Redis como pickle: {pickle_error}")
                                # Se ambos falharem, vamos criar uma nova crew
            except Exception as e:
                logger.warning(f"Erro ao acessar Redis para crew {cache_key}: {e}")

        # Camada 3: Criar nova crew
        crew = await self.crew_factory.create_crew(
            crew_type=crew_type,
            domain_name=domain_name,
            account_id=account_id,
            channel_type=channel_type
        )

        # Atualizar cache em memória
        self.memory_cache[cache_key] = crew

        # Atualizar Redis se disponível
        if self.redis_client:
            try:
                # Obter cliente Redis assíncrono
                redis_async = await self._get_async_redis_client()
                if redis_async:
                    # Armazenar apenas as informações necessárias para recriar a crew
                    import json
                    crew_info = {
                        "crew_type": crew_type,
                        "domain_name": domain_name,
                        "account_id": account_id,
                        "channel_type": channel_type,
                        "timestamp": time.time()
                    }
                    crew_data = json.dumps(crew_info)
                    await redis_async.set(cache_key, crew_data, ex=3600)  # 1 hora
            except Exception as e:
                logger.warning(f"Erro ao armazenar crew em Redis: {e}")

        logger.info(f"Crew criada e armazenada em cache: {cache_key}")
        return crew

    async def finalize_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Finaliza uma conversa, liberando recursos.

        Args:
            conversation_id: ID da conversa a ser finalizada

        Returns:
            Resultado da finalização
        """
        # Na nova arquitetura, não precisamos fazer nada especial para finalizar a conversa
        return {
            "conversation_id": conversation_id,
            "status": "resolved",
            "success": True
        }

# Instância singleton
_hub = None

def get_hub(force_new=False, redis_client=None, config_registry=None, crew_factory=None) -> Hub:
    """
    Obtém a instância singleton do Hub.

    Args:
        force_new: Se True, força a criação de uma nova instância
        redis_client: Cliente Redis opcional
        config_registry: Registro de configurações opcional
        crew_factory: Fábrica de crews opcional

    Returns:
        Instância do Hub
    """
    global _hub

    if _hub is None or force_new:
        _hub = Hub(
            redis_client=redis_client,
            config_registry=config_registry,
            crew_factory=crew_factory
        )

    return _hub
