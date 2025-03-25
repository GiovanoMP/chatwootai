#!/usr/bin/env python3
"""
GenericCrew para o ChatwootAI

Este módulo implementa a GenericCrew, uma classe base para todas as crews
configuradas via YAML, eliminando a necessidade de classes específicas para
cada tipo de crew e permitindo a configuração dinâmica de comportamentos.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from crewai import Crew, Agent, Task

# Configurar logging
logger = logging.getLogger(__name__)

class GenericCrew:
    """
    Implementação genérica de uma crew configurável via YAML.
    
    Esta classe substitui implementações específicas como SalesCrew, SupportCrew, etc.,
    permitindo que todas as crews sejam configuradas via YAML sem necessidade
    de classes específicas para cada domínio de negócio.
    """
    
    def __init__(self, crew: Crew, domain_name: str = None, crew_id: str = None, data_proxy_agent = None, 
                 agent_id_map: Dict[str, Agent] = None, task_id_map: Dict[str, Task] = None):
        """
        Inicializa uma GenericCrew.
        
        Args:
            crew: Instância da Crew do CrewAI
            domain_name: Nome do domínio associado à crew
            crew_id: Identificador único da crew
            data_proxy_agent: Agente de proxy para acesso a dados
            agent_id_map: Mapeamento de IDs personalizados para objetos Agent
            task_id_map: Mapeamento de IDs personalizados para objetos Task
        """
        self.crew = crew
        self.domain_name = domain_name
        self.crew_id = crew_id
        self.data_proxy_agent = data_proxy_agent
        self.agent_id_map = agent_id_map or {}
        self.task_id_map = task_id_map or {}
        
        # Metadados adicionais
        self.metadata = {
            "domain_name": domain_name,
            "crew_id": crew_id,
            "type": "generic"
        }
        
        logger.info(f"GenericCrew inicializada: {crew_id} para domínio {domain_name}")
    
    @property
    def name(self) -> str:
        """Nome da crew, composto pelo domínio e o ID."""
        domain_prefix = self.domain_name.capitalize() if self.domain_name else ""
        crew_suffix = self.crew_id.replace("_", " ").title().replace(" ", "")
        return f"{domain_prefix}{crew_suffix}"
        
    @property
    def agents(self) -> List[Agent]:
        """Retorna a lista de agentes da crew."""
        return getattr(self.crew, 'agents', [])
        
    @property
    def tasks(self) -> List[Task]:
        """Retorna a lista de tarefas da crew."""
        return getattr(self.crew, 'tasks', [])
    
    async def process(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem usando a crew configurada.
        
        Este método é chamado pelo HubCrew quando uma mensagem é roteada para esta crew.
        Implementa o processamento assíncrono da mensagem utilizando a configuração
        definida no YAML do domínio.
        
        Args:
            message: Mensagem a ser processada
            context: Contexto da conversa
            
        Returns:
            Resposta processada
        """
        try:
            logger.info(f"Processando mensagem com GenericCrew {self.crew_id} para domínio {self.domain_name}")
            
            # Extrair informações relevantes da mensagem
            message_content = message.get("content", "")
            sender_id = message.get("sender_id", "unknown")
            
            # Adicionar informações do domínio ao contexto
            processing_context = {
                **context,
                "domain_name": self.domain_name,
                "crew_id": self.crew_id,
                "message_content": message_content,
                "sender_id": sender_id
            }
            
            # Verificar se temos acesso ao DataProxyAgent
            if self.data_proxy_agent:
                # Obter configurações específicas do domínio
                domain_config = self.get_active_domain_config()
                if domain_config:
                    processing_context["domain_config"] = domain_config
                    
                    # Obter configurações específicas da crew
                    crew_config = domain_config.get("crews", {}).get(self.crew_id, {})
                    if crew_config:
                        processing_context["crew_config"] = crew_config
            
            # Preparar os dados para a crew
            crew_input = {
                "message": message_content,
                "context": processing_context
            }
            
            # Executar o processamento com a crew do CrewAI
            # Usando asyncio.to_thread para executar operações síncronas em thread separada
            result = await asyncio.to_thread(self.crew.kickoff, inputs=crew_input)
            
            # Processar o resultado
            if isinstance(result, str):
                response = {
                    "content": result,
                    "metadata": {
                        "crew_id": self.crew_id,
                        "domain_name": self.domain_name,
                        "processed_by": "generic_crew"
                    }
                }
            else:
                response = {
                    "content": str(result),
                    "raw_result": result,
                    "metadata": {
                        "crew_id": self.crew_id,
                        "domain_name": self.domain_name,
                        "processed_by": "generic_crew"
                    }
                }
            
            logger.info(f"Mensagem processada com sucesso pela GenericCrew {self.crew_id}")
            return response
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com GenericCrew {self.crew_id}: {str(e)}")
            # Retornar erro formatado
            return {
                "error": str(e),
                "metadata": {
                    "crew_id": self.crew_id,
                    "domain_name": self.domain_name,
                    "processed_by": "generic_crew",
                    "success": False
                }
            }
    
    def get_active_domain_config(self) -> Dict[str, Any]:
        """
        Obtém a configuração do domínio ativo.
        
        Returns:
            Configuração do domínio ou None se não disponível
        """
        if not self.data_proxy_agent or not self.domain_name:
            return None
            
        try:
            # Usar o DataProxyAgent para obter a configuração do domínio
            domain_config = self.data_proxy_agent.fetch_data(
                "domain_config", 
                {"domain_name": self.domain_name}
            )
            return domain_config
        except Exception as e:
            logger.warning(f"Erro ao obter configuração do domínio {self.domain_name}: {str(e)}")
            return None
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre esta crew.
        
        Returns:
            Dicionário com informações da crew
        """
        agents_info = []
        if hasattr(self.crew, 'agents'):
            for agent in self.crew.agents:
                agent_info = {
                    "id": getattr(agent, 'id', 'unknown'),
                    "role": getattr(agent, 'role', 'unknown'),
                    "tools": [tool.__class__.__name__ for tool in getattr(agent, 'tools', [])]
                }
                agents_info.append(agent_info)
        
        return {
            "crew_id": self.crew_id,
            "domain_name": self.domain_name,
            "type": "generic",
            "agents": agents_info,
            "tasks": len(getattr(self.crew, 'tasks', [])),
            "has_data_proxy": self.data_proxy_agent is not None
        }
        
    def run(self, inputs: Optional[Dict[str, Any]] = None) -> Any:
        """
        Executa a crew com os inputs fornecidos.
        
        Este método é um wrapper para o método kickoff da classe Crew do CrewAI,
        mantido para compatibilidade com código existente que espera um método run.
        
        Args:
            inputs: Dados de entrada para a crew
            
        Returns:
            Resultado da execução da crew
        """
        logger.info(f"Executando GenericCrew {self.crew_id} para domínio {self.domain_name}")
        try:
            # Registrar o mapeamento de IDs para debug
            if self.agent_id_map:
                logger.debug(f"Mapeamento de IDs de agentes: {', '.join(self.agent_id_map.keys())}")
            
            # Usar o método kickoff da Crew do CrewAI
            result = self.crew.kickoff(inputs=inputs)
            return result
        except Exception as e:
            logger.error(f"Erro ao executar GenericCrew {self.crew_id}: {str(e)}")
            raise
    
    def process_message(self, message: str) -> str:
        """
        Processa uma mensagem de texto simples e retorna uma resposta.
        
        Este método é uma simplificação do método process assíncrono, criado para
        facilitar o uso em testes e interfaces síncronas.
        
        Args:
            message: Mensagem de texto a ser processada
            
        Returns:
            Resposta processada como texto
        """
        logger.info(f"Processando mensagem simples com GenericCrew {self.crew_id}")
        try:
            # Registrar o mapeamento de IDs de agentes para debug
            if self.agent_id_map:
                logger.debug(f"Mapeamento de IDs de agentes disponível: {', '.join(self.agent_id_map.keys())}")
            
            # Preparar os dados para a crew
            crew_input = {
                "message": message,
                "context": {
                    "domain_name": self.domain_name,
                    "crew_id": self.crew_id,
                    "agent_id_map": self.agent_id_map  # Incluir o mapeamento no contexto para uso nas tarefas
                }
            }
            
            # Executar a crew
            result = self.run(inputs=crew_input)
            
            # Garantir que o resultado seja uma string
            if isinstance(result, str):
                return result
            else:
                return str(result)
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com GenericCrew {self.crew_id}: {str(e)}")
            return f"Erro ao processar mensagem: {str(e)}"
