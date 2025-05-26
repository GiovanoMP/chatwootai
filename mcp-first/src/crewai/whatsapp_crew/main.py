"""
WhatsAppCrew - Crew especializada para atendimento via WhatsApp

Esta crew é responsável por processar mensagens recebidas via WhatsApp,
utilizando o protocolo MCP para acessar dados e funcionalidades.
"""

import os
from typing import Dict, Any, List, Optional
import json
import requests
from crewai import Agent, Crew, Task, Process
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class WhatsAppCrew:
    """Crew especializada para atendimento via WhatsApp."""
    
    def __init__(self, account_id: str):
        """
        Inicializa a WhatsAppCrew para um tenant específico.
        
        Args:
            account_id: Identificador do tenant
        """
        self.account_id = account_id
        self.mcp_odoo_url = os.getenv("MCP_ODOO_URL", "http://localhost:8000")
        self.mcp_mongodb_url = os.getenv("MCP_MONGODB_URL", "http://localhost:8001")
        self.mcp_qdrant_url = os.getenv("MCP_QDRANT_URL", "http://localhost:8002")
        
        # Carregar configurações do tenant
        self.config = self._load_tenant_config()
        
        # Inicializar agentes
        self.agents = self._initialize_agents()
        
        # Criar a crew
        self.crew = self._create_crew()
    
    def _load_tenant_config(self) -> Dict[str, Any]:
        """
        Carrega configurações específicas do tenant via MCP-MongoDB.
        
        Returns:
            Configurações do tenant
        """
        try:
            # Chamar MCP-MongoDB para obter configurações
            response = requests.post(
                f"{self.mcp_mongodb_url}/tools/call",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "aggregate",
                        "arguments": {
                            "collection": "company_metadata",
                            "pipeline": [
                                {"$match": {"account_id": self.account_id}},
                                {"$limit": 1}
                            ]
                        }
                    }
                }
            )
            
            result = response.json()
            
            if result.get("result", {}).get("success", False):
                config_data = result.get("result", {}).get("content", [{}])[0].get("json", [{}])[0]
                return config_data
            else:
                print(f"Erro ao carregar configurações: {result.get('error')}")
                return {}
        
        except Exception as e:
            print(f"Erro ao conectar ao MCP-MongoDB: {str(e)}")
            return {}
    
    def _initialize_agents(self) -> Dict[str, Agent]:
        """
        Inicializa os agentes da crew com contexto do tenant.
        
        Returns:
            Dicionário de agentes
        """
        # Contexto da empresa baseado nas configurações
        company_context = f"""
        Você está atendendo clientes da empresa {self.config.get('company_name', 'Empresa')}.
        Horário de atendimento: {self.config.get('business_hours', '9h às 18h')}.
        Serviços oferecidos: {', '.join(self.config.get('services', ['Informações gerais']))}.
        Estilo de comunicação: {self.config.get('communication_style', 'Profissional e amigável')}.
        """
        
        # Agente de Intenção - Identifica a intenção do cliente
        intention_agent = Agent(
            name="Agente de Intenção",
            llm="gpt-4",
            system_prompt=f"""
            {company_context}
            
            Você é um especialista em identificar a intenção por trás das mensagens dos clientes.
            Sua função é analisar a mensagem e classificá-la em uma das seguintes categorias:
            - Informação sobre produtos
            - Suporte técnico
            - Reclamação
            - Agendamento
            - Consulta de pedido
            - Outros (especificar)
            
            Forneça uma classificação precisa e uma breve justificativa.
            """
        )
        
        # Agente de Produtos - Especialista em informações sobre produtos
        product_agent = Agent(
            name="Agente de Produtos",
            llm="gpt-4",
            system_prompt=f"""
            {company_context}
            
            Você é um especialista em produtos da empresa.
            Utilize o MCP-Qdrant para buscar informações sobre produtos e o MCP-Odoo para verificar
            preços e disponibilidade em tempo real.
            
            Forneça informações precisas e detalhadas sobre os produtos, incluindo:
            - Descrição
            - Características
            - Preço
            - Disponibilidade
            - Opções de pagamento
            
            Sempre verifique os dados mais recentes antes de responder.
            """
        )
        
        # Agente de Suporte - Especialista em resolver problemas técnicos
        support_agent = Agent(
            name="Agente de Suporte",
            llm="gpt-4",
            system_prompt=f"""
            {company_context}
            
            Você é um especialista em suporte técnico.
            Utilize o MCP-Qdrant para buscar procedimentos de suporte e o MCP-Odoo para verificar
            informações sobre o cliente e seus produtos.
            
            Siga estas etapas ao atender um cliente:
            1. Identifique o problema específico
            2. Busque procedimentos relevantes
            3. Forneça instruções passo a passo
            4. Verifique se o problema foi resolvido
            5. Ofereça alternativas se necessário
            
            Seja paciente e claro em suas explicações.
            """
        )
        
        # Agente de Finalização - Formata a resposta final
        finalizer_agent = Agent(
            name="Agente de Finalização",
            llm="gpt-4",
            system_prompt=f"""
            {company_context}
            
            Você é responsável por formatar a resposta final ao cliente.
            Sua função é garantir que a resposta seja:
            - Clara e objetiva
            - Alinhada com o estilo de comunicação da empresa
            - Personalizada para o cliente
            - Gramaticalmente correta
            
            Adicione uma saudação inicial e uma despedida adequada.
            """
        )
        
        return {
            "intention": intention_agent,
            "product": product_agent,
            "support": support_agent,
            "finalizer": finalizer_agent
        }
    
    def _create_crew(self) -> Crew:
        """
        Cria a crew com os agentes e tarefas definidas.
        
        Returns:
            Objeto Crew configurado
        """
        # Tarefa: Identificar intenção
        identify_intention_task = Task(
            description="Analise a mensagem do cliente e identifique a intenção principal.",
            agent=self.agents["intention"],
            expected_output="Categoria de intenção e justificativa"
        )
        
        # Tarefa: Buscar informações de produto
        product_info_task = Task(
            description="Busque informações detalhadas sobre o produto mencionado pelo cliente.",
            agent=self.agents["product"],
            expected_output="Informações completas sobre o produto"
        )
        
        # Tarefa: Fornecer suporte técnico
        support_task = Task(
            description="Forneça instruções de suporte técnico para resolver o problema do cliente.",
            agent=self.agents["support"],
            expected_output="Instruções passo a passo para resolver o problema"
        )
        
        # Tarefa: Finalizar resposta
        finalize_response_task = Task(
            description="Formate a resposta final ao cliente com base nas informações coletadas.",
            agent=self.agents["finalizer"],
            expected_output="Resposta final formatada"
        )
        
        # Criar a crew
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=[
                identify_intention_task,
                product_info_task,
                support_task,
                finalize_response_task
            ],
            verbose=True,
            process=Process.sequential  # Processar tarefas sequencialmente
        )
        
        return crew
    
    def process_message(self, message: str, conversation_id: str) -> str:
        """
        Processa uma mensagem recebida via WhatsApp.
        
        Args:
            message: Texto da mensagem
            conversation_id: ID da conversa
        
        Returns:
            Resposta ao cliente
        """
        print(f"Processando mensagem para account_id: {self.account_id}")
        print(f"Mensagem: {message}")
        print(f"Conversa ID: {conversation_id}")
        
        # Aqui implementaremos a lógica para processar a mensagem
        # usando a crew e os agentes configurados
        
        # Por enquanto, retornamos uma resposta simples
        return f"Mensagem recebida: {message}. Em breve implementaremos o processamento completo."
    
    def send_response(self, response: str, conversation_id: str) -> bool:
        """
        Envia uma resposta ao cliente via Chatwoot.
        
        Args:
            response: Texto da resposta
            conversation_id: ID da conversa
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            # Aqui implementaremos a chamada à API do Chatwoot
            # para enviar a resposta ao cliente
            
            print(f"Enviando resposta para conversa {conversation_id}: {response}")
            return True
        
        except Exception as e:
            print(f"Erro ao enviar resposta: {str(e)}")
            return False


# Exemplo de uso
if __name__ == "__main__":
    # Criar uma instância da WhatsAppCrew para um tenant específico
    crew = WhatsAppCrew(account_id="tenant1")
    
    # Processar uma mensagem de exemplo
    response = crew.process_message(
        message="Olá, gostaria de saber mais sobre o produto XYZ",
        conversation_id="12345"
    )
    
    # Enviar a resposta
    crew.send_response(response, conversation_id="12345")
