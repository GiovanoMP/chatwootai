"""
Agentes de Canal (Channel Agents) para a arquitetura hub-and-spoke do ChatwootAI.

Este módulo contém implementações de agentes responsáveis por processar 
mensagens de diferentes canais de comunicação (WhatsApp, Instagram, etc.)
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process

from src.core.base_crew import BaseCrew
from src.core.memory import MemorySystem
from src.core.data_proxy_agent import DataProxyAgent
from src.utils.text_processor import normalize_text, extract_keywords

logger = logging.getLogger(__name__)

class ChannelCrew(BaseCrew):
    """
    Crew responsável por processar mensagens de um canal específico.
    
    Esta equipe de agentes:
    - Processa mensagens de um canal específico (WhatsApp, Instagram, etc.)
    - Normaliza o formato das mensagens
    - Extrai entidades e intenções
    - Monitora o status do canal
    - Categoriza preliminarmente as mensagens
    """
    
    def __init__(self, 
                channel_name: str,
                memory_system: Optional[MemorySystem] = None,
                data_proxy_agent: Optional[DataProxyAgent] = None):
        """
        Inicializa o ChannelCrew.
        
        Args:
            channel_name: Nome do canal
            memory_system: Sistema de memória compartilhada
            data_proxy_agent: Agente proxy para acesso a dados
        """
        self.channel_name = channel_name
        self.memory_system = memory_system
        self.data_proxy_agent = data_proxy_agent
        
        # Cria os agentes da crew
        self.processor_agent = MessageProcessorAgent(
            channel_name=channel_name,
            memory_system=memory_system,
            data_proxy_agent=data_proxy_agent
        )
        
        self.monitor_agent = ChannelMonitorAgent(
            channel_name=channel_name,
            memory_system=memory_system,
            data_proxy_agent=data_proxy_agent
        )
        
        # Define os agentes da crew
        agents = [
            self.processor_agent.agent,
            self.monitor_agent.agent
        ]
        
        # Inicializa a crew (usando apenas os parâmetros compatíveis com BaseCrew)
        super().__init__(
            name=f"{channel_name}Crew",
            agents=agents
        )
        
        # Armazena configurações adicionais que seriam usadas em Crew do CrewAI
        self.__dict__["_process_type"] = Process.sequential
        self.__dict__["_verbose"] = True
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem do canal.
        
        Args:
            message: Mensagem original
            
        Returns:
            Dict[str, Any]: Mensagem processada e normalizada
        """
        # Verifica se o canal está disponível
        channel_status = self.monitor_agent.check_status()
        
        if channel_status.get("status") != "online":
            return {
                "status": "error",
                "error": f"Canal {self.channel_name} não está disponível",
                "channel_status": channel_status
            }
        
        # Verifica se a mensagem está em um formato válido
        if not self._validate_message(message):
            return {
                "status": "error",
                "error": "Formato de mensagem inválido",
                "message": message
            }
        
        # Processa a mensagem com o agente processador
        processed_message = self.processor_agent.process(message)
        
        # Verifica se ocorreu algum erro no processamento
        if processed_message.get("status") == "error":
            return processed_message
        
        return processed_message
    
    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """
        Valida se a mensagem está em um formato válido.
        
        Args:
            message: Mensagem a ser validada
            
        Returns:
            bool: True se a mensagem é válida, False caso contrário
        """
        # Verifica campos mínimos obrigatórios
        required_fields = ["id", "content", "sender"]
        
        for field in required_fields:
            if field not in message:
                logger.error(f"Campo obrigatório '{field}' não encontrado na mensagem")
                return False
        
        # Verifica se o conteúdo não está vazio
        if not message.get("content"):
            logger.error("Conteúdo da mensagem está vazio")
            return False
        
        return True


class MessageProcessorAgent:
    """
    Agente responsável por processar e normalizar mensagens de um canal específico.
    
    Este agente aplica técnicas de NLP para:
    - Normalizar o texto (remover caracteres especiais, corrigir erros comuns)
    - Extrair entidades (nomes, produtos, valores)
    - Detectar intenções preliminares
    - Categorizar preliminarmente as mensagens
    """
    
    def __init__(
            self,
            channel_name: str,
            memory_system: Optional[MemorySystem] = None,
            data_proxy_agent: Optional[DataProxyAgent] = None
        ):
        """
        Inicializa o MessageProcessorAgent.
        
        Args:
            channel_name: Nome do canal que este agente vai processar
            memory_system: Sistema de memória para manter contexto
            data_proxy_agent: Agente proxy para acessar dados necessários
        """
        self.channel_name = channel_name
        self.memory_system = memory_system
        self.data_proxy_agent = data_proxy_agent
        
        # Criar o agente CrewAI
        self.agent = Agent(
            role=f"Processador de Mensagens do {channel_name}",
            goal=f"Analisar e normalizar mensagens do canal {channel_name}",
            backstory=f"Especialista em NLP dedicado a processar mensagens do {channel_name} "
                    f"para extrair significado e intenções, facilitando a resposta adequada.",
            verbose=True
        )
    
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem do canal.
        
        Args:
            message: Mensagem original
            
        Returns:
            Mensagem processada com metadados enriquecidos
        """
        try:
            # Extrai o conteúdo da mensagem
            content = message.get("content", "")
            
            # Normaliza o texto
            normalized_content = normalize_text(content)
            
            # Extrai palavras-chave
            keywords = extract_keywords(normalized_content)
            
            # Determina preliminarmente a categoria
            category = self._determine_category(normalized_content, keywords)
            
            # Enriquece a mensagem com os metadados processados
            processed_message = message.copy()
            processed_message.update({
                "normalized_content": normalized_content,
                "keywords": keywords,
                "category": category,
                "channel": self.channel_name,
                "status": "processed"
            })
            
            return processed_message
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return {
                "status": "error",
                "error": f"Erro ao processar mensagem: {str(e)}",
                "message": message
            }
    
    def _determine_category(self, content: str, keywords: List[str]) -> str:
        """
        Determina a categoria preliminar da mensagem.
        
        Args:
            content: Conteúdo normalizado da mensagem
            keywords: Palavras-chave extraídas
            
        Returns:
            str: Categoria da mensagem
        """
        # Categorias possíveis
        categories = {
            "sales": ["comprar", "produto", "preço", "promoção", "desconto", "oferta"],
            "support": ["problema", "ajuda", "dúvida", "não funciona", "quebrado", "erro"],
            "scheduling": ["agendar", "marcar", "horário", "consulta", "disponível", "quando"]
        }
        
        # Conta ocorrências de palavras-chave por categoria
        category_scores = {category: 0 for category in categories}
        
        for keyword in keywords:
            for category, category_keywords in categories.items():
                if any(cat_keyword in keyword.lower() for cat_keyword in category_keywords):
                    category_scores[category] += 1
        
        # Obtém a categoria com maior pontuação
        if max(category_scores.values()) > 0:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        # Se não houver correspondência, retorna "general"
        return "general"


class ChannelMonitorAgent:
    """
    Agente responsável por monitorar o status e eventos de um canal específico.
    
    Este agente:
    - Monitora a disponibilidade do canal
    - Detecta falhas de comunicação
    - Acompanha métricas de uso
    - Alerta sobre eventos importantes
    """
    
    def __init__(
            self,
            channel_name: str,
            memory_system: Optional[MemorySystem] = None,
            data_proxy_agent: Optional[DataProxyAgent] = None
        ):
        """
        Inicializa o ChannelMonitorAgent.
        
        Args:
            channel_name: Nome do canal que este agente vai monitorar
            memory_system: Sistema de memória para manter contexto
            data_proxy_agent: Agente proxy para acessar dados necessários
        """
        self.channel_name = channel_name
        self.memory_system = memory_system
        self.data_proxy_agent = data_proxy_agent
        
        # Criar o agente CrewAI
        self.agent = Agent(
            role=f"Monitor do Canal {channel_name}",
            goal=f"Garantir a disponibilidade e monitorar eventos do canal {channel_name}",
            backstory=f"Vigilante dedicado que continuamente avalia a saúde e performance "
                    f"do canal {channel_name}, identificando problemas antes que afetem usuários.",
            verbose=True
        )
    
    def check_status(self) -> Dict[str, Any]:
        """
        Verifica o status atual do canal.
        
        Returns:
            Status do canal com métricas
        """
        try:
            # Simula verificação de status
            # Em produção, faria uma checagem real no sistema do canal
            status = "online"
            
            # Coleta métricas do canal
            metrics = self._collect_metrics()
            
            return {
                "status": status,
                "channel": self.channel_name,
                "metrics": metrics,
                "timestamp": "2023-08-10T15:30:45"
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar status do canal {self.channel_name}: {str(e)}")
            return {
                "status": "error",
                "error": f"Erro ao verificar status: {str(e)}",
                "channel": self.channel_name
            }
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """
        Coleta métricas do canal.
        
        Returns:
            Dict[str, Any]: Métricas do canal
        """
        # Simulação de métricas
        # Em produção, obteria métricas reais dos sistemas
        return {
            "message_count_24h": 152,
            "response_time_avg": "00:02:35",
            "active_conversations": 8,
            "error_rate": 0.02,
            "satisfaction_score": 4.7
        }
