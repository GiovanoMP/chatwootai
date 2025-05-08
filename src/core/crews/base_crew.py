#!/usr/bin/env python3
"""
BaseCrew para o ChatwootAI

Este módulo implementa a classe base para todas as crews específicas por canal,
definindo a interface comum e comportamentos padrão.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from crewai import Crew, Agent, Task

# Configurar logging
logger = logging.getLogger(__name__)

class BaseCrew:
    """
    Classe base para todas as crews específicas por canal.
    
    Esta classe define a interface comum e comportamentos padrão para
    todas as crews específicas por canal, como WhatsAppCrew, InstagramCrew, etc.
    """
    
    def __init__(self, config: Dict[str, Any], domain_name: str, account_id: str):
        """
        Inicializa a crew base.
        
        Args:
            config: Configuração da crew
            domain_name: Nome do domínio
            account_id: ID da conta
        """
        self.config = config
        self.domain_name = domain_name
        self.account_id = account_id
        
        # Metadados da crew
        self.metadata = {
            "domain_name": domain_name,
            "account_id": account_id,
            "type": "base"
        }
        
        # Inicializar agentes e crew
        self.agents = self._create_agents()
        self.crew = self._create_crew()
        
        logger.info(f"BaseCrew inicializada para {domain_name}/{account_id}")
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes para a crew.
        
        Este método deve ser sobrescrito pelas classes filhas para criar
        agentes específicos para cada canal.
        
        Returns:
            Lista de agentes
        """
        # Implementação base - deve ser sobrescrita
        logger.warning("Método _create_agents() não implementado na classe filha")
        return []
    
    def _create_crew(self) -> Crew:
        """
        Cria a crew com os agentes e tarefas.
        
        Returns:
            Instância da Crew
        """
        # Verificar se temos agentes
        if not self.agents:
            logger.warning("Tentativa de criar crew sem agentes")
            raise ValueError("Não é possível criar uma crew sem agentes")
        
        # Criar tarefas
        tasks = self._create_tasks()
        
        # Criar a crew
        crew_kwargs = {
            "agents": self.agents,
            "tasks": tasks,
            "verbose": True
        }
        
        # Adicionar nome se disponível na configuração
        if "name" in self.config:
            crew_kwargs["name"] = self.config["name"]
        else:
            crew_kwargs["name"] = f"{self.domain_name.capitalize()}Crew"
        
        # Adicionar descrição se disponível na configuração
        if "description" in self.config:
            crew_kwargs["description"] = self.config["description"]
        
        # Criar a crew
        crew = Crew(**crew_kwargs)
        
        logger.info(f"Crew criada com {len(self.agents)} agentes e {len(tasks)} tarefas")
        return crew
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas para a crew.
        
        Este método pode ser sobrescrito pelas classes filhas para criar
        tarefas específicas para cada canal.
        
        Returns:
            Lista de tarefas
        """
        # Implementação base - pode ser sobrescrita
        logger.warning("Método _create_tasks() não implementado na classe filha")
        return []
    
    async def process(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem com a crew.
        
        Args:
            message: Mensagem a ser processada
            context: Contexto da conversa
            
        Returns:
            Resultado do processamento
        """
        logger.info(f"Processando mensagem com {self.__class__.__name__}")
        
        try:
            # Preparar input para a crew
            crew_input = self._prepare_crew_input(message, context)
            
            # Executar a crew em uma thread separada para não bloquear o event loop
            result = await asyncio.to_thread(self.crew.kickoff, inputs=crew_input)
            
            # Processar o resultado
            processed_result = self._process_result(result)
            
            logger.info(f"Mensagem processada com sucesso por {self.__class__.__name__}")
            return processed_result
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com {self.__class__.__name__}: {str(e)}")
            return {
                "error": str(e),
                "status": "error",
                "content": f"Ocorreu um erro ao processar sua mensagem: {str(e)}"
            }
    
    def _prepare_crew_input(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara o input para a crew.
        
        Este método pode ser sobrescrito pelas classes filhas para preparar
        o input específico para cada canal.
        
        Args:
            message: Mensagem a ser processada
            context: Contexto da conversa
            
        Returns:
            Input para a crew
        """
        # Implementação base - pode ser sobrescrita
        return {
            "message": message.get("content", ""),
            "sender_id": message.get("sender_id", ""),
            "conversation_id": context.get("conversation_id", ""),
            "channel_type": context.get("channel_type", ""),
            "account_id": self.account_id,
            "domain_name": self.domain_name
        }
    
    def _process_result(self, result: Any) -> Dict[str, Any]:
        """
        Processa o resultado da crew.
        
        Este método pode ser sobrescrito pelas classes filhas para processar
        o resultado específico para cada canal.
        
        Args:
            result: Resultado da crew
            
        Returns:
            Resultado processado
        """
        # Implementação base - pode ser sobrescrita
        if isinstance(result, str):
            return {
                "content": result,
                "status": "success",
                "metadata": {
                    "crew_type": self.__class__.__name__,
                    "domain_name": self.domain_name,
                    "account_id": self.account_id
                }
            }
        elif isinstance(result, dict):
            result.setdefault("status", "success")
            result.setdefault("metadata", {})
            result["metadata"].update({
                "crew_type": self.__class__.__name__,
                "domain_name": self.domain_name,
                "account_id": self.account_id
            })
            return result
        else:
            return {
                "content": str(result),
                "status": "success",
                "metadata": {
                    "crew_type": self.__class__.__name__,
                    "domain_name": self.domain_name,
                    "account_id": self.account_id
                }
            }
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre a crew.
        
        Returns:
            Informações sobre a crew
        """
        return {
            "type": self.__class__.__name__,
            "domain_name": self.domain_name,
            "account_id": self.account_id,
            "agents_count": len(self.agents),
            "tasks_count": len(getattr(self.crew, "tasks", [])),
            "config": {
                "name": self.config.get("name", ""),
                "description": self.config.get("description", "")
            }
        }
