"""
WhatsApp Channel Crew para a arquitetura hub-and-spoke.

Esta crew é responsável por processar mensagens do WhatsApp,
normalizando-as e detectando intenções preliminares antes de enviá-las
para o Hub Crew para roteamento para as crews funcionais apropriadas.
"""

import logging
from typing import Dict, List, Any, Optional
import json
from crewai import Agent, Task, Crew, Process
from src.core.cache.agent_cache import RedisAgentCache

from src.agents.channel_agents import ChannelCrew
from src.utils.text_processor import normalize_text, extract_keywords
from src.core.memory import MemorySystem
from src.agents.core.data_proxy_agent import DataProxyAgent
from src.services.data.data_service_hub import DataServiceHub
from src.core.hub import HubCrew
from src.crews.sales_crew import SalesCrew
from src.crews.support_crew import SupportCrew
from src.crews.info_crew import InfoCrew
from src.crews.scheduling_crew import SchedulingCrew
from src.agents.channel_agents import MessageProcessorAgent, ChannelMonitorAgent
from src.core.domain import DomainManager
from src.plugins.plugin_manager import PluginManager
from src.tasks.whatsapp_tasks import create_whatsapp_tasks
from src.api.multi_instance_handler import get_instance_manager

logger = logging.getLogger(__name__)


class WhatsAppChannelCrew(ChannelCrew):
    """
    Crew especializada no canal WhatsApp.
    
    Esta crew processa mensagens do WhatsApp, normaliza-as e as encaminha
    para o Hub Crew, que por sua vez as encaminha para as crews funcionais
    apropriadas (Vendas, Suporte, Informações ou Agendamentos).
    """
    # Configuração Pydantic para permitir tipos arbitrários
    model_config = {"arbitrary_types_allowed": True, "validate_assignment": False}
    
    def __init__(self, 
                 memory_system: Optional[MemorySystem] = None,
                 data_service_hub: Optional[DataServiceHub] = None,
                 agent_cache: Optional[RedisAgentCache] = None,
                 domain_manager: Optional[DomainManager] = None,
                 plugin_manager: Optional[PluginManager] = None,
                 additional_tools: Optional[List[Any]] = None,
                 agents: Optional[List[Agent]] = None):
        """
        Inicializa a crew do WhatsApp.
        
        Args:
            memory_system: Sistema de memória compartilhada
            vector_tool: Ferramenta para busca vetorial
            db_tool: Ferramenta para busca no banco de dados
            cache_tool: Ferramenta para cache
            agent_cache: Cache para resultados de agentes
            domain_manager: Gerenciador de domínios de negócio
            plugin_manager: Gerenciador de plugins
            additional_tools: Ferramentas adicionais para os agentes
            agents: Lista de agentes CrewAI para esta crew
        """
        # Inicializa ferramentas e sistemas
        # Não atribuir diretamente devido ao modelo Pydantic
        memory_system = memory_system or MemorySystem()
        data_service_hub = data_service_hub or DataServiceHub()
        domain_manager = domain_manager or DomainManager()
        # Inicializa o plugin_manager com uma configuração vazia se não for fornecido
        plugin_manager = plugin_manager or PluginManager(config={})
        additional_tools = additional_tools or []
        
        # Inicializa a classe base com todos os parâmetros necessários
        # Criar um cliente Chatwoot para uso no ChannelCrew
        from src.api.chatwoot.client import ChatwootClient
        # Obter as configurações do Chatwoot da primeira instância
        instance_manager = get_instance_manager()
        first_instance = list(instance_manager.instances.values())[0] if instance_manager.instances else None
        
        # Obter a URL base e a chave API diretamente da instância
        chatwoot_base_url = first_instance.base_url if first_instance else 'http://localhost:3000'
        chatwoot_api_key = first_instance.api_key if first_instance else 'test_api_key'
        chatwoot_client = ChatwootClient(base_url=chatwoot_base_url, api_key=chatwoot_api_key)
        
        # Garantir que agents seja uma lista mesmo que None seja passado
        if agents is None:
            agents = []
            
        # Criar pelo menos um agente e uma tarefa simples para resolver o problema de validação
        from crewai import Agent, Task
        dummy_agent = Agent(
            role="Agente auxiliar",
            goal="Auxiliar o sistema",
            backstory="Um agente para contornar a validação do Pydantic",
            verbose=False,
            allow_delegation=False
        )
        
        dummy_task = Task(
            description="Tarefa auxiliar",
            expected_output="Nenhum",
            agent=dummy_agent
        )
            
        super().__init__(
            channel_type="WhatsApp", 
            memory_system=memory_system,
            data_proxy_agent=data_service_hub.get_data_proxy_agent(),
            chatwoot_client=chatwoot_client,
            additional_tools={"processor": additional_tools, "monitor": additional_tools},
            agent_cache=agent_cache,
            agents=[dummy_agent, *agents],
            tasks=[dummy_task]
        )
        
        # Armazenar estes objetos como atributos privados
        self.__dict__["_domain_manager"] = domain_manager
        self.__dict__["_plugin_manager"] = plugin_manager
        self.__dict__["_additional_tools"] = additional_tools
        self.__dict__["_data_service_hub"] = data_service_hub
        
        # Inicializar o atributo _agents para acessá-lo posteriormente via dict
        # Usamos self.agents que existe na classe base para inicializar
        self.__dict__["_agents"] = self.agents.copy() if self.agents else []
        
        # Inicializa o Hub Crew e as crews funcionais
        self._initialize_crews()
        
    def create_tasks(self):
        """Método necessário para a classe Crew, mas não usado nesta implementação.
        
        As tasks são criadas nos métodos específicos de ChannelCrew.
        """
        return []
    
    @property
    def domain_manager(self):
        return self.__dict__["_domain_manager"]
    
    @property
    def plugin_manager(self):
        return self.__dict__["_plugin_manager"]
        
    @property
    def data_service_hub(self):
        """Retorna o DataServiceHub."""
        return self.__dict__["_data_service_hub"]
    
    @property
    def additional_tools(self):
        """Retorna as ferramentas adicionais."""
        if "_additional_tools" in self.__dict__:
            return self.__dict__["_additional_tools"]
        return []
        
    @property
    def hub_crew(self):
        """Retorna o Hub Crew."""
        return self.__dict__["_hub_crew"]
        
    @property
    def functional_crews(self):
        """Retorna as crews funcionais."""
        return self.__dict__["_functional_crews"]
        
    @property
    def agents(self):
        """Retorna os agentes do canal."""
        return self.__dict__["_agents"]
        
    @agents.setter
    def agents(self, value):
        """Define os agentes do canal."""
        self.__dict__["_agents"] = value
    
    def initialize_tools(self) -> Dict[str, Any]:
        """Inicializa ferramentas específicas para o WhatsApp."""
        # Aqui poderíamos adicionar ferramentas específicas para o WhatsApp
        # como formatadores de mensagem específicos
        return {
            "message_formatter": None,  # Será implementado com uma ferramenta real
            "channel_api": None,        # Será implementado com uma ferramenta real
        }
    
    def normalize_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza uma mensagem do WhatsApp para um formato padrão.
        
        Args:
            message: A mensagem bruta do WhatsApp
            
        Returns:
            A mensagem normalizada
        """
        # Extrai o conteúdo da mensagem do formato do Chatwoot
        content = message.get('content', '')
        
        # Normaliza o texto usando o utilitário de processamento de texto
        normalized_content = normalize_text(content)
        
        # Extrai palavras-chave para análise de intenção
        keywords = extract_keywords(content)
        
        # Constrói a mensagem normalizada
        normalized_message = {
            'original_content': content,
            'normalized_content': normalized_content,
            'keywords': keywords,
            'sender': message.get('sender', {}).get('name', 'Unknown'),
            'timestamp': message.get('created_at'),
            'message_type': 'text'  # Pode ser 'text', 'image', 'audio', etc.
        }
        
        # Detecta se há anexos (imagens, áudio, etc.)
        if message.get('attachments'):
            normalized_message['attachments'] = message.get('attachments')
            normalized_message['message_type'] = 'media'
        
        return normalized_message
    
    def detect_preliminary_intent(self, message: Dict[str, Any]) -> str:
        """
        Detecta a intenção preliminar de uma mensagem.
        
        Args:
            message: A mensagem normalizada
            
        Returns:
            A intenção detectada
        """
        # Palavras-chave que indicam diferentes intenções
        intent_keywords = {
            'sales_inquiry': ['comprar', 'preço', 'promoção', 'desconto', 'valor', 'produto'],
            'support_request': ['problema', 'ajuda', 'suporte', 'não funciona', 'erro', 'dúvida'],
            'scheduling_request': ['agendar', 'horário', 'marcar', 'consulta', 'disponibilidade'],
            'feedback': ['feedback', 'avaliação', 'opinião', 'satisfação', 'experiência'],
            'marketing_inquiry': ['campanha', 'anúncio', 'marketing', 'divulgação', 'promoção']
        }
        
        # Verifica as palavras-chave na mensagem
        content = message.get('normalized_content', '').lower()
        keywords = message.get('keywords', [])
        
        # Conta ocorrências de palavras-chave por categoria
        intent_scores = {intent: 0 for intent in intent_keywords}
        
        for intent, kw_list in intent_keywords.items():
            for kw in kw_list:
                if kw in content:
                    intent_scores[intent] += 1
        
        # Seleciona a intenção com maior pontuação
        max_score = 0
        detected_intent = 'general_inquiry'  # Padrão
        
        for intent, score in intent_scores.items():
            if score > max_score:
                max_score = score
                detected_intent = intent
        
        return detected_intent
    
    def extract_metadata(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai metadados de uma mensagem.
        
        Args:
            message: A mensagem bruta do WhatsApp
            
        Returns:
            Os metadados extraídos
        """
        # Extrai metadados específicos do WhatsApp
        metadata = {
            'channel': 'whatsapp',
            'phone_number': message.get('sender', {}).get('phone_number'),
            'conversation_id': message.get('conversation', {}).get('id'),
            'inbox_id': message.get('inbox', {}).get('id')
        }
        
        return metadata
    
    def _initialize_crews(self):
        """
        Inicializa o Hub Crew e as crews funcionais.
        """
        # Inicializa o RedisAgentCache para o HubCrew
        from src.core.cache.agent_cache import RedisAgentCache
        import redis
        import os
        
        # Usa o agent_cache fornecido no construtor, ou cria um novo se não fornecido
        if self.agent_cache is None:
            # Obtém a URL do Redis da variável de ambiente ou usa o padrão
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = redis.from_url(redis_url)
            
            # Cria o cache de agentes
            self.agent_cache = RedisAgentCache(
                redis_client=redis_client,
                ttl=3600,  # 1 hora de TTL para os resultados em cache
                prefix='agent_cache:'
            )
        
        # Inicializa o Hub Crew com os parâmetros corretos
        hub_crew = HubCrew(
            memory_system=self.memory_system,
            data_service_hub=self.data_service_hub,
            additional_tools=self.additional_tools,
            agent_cache=self.agent_cache
        )
        
        # Armazenar no dicionário privado para evitar problemas com Pydantic
        self.__dict__["_hub_crew"] = hub_crew
        
        # Inicializa as crews funcionais
        functional_crews = {
            "sales": SalesCrew(
                memory_system=self.memory_system,
                data_service_hub=self.data_service_hub,
                agent_cache=self.agent_cache,
                domain_manager=self.domain_manager,
                plugin_manager=self.plugin_manager,
                additional_tools=self.additional_tools
            ),
            "support": SupportCrew(
                memory_system=self.memory_system,
                data_service_hub=self.data_service_hub,
                agent_cache=self.agent_cache,
                domain_manager=self.domain_manager,
                plugin_manager=self.plugin_manager,
                additional_tools=self.additional_tools
            ),
            "info": InfoCrew(
                memory_system=self.memory_system,
                data_service_hub=self.data_service_hub,
                agent_cache=self.agent_cache,
                domain_manager=self.domain_manager,
                plugin_manager=self.plugin_manager,
                additional_tools=self.additional_tools
            ),
            "scheduling": SchedulingCrew(
                memory_system=self.memory_system,
                data_service_hub=self.data_service_hub,
                agent_cache=self.agent_cache,
                domain_manager=self.domain_manager,
                plugin_manager=self.plugin_manager,
                additional_tools=self.additional_tools
            )
        }
        
        # Armazenar no dicionário privado para evitar problemas com Pydantic
        self.__dict__["_functional_crews"] = functional_crews
        
        # Inicializa os agentes específicos do canal, se não foram fornecidos
        if not self.__dict__["_agents"]:
            # Usar o dicionário privado para armazenar os agentes
            self.__dict__["_agents"] = self._create_channel_agents()
    
    def _create_channel_agents(self) -> List[Agent]:
        """
        Retorna os agentes já criados pelo ChannelCrew.
        
        Uma vez que a classe base ChannelCrew já inicializou os agentes,
        apenas retornamos os agentes existentes.
        
        Returns:
            List[Agent]: Lista de agentes
        """
        # Os agentes já foram criados pelo ChannelCrew, podemos usar self.processor e self.monitor
        # que são atributos definidos na classe base
        processor_agent = self.processor
        monitor_agent = self.monitor
        
        # Cria as tasks para os agentes
        self.tasks = self._create_tasks(processor_agent, monitor_agent)
        
        return [processor_agent, monitor_agent]
        
    def _create_tasks(self, processor_agent: Agent, monitor_agent: Agent) -> List[Task]:
        """
        Cria as tasks específicas para o WhatsApp Channel Crew.
        
        Args:
            processor_agent: Agente de processamento de mensagens
            monitor_agent: Agente de monitoramento do canal
            
        Returns:
            List[Task]: Lista de tasks
        """
        # Utiliza o módulo de tasks do WhatsApp para criar as tasks
        return create_whatsapp_tasks(processor_agent, monitor_agent)
    
    def process(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem recebida do WhatsApp.
        
        Args:
            message: A mensagem bruta do WhatsApp
            context: Contexto adicional para processamento
            
        Returns:
            O resultado processado com mensagem normalizada, intenção e metadados
        """
        logger.info(f"Processando mensagem do WhatsApp: {message.get('content', '')[:50]}...")
        
        # Verifica se há resultado em cache
        conversation_id = message.get('conversation', {}).get('id', '')
        message_id = message.get('id', '')
        cache_key = f"whatsapp:process:{conversation_id}:{message_id}"
        cached_result = self.cache_tool.get(cache_key)
        
        if cached_result:
            logger.info(f"Usando resultado em cache para mensagem {message_id}")
            return cached_result
        
        # Cria uma instância da Crew com as tasks específicas para esta mensagem
        # Isso permite que cada mensagem seja processada por uma instância dedicada da crew
        whatsapp_crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            process=Process.sequential  # Processa tasks sequencialmente
        )
        
        # Prepara o contexto para o processamento pelas tasks
        crew_context = {
            "message": message,
            "context": context,
            "domain": self.domain_manager.get_current_domain() if self.domain_manager else None,
            "erp_type": "odoo"  # Definindo Odoo como ERP padrão
        }
        
        # Executa a crew para processar a mensagem usando as tasks definidas
        try:
            logger.info("Iniciando processamento da mensagem com tasks específicas do WhatsApp")
            crew_result = whatsapp_crew.kickoff(inputs=crew_context)
            
            # Tenta extrair um objeto JSON do resultado
            try:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', crew_result, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Tenta parsear o resultado inteiro como JSON
                    result = json.loads(crew_result)
            except Exception as e:
                logger.warning(f"Não foi possível parsear o resultado como JSON: {e}")
                # Se não conseguir parsear, usa o resultado como string
                result = {
                    "message_processing_result": crew_result,
                    "error_parsing": str(e)
                }
            
            # Adiciona informações básicas ao resultado
            if isinstance(result, dict):
                # Extrai informações básicas para fallback
                normalized_message = result.get("normalized_message", self.normalize_message(message))
                intent = result.get("intent_analysis", {}).get("primary_intent", self.detect_preliminary_intent(normalized_message))
                metadata = result.get("extracted_metadata", self.extract_metadata(message))
            else:
                # Fallback para o método antigo se o resultado não for um dicionário
                normalized_message = self.normalize_message(message)
                intent = self.detect_preliminary_intent(normalized_message)
                metadata = self.extract_metadata(message)
                result = {
                    "raw_result": crew_result
                }
            
            # Prepara o contexto para o Hub Crew
            enriched_context = {
                **context,
                "preliminary_intent": intent,
                "channel_metadata": metadata,
                "channel_type": self.channel_type
            }
            
            # Integração com o Odoo para obter informações do cliente
            # Mantendo a flexibilidade para diferentes domínios de negócio
            from src.services.context.odoo_crm_context_service import OdooCRMContextService
            odoo_service = OdooCRMContextService()
            
            # Extrai informações de contato da mensagem
            contact_info = {
                'phone': metadata.get('sender_phone', ''),
                'name': metadata.get('sender_name', ''),
                'email': metadata.get('sender_email', '')
            }
            
            # Busca ou cria o cliente no Odoo, adaptando para o domínio de negócio atual
            domain_info = self.domain_manager.get_current_domain() if self.domain_manager else None
            customer_info = odoo_service.get_or_create_customer(
                contact_info=contact_info,
                domain_context=domain_info
            )
            
            # Adiciona informações do cliente e do domínio ao contexto
            enriched_context['customer_info'] = customer_info
            enriched_context['domain_info'] = domain_info
            
            # Processa através do Hub Crew com contexto enriquecido
            # Extraímos os parâmetros necessários do contexto para chamar o process_message corretamente
            conversation_id = enriched_context.get('conversation_id', 'unknown')
            channel_type = enriched_context.get('channel_type', self.channel_type)
            
            # Usamos a mensagem normalizada como entrada para o hub_crew.process_message
            hub_result = self.hub_crew.process_message(
                message=normalized_message,
                conversation_id=conversation_id,
                channel_type=channel_type
            )
            
            # Combina com o resultado do hub
            result.update(hub_result)
            
            # Roteia para a crew funcional apropriada
            functional_result = self.hub_crew.route_to_functional_crew(
                message=normalized_message,
                context=enriched_context,
                functional_crews=self.functional_crews
            )
            
            # Combina com o resultado da crew funcional
            result.update(functional_result)
            
            # Armazena a conversa no histórico do cliente
            if 'formatted_response' in result:
                odoo_service.store_conversation(
                    customer_id=customer_info.get('id'),
                    conversation={
                        'message': normalized_message.get('content', ''),
                        'response': result.get('formatted_response', ''),
                        'timestamp': metadata.get('timestamp', '')
                    }
                )
            
            # Adiciona informações específicas do WhatsApp ao resultado
            result["normalized_message"] = normalized_message
            result["preliminary_intent"] = intent
            result["channel_metadata"] = metadata
            result["channel_type"] = self.channel_type
            
            # Formata a resposta final
            result["formatted_response"] = self._format_response(result)
            
            logger.info(f"Mensagem processada com tasks. Roteada para: {result.get('hub_metadata', {}).get('original_target_crew', 'unknown')}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com tasks: {str(e)}")
            # Fallback para o método antigo se a execução da crew falhar
            normalized_message = self.normalize_message(message)
            intent = self.detect_preliminary_intent(normalized_message)
            metadata = self.extract_metadata(message)
            
            result = {
                "error": str(e),
                "normalized_message": normalized_message,
                "preliminary_intent": intent,
                "channel_metadata": metadata,
                "channel_type": self.channel_type,
                "formatted_response": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente mais tarde."
            }
        
        # Armazena o resultado em cache
        self.cache_tool.set(cache_key, result, ttl=3600)  # Cache por 1 hora
        
        return result
    
    def _format_response(self, result: Dict[str, Any]) -> str:
        """
        Formata a resposta final para o cliente.
        
        Args:
            result: Resultado do processamento
            
        Returns:
            str: Resposta formatada
        """
        # Verifica se já existe uma resposta formatada
        if "response" in result:
            if isinstance(result["response"], str):
                return result["response"]
            elif isinstance(result["response"], dict) and "text" in result["response"]:
                return result["response"]["text"]
        
        # Caso contrário, tenta extrair a resposta do resultado
        crew_type = result.get("hub_metadata", {}).get("original_target_crew", "unknown")
        
        if crew_type == "sales":
            # Formata resposta de vendas
            products = result.get("products", [])
            promotions = result.get("promotions", [])
            
            response_parts = []
            
            if "message" in result:
                response_parts.append(result["message"])
            
            if products:
                response_parts.append("\n\n*Produtos recomendados:*")
                for product in products[:3]:  # Limita a 3 produtos
                    name = product.get("name", "Produto")
                    price = product.get("price", "Preço sob consulta")
                    response_parts.append(f"• {name}: R$ {price}")
            
            if promotions:
                response_parts.append("\n\n*Promoções ativas:*")
                for promo in promotions[:2]:  # Limita a 2 promoções
                    name = promo.get("name", "Promoção")
                    desc = promo.get("description", "")
                    response_parts.append(f"• {name}: {desc}")
            
            return "\n".join(response_parts)
        
        elif crew_type == "support":
            # Formata resposta de suporte
            if "problem_analysis" in result:
                analysis = result["problem_analysis"]
                solutions = analysis.get("recommended_solutions", [])
                
                response_parts = []
                
                if "message" in result:
                    response_parts.append(result["message"])
                
                if solutions:
                    response_parts.append("\n\n*Soluções recomendadas:*")
                    for solution in solutions:
                        response_parts.append(f"• {solution.get('solution', '')}")
                
                return "\n".join(response_parts)
        
        elif crew_type == "scheduling":
            # Formata resposta de agendamento
            if "appointment" in result:
                appointment = result["appointment"]
                
                response_parts = []
                
                if "message" in result:
                    response_parts.append(result["message"])
                
                service = appointment.get("service", "Serviço")
                date = appointment.get("date", "Data")
                time = appointment.get("time", "Horário")
                
                response_parts.append(f"\n\n*Agendamento confirmado:*\n• Serviço: {service}\n• Data: {date}\n• Horário: {time}")
                
                return "\n".join(response_parts)
        
        # Resposta padrão para outros casos
        if "message" in result:
            return result["message"]
        
        # Fallback
        return "Obrigado por sua mensagem. Estamos processando sua solicitação."
