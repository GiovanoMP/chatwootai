"""
MCP-Crew Core v2 - Orquestrador Principal com Provisão Dinâmica de Ferramentas
Sistema atualizado para descoberta dinâmica de ferramentas e compartilhamento de conhecimento
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
from concurrent.futures import ThreadPoolExecutor

# Importações do CrewAI
try:
    from crewai import Agent, Task, Crew
    from crewai_tools import MCPServerAdapter
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI não disponível. Usando simulação.")

from src.config import Config, redis_manager, serialize_json, deserialize_json, get_cache_key
from src.mcp_tool_discovery import tool_discovery, ToolMetadata
from src.knowledge_sharing import knowledge_manager, KnowledgeItem, KnowledgeType

logger = logging.getLogger(__name__)

@dataclass
class CrewExecutionResult:
    """Resultado da execução de uma crew"""
    crew_name: str
    success: bool
    result: Any
    execution_time: float
    tools_used: List[str]
    knowledge_created: List[str]
    knowledge_consumed: List[str]
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class DynamicMCPCrewOrchestrator:
    """Orquestrador principal do MCP-Crew com provisão dinâmica de ferramentas"""
    
    def __init__(self):
        self.active_crews: Dict[str, Any] = {}
        self.mcp_adapters: Dict[str, Any] = {}
        self.execution_metrics: Dict[str, Any] = {}
        self.knowledge_subscriptions: Dict[str, List[str]] = {}
        
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa requisição com descoberta dinâmica de ferramentas"""
        start_time = time.time()
        
        try:
            # Extrair informações da requisição
            account_id = request_data.get('account_id')
            payload = request_data.get('payload', {})
            channel = request_data.get('channel', 'api')
            
            if not account_id:
                return self._create_error_response("account_id é obrigatório")
            
            # Descobrir ferramentas disponíveis
            logger.info(f"🔍 Descobrindo ferramentas para {account_id}")
            available_tools = await tool_discovery.discover_all_tools(account_id)
            
            if not available_tools:
                logger.warning(f"⚠️ Nenhuma ferramenta descoberta para {account_id}")
            
            # Analisar requisição e determinar crew apropriada
            crew_selection = await self._analyze_and_select_crew(payload, available_tools)
            
            # Executar crew com ferramentas dinâmicas
            execution_result = await self._execute_crew_with_dynamic_tools(
                account_id, crew_selection, available_tools, payload
            )
            
            # Processar resultado e compartilhar conhecimento
            await self._process_execution_result(account_id, execution_result)
            
            # Calcular métricas
            execution_time = time.time() - start_time
            
            # Atualizar métricas
            self._update_metrics(account_id, execution_result, execution_time)
            
            return {
                "success": execution_result.success,
                "result": execution_result.result,
                "crew_used": execution_result.crew_name,
                "tools_used": execution_result.tools_used,
                "knowledge_created": execution_result.knowledge_created,
                "execution_time": execution_time,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar requisição: {e}")
            return self._create_error_response(f"Erro interno: {str(e)}")
    
    async def _analyze_and_select_crew(self, payload: Dict[str, Any], available_tools: Dict[str, List[ToolMetadata]]) -> Dict[str, Any]:
        """Analisa requisição e seleciona crew apropriada"""
        text = payload.get('text', '').lower()
        
        # Lógica de seleção baseada no conteúdo
        if any(keyword in text for keyword in ['produto', 'item', 'comprar', 'preço', 'estoque']):
            return {
                'name': 'product_inquiry_crew',
                'type': 'product_research',
                'priority': 'high',
                'required_mcps': ['mcp-mongodb', 'mcp-qdrant']
            }
        elif any(keyword in text for keyword in ['agendar', 'reunião', 'compromisso', 'horário']):
            return {
                'name': 'scheduling_crew',
                'type': 'scheduling',
                'priority': 'medium',
                'required_mcps': ['mcp-mongodb', 'mcp-chatwoot']
            }
        elif any(keyword in text for keyword in ['suporte', 'ajuda', 'problema', 'dúvida']):
            return {
                'name': 'support_crew',
                'type': 'customer_support',
                'priority': 'high',
                'required_mcps': ['mcp-chatwoot', 'mcp-mongodb']
            }
        elif any(keyword in text for keyword in ['análise', 'relatório', 'dados', 'estatística']):
            return {
                'name': 'analytics_crew',
                'type': 'data_analysis',
                'priority': 'low',
                'required_mcps': ['mcp-mongodb', 'mcp-redis']
            }
        else:
            return {
                'name': 'general_crew',
                'type': 'general_assistance',
                'priority': 'medium',
                'required_mcps': ['mcp-mongodb']
            }
    
    async def _execute_crew_with_dynamic_tools(
        self, 
        account_id: str, 
        crew_selection: Dict[str, Any], 
        available_tools: Dict[str, List[ToolMetadata]], 
        payload: Dict[str, Any]
    ) -> CrewExecutionResult:
        """Executa crew com ferramentas descobertas dinamicamente"""
        start_time = time.time()
        crew_name = crew_selection['name']
        
        try:
            # Coletar ferramentas necessárias
            required_mcps = crew_selection.get('required_mcps', [])
            crew_tools = []
            tools_used = []
            
            for mcp_name in required_mcps:
                if mcp_name in available_tools:
                    mcp_tools = available_tools[mcp_name]
                    crew_tools.extend(mcp_tools)
                    tools_used.extend([tool.name for tool in mcp_tools])
                    logger.info(f"🔧 Adicionadas {len(mcp_tools)} ferramentas do {mcp_name}")
            
            # Buscar conhecimento relevante
            knowledge_consumed = await self._gather_relevant_knowledge(account_id, payload, crew_selection)
            
            # Executar crew (simulação se CrewAI não disponível)
            if CREWAI_AVAILABLE:
                result = await self._execute_real_crew(crew_name, crew_tools, payload, knowledge_consumed)
            else:
                result = await self._simulate_crew_execution(crew_name, crew_tools, payload, knowledge_consumed)
            
            # Criar conhecimento baseado no resultado
            knowledge_created = await self._create_knowledge_from_result(
                account_id, crew_name, result, payload
            )
            
            execution_time = time.time() - start_time
            
            return CrewExecutionResult(
                crew_name=crew_name,
                success=True,
                result=result,
                execution_time=execution_time,
                tools_used=tools_used,
                knowledge_created=knowledge_created,
                knowledge_consumed=knowledge_consumed,
                metadata={
                    'required_mcps': required_mcps,
                    'tools_count': len(crew_tools)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na execução da crew {crew_name}: {e}")
            return CrewExecutionResult(
                crew_name=crew_name,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                tools_used=[],
                knowledge_created=[],
                knowledge_consumed=[],
                error_message=str(e)
            )
    
    async def _execute_real_crew(self, crew_name: str, tools: List[ToolMetadata], payload: Dict[str, Any], knowledge: List[str]) -> Any:
        """Executa crew real usando CrewAI"""
        try:
            # Converter ToolMetadata para ferramentas CrewAI
            crewai_tools = []
            
            # Agrupar ferramentas por MCP para criar adaptadores
            tools_by_mcp = {}
            for tool in tools:
                mcp_name = tool.mcp_source
                if mcp_name not in tools_by_mcp:
                    tools_by_mcp[mcp_name] = []
                tools_by_mcp[mcp_name].append(tool)
            
            # Criar adaptadores MCP
            for mcp_name, mcp_tools in tools_by_mcp.items():
                if mcp_name in Config.MCP_REGISTRY:
                    mcp_config = Config.MCP_REGISTRY[mcp_name]
                    try:
                        # Criar adaptador para o MCP
                        adapter = MCPServerAdapter({"url": mcp_config.url})
                        crewai_tools.extend(adapter.tools)
                        logger.info(f"✅ Adaptador criado para {mcp_name}")
                    except Exception as e:
                        logger.error(f"❌ Erro ao criar adaptador para {mcp_name}: {e}")
            
            # Criar agentes baseados no tipo de crew
            agents = self._create_agents_for_crew(crew_name, crewai_tools, knowledge)
            
            # Criar tarefas
            tasks = self._create_tasks_for_crew(crew_name, agents, payload)
            
            # Executar crew
            crew = Crew(agents=agents, tasks=tasks, verbose=True)
            result = crew.kickoff()
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na execução real da crew: {e}")
            raise
    
    async def _simulate_crew_execution(self, crew_name: str, tools: List[ToolMetadata], payload: Dict[str, Any], knowledge: List[str]) -> Any:
        """Simula execução de crew quando CrewAI não está disponível"""
        text = payload.get('text', '')
        
        # Simulações específicas por tipo de crew
        if 'product' in crew_name:
            return {
                "type": "product_recommendation",
                "products": [
                    {
                        "name": "Smartphone Samsung Galaxy",
                        "price": "R$ 1.299,00",
                        "availability": "Em estoque",
                        "rating": 4.5
                    }
                ],
                "recommendation": f"Baseado na sua consulta '{text}', encontrei produtos relevantes.",
                "tools_used": [tool.name for tool in tools],
                "knowledge_used": knowledge
            }
        elif 'scheduling' in crew_name:
            return {
                "type": "scheduling_result",
                "suggested_times": ["14:00", "15:30", "16:00"],
                "calendar_updated": True,
                "confirmation": f"Agendamento processado para: {text}",
                "tools_used": [tool.name for tool in tools]
            }
        elif 'support' in crew_name:
            return {
                "type": "support_response",
                "solution": f"Para resolver '{text}', recomendo verificar as configurações.",
                "escalation_needed": False,
                "satisfaction_survey": True,
                "tools_used": [tool.name for tool in tools]
            }
        elif 'analytics' in crew_name:
            return {
                "type": "analytics_report",
                "metrics": {
                    "total_requests": 150,
                    "success_rate": 0.95,
                    "avg_response_time": "2.3s"
                },
                "insights": f"Análise gerada para: {text}",
                "tools_used": [tool.name for tool in tools]
            }
        else:
            return {
                "type": "general_response",
                "message": f"Processado: {text}",
                "status": "completed",
                "tools_used": [tool.name for tool in tools],
                "knowledge_used": knowledge
            }
    
    def _create_agents_for_crew(self, crew_name: str, tools: List, knowledge: List[str]) -> List:
        """Cria agentes para a crew especificada"""
        if not CREWAI_AVAILABLE:
            return []
        
        agents = []
        
        if 'product' in crew_name:
            researcher = Agent(
                role="Pesquisador de Produtos",
                goal="Encontrar produtos relevantes usando ferramentas disponíveis",
                backstory="Sou especialista em pesquisa de produtos com acesso a sistemas avançados.",
                tools=tools,
                verbose=True
            )
            agents.append(researcher)
            
        elif 'scheduling' in crew_name:
            scheduler = Agent(
                role="Agendador",
                goal="Gerenciar agendamentos e calendários",
                backstory="Sou especialista em organização de tempo e agendamentos.",
                tools=tools,
                verbose=True
            )
            agents.append(scheduler)
            
        # Adicionar mais agentes conforme necessário
        
        return agents
    
    def _create_tasks_for_crew(self, crew_name: str, agents: List, payload: Dict[str, Any]) -> List:
        """Cria tarefas para a crew especificada"""
        if not CREWAI_AVAILABLE or not agents:
            return []
        
        tasks = []
        text = payload.get('text', '')
        
        if 'product' in crew_name:
            task = Task(
                description=f"Pesquisar produtos relacionados a: {text}",
                agent=agents[0],
                expected_output="Lista de produtos relevantes com detalhes"
            )
            tasks.append(task)
            
        elif 'scheduling' in crew_name:
            task = Task(
                description=f"Processar solicitação de agendamento: {text}",
                agent=agents[0],
                expected_output="Confirmação de agendamento com horários disponíveis"
            )
            tasks.append(task)
            
        return tasks
    
    async def _gather_relevant_knowledge(self, account_id: str, payload: Dict[str, Any], crew_selection: Dict[str, Any]) -> List[str]:
        """Coleta conhecimento relevante para a execução"""
        try:
            text = payload.get('text', '')
            crew_type = crew_selection.get('type', '')
            
            # Buscar conhecimento por tópico relacionado
            topic_mapping = {
                'product_research': KnowledgeType.PRODUCT_INFO,
                'customer_support': KnowledgeType.CUSTOMER_INSIGHT,
                'scheduling': KnowledgeType.CONVERSATION_SUMMARY,
                'data_analysis': KnowledgeType.ANALYSIS_RESULT
            }
            
            knowledge_items = []
            if crew_type in topic_mapping:
                items = knowledge_manager.search_knowledge_by_topic(
                    account_id, 
                    topic_mapping[crew_type].value, 
                    limit=5
                )
                knowledge_items.extend(items)
            
            # Buscar por conteúdo se houver texto específico
            if len(text) > 10:  # Apenas para textos significativos
                content_items = knowledge_manager.search_knowledge_by_content(
                    account_id, 
                    text, 
                    limit=3
                )
                knowledge_items.extend(content_items)
            
            # Converter para lista de IDs
            knowledge_ids = [item.id for item in knowledge_items]
            
            if knowledge_ids:
                logger.info(f"📚 Encontrados {len(knowledge_ids)} itens de conhecimento relevantes")
            
            return knowledge_ids
            
        except Exception as e:
            logger.error(f"Erro ao coletar conhecimento: {e}")
            return []
    
    async def _create_knowledge_from_result(self, account_id: str, crew_name: str, result: Any, payload: Dict[str, Any]) -> List[str]:
        """Cria itens de conhecimento baseados no resultado da execução"""
        try:
            knowledge_items = []
            
            # Determinar tipo de conhecimento baseado na crew
            if 'product' in crew_name:
                knowledge_type = KnowledgeType.PRODUCT_INFO
                topic = "product_research"
            elif 'support' in crew_name:
                knowledge_type = KnowledgeType.CUSTOMER_INSIGHT
                topic = "customer_support"
            elif 'analytics' in crew_name:
                knowledge_type = KnowledgeType.ANALYSIS_RESULT
                topic = "data_analysis"
            else:
                knowledge_type = KnowledgeType.GENERAL_FACT
                topic = "general"
            
            # Criar item de conhecimento
            knowledge_item = KnowledgeItem(
                id="",  # Será gerado automaticamente
                type=knowledge_type,
                topic=topic,
                title=f"Resultado de {crew_name}",
                content={
                    "result": result,
                    "original_query": payload.get('text', ''),
                    "crew_used": crew_name
                },
                metadata={
                    "channel": payload.get('channel', 'api'),
                    "execution_timestamp": time.time()
                },
                source_agent=f"{crew_name}_orchestrator",
                source_crew=crew_name,
                account_id=account_id,
                created_at=time.time(),
                tags=[crew_name, topic],
                confidence_score=0.8
            )
            
            # Armazenar conhecimento
            if knowledge_manager.store_knowledge(knowledge_item):
                knowledge_items.append(knowledge_item.id)
                logger.info(f"💾 Conhecimento criado: {knowledge_item.id}")
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Erro ao criar conhecimento: {e}")
            return []
    
    async def _process_execution_result(self, account_id: str, execution_result: CrewExecutionResult):
        """Processa resultado da execução e realiza ações pós-processamento"""
        try:
            # Atualizar cache de resultados recentes
            cache_key = get_cache_key(account_id, "recent_executions", "list")
            
            result_summary = {
                "crew_name": execution_result.crew_name,
                "success": execution_result.success,
                "execution_time": execution_result.execution_time,
                "timestamp": time.time(),
                "tools_count": len(execution_result.tools_used),
                "knowledge_created": len(execution_result.knowledge_created)
            }
            
            # Manter apenas os últimos 10 resultados
            cached_results = redis_manager.get(cache_key)
            if cached_results:
                results_list = deserialize_json(cached_results)
            else:
                results_list = []
            
            results_list.insert(0, result_summary)
            results_list = results_list[:10]  # Manter apenas os 10 mais recentes
            
            redis_manager.set(cache_key, serialize_json(results_list), Config.DEFAULT_CACHE_TTL)
            
        except Exception as e:
            logger.error(f"Erro ao processar resultado: {e}")
    
    def _update_metrics(self, account_id: str, execution_result: CrewExecutionResult, execution_time: float):
        """Atualiza métricas de execução"""
        try:
            metrics_key = get_cache_key(account_id, "metrics", "execution")
            
            # Obter métricas existentes
            cached_metrics = redis_manager.get(metrics_key)
            if cached_metrics:
                metrics = deserialize_json(cached_metrics)
            else:
                metrics = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "total_execution_time": 0,
                    "crews_used": {},
                    "tools_usage": {},
                    "last_updated": time.time()
                }
            
            # Atualizar métricas
            metrics["total_executions"] += 1
            if execution_result.success:
                metrics["successful_executions"] += 1
            
            metrics["total_execution_time"] += execution_time
            
            # Contadores por crew
            crew_name = execution_result.crew_name
            if crew_name not in metrics["crews_used"]:
                metrics["crews_used"][crew_name] = 0
            metrics["crews_used"][crew_name] += 1
            
            # Contadores por ferramenta
            for tool in execution_result.tools_used:
                if tool not in metrics["tools_usage"]:
                    metrics["tools_usage"][tool] = 0
                metrics["tools_usage"][tool] += 1
            
            metrics["last_updated"] = time.time()
            
            # Salvar métricas atualizadas
            redis_manager.set(metrics_key, serialize_json(metrics), Config.DEFAULT_CACHE_TTL)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")
    
    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """Cria resposta de erro padronizada"""
        return {
            "success": False,
            "error": message,
            "timestamp": time.time()
        }
    
    def get_metrics(self, account_id: str) -> Dict[str, Any]:
        """Obtém métricas de execução"""
        try:
            metrics_key = get_cache_key(account_id, "metrics", "execution")
            cached_metrics = redis_manager.get(metrics_key)
            
            if cached_metrics:
                metrics = deserialize_json(cached_metrics)
                
                # Calcular métricas derivadas
                if metrics["total_executions"] > 0:
                    metrics["success_rate"] = metrics["successful_executions"] / metrics["total_executions"]
                    metrics["avg_execution_time"] = metrics["total_execution_time"] / metrics["total_executions"]
                else:
                    metrics["success_rate"] = 0
                    metrics["avg_execution_time"] = 0
                
                return metrics
            
            return {"message": "Nenhuma métrica disponível"}
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {e}")
            return {"error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtém status de saúde do sistema"""
        try:
            # Verificar disponibilidade dos MCPs
            mcp_status = {}
            for mcp_name, mcp_config in Config.MCP_REGISTRY.items():
                try:
                    import requests
                    response = requests.get(f"{mcp_config.url}/health", timeout=5)
                    mcp_status[mcp_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time": response.elapsed.total_seconds()
                    }
                except Exception:
                    mcp_status[mcp_name] = {
                        "status": "unreachable",
                        "response_time": None
                    }
            
            # Status geral
            healthy_mcps = sum(1 for status in mcp_status.values() if status["status"] == "healthy")
            total_mcps = len(mcp_status)
            
            return {
                "status": "healthy" if healthy_mcps > 0 else "degraded",
                "redis_available": redis_manager.redis_available,
                "crewai_available": CREWAI_AVAILABLE,
                "mcps": mcp_status,
                "mcp_health_ratio": f"{healthy_mcps}/{total_mcps}",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar saúde: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }

# Instância global do orquestrador
mcp_crew_orchestrator = DynamicMCPCrewOrchestrator()

