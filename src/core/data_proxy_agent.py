"""
DataProxyAgent para o ChatwootAI.

Este agente foi redesenhado para:
1. Conectar-se diretamente ao Odoo via MCP
2. Ler credenciais do YAML de domínio
3. Utilizar Redis para cache
4. Suportar múltiplos clientes simultaneamente

Principais responsabilidades:
1. Ser o ÚNICO ponto de acesso para consultas de dados no sistema
2. Traduzir consultas em linguagem natural para operações específicas
3. Implementar otimizações como caching e batching
4. Garantir consistência na formatação dos dados retornados
"""

import logging
import time
from typing import Dict, List, Any, Optional

from crewai import Agent
from crewai.tools.base_tool import BaseTool

# Importando serviços e ferramentas de suporte
from src.core.memory import MemorySystem
from src.core.domain.domain_manager import DomainManager
from src.utils.redis_client import get_redis_client, RedisCache

# Os clientes MCP serão importados dinamicamente conforme necessário
# para evitar import circular e permitir carregamento sob demanda

logger = logging.getLogger(__name__)


class DataAccessError(Exception):
    """Exceção lançada quando há erros de acesso a dados."""
    pass


class ConfigurationError(Exception):
    """Exceção lançada quando há erros de configuração."""
    pass


class DataProxyAgent:
    """
    Agente responsável por intermediar o acesso a dados para outros agentes.

    Este agente se conecta diretamente ao Odoo via MCP,
    lê credenciais do YAML de domínio e utiliza Redis para cache.
    """

    def __init__(self,
                 domain_manager: DomainManager,
                 memory_system: Optional[MemorySystem] = None,
                 additional_tools: Optional[List[BaseTool]] = None,
                 **kwargs):
        """
        Inicializa o agente de proxy de dados.

        Args:
            domain_manager: Gerenciador de domínios de negócio
            memory_system: Sistema de memória compartilhada (opcional)
            additional_tools: Ferramentas adicionais para o agente (opcional)
            **kwargs: Argumentos adicionais para a classe Agent
        """
        # Validar e armazenar atributos essenciais
        if not domain_manager:
            raise ConfigurationError("DomainManager é obrigatório para o DataProxyAgentV2")

        self._domain_manager = domain_manager
        self._memory_system = memory_system

        # Inicializar Redis para cache
        self._redis_client = get_redis_client()
        self._redis_cache = RedisCache(self._redis_client) if self._redis_client else None

        if self._redis_cache:
            logger.info("Redis cache inicializado para o DataProxyAgentV2")
        else:
            logger.warning("Redis não disponível, cache não será utilizado")

        # Configurar ferramentas padrão
        tools = []

        # Adicionar ferramentas adicionais se fornecidas
        if additional_tools:
            tools.extend(additional_tools)

        # Configuração padrão para o agente de proxy de dados
        default_config = {
            "role": "Data Proxy",
            "goal": "Fornecer acesso eficiente e adaptado ao domínio de negócio para todos os agentes",
            "backstory": """Você é o proxy de dados da arquitetura centralizada.
            Seu trabalho é facilitar o acesso a dados para outros agentes, traduzindo suas
            requisições em consultas otimizadas e garantindo que recebam dados em um
            formato consistente, independentemente da fonte de dados subjacente ou domínio de negócio.
            Você tem conhecimento profundo de estruturas de dados, otimização de consultas e
            esquemas específicos de domínio.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }

        # Sobrescrever padrões com kwargs fornecidos
        config = {**default_config, **kwargs}

        # Criar o agente CrewAI
        self._crew_agent = Agent(**config)

        # Estatísticas de acesso para otimização
        self._access_stats = {
            "products": {"count": 0, "avg_time": 0},
            "customers": {"count": 0, "avg_time": 0},
            "orders": {"count": 0, "avg_time": 0},
            "business_rules": {"count": 0, "avg_time": 0},
        }

        logger.info("DataProxyAgent inicializado com sucesso")

    def get_mcp_config(self, domain_name: str, account_id: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração do MCP (Message Control Program) para um domínio específico.

        Esta função primeiro verifica o cache Redis antes de carregar do YAML.
        Ela identifica qual tipo de MCP está configurado para o domínio e retorna suas configurações.

        Args:
            domain_name: Nome do domínio
            account_id: ID da conta (opcional)

        Returns:
            Dict[str, Any]: Configuração do MCP incluindo tipo e credenciais
        """
        # Construir a chave do cache
        cache_key = f"mcp_config:{domain_name}"
        if account_id:
            cache_key += f":{account_id}"

        # Verificar o cache primeiro
        if self._redis_cache:
            cached_config = self._redis_cache.get(cache_key)
            if cached_config:
                logger.debug(f"Configuração do MCP encontrada no cache para {domain_name}")
                return cached_config

        # Se não estiver no cache, carregar do YAML via DomainManager
        try:
            # Se account_id for fornecido, tentar obter a configuração específica da conta
            if account_id:
                # Obter a configuração da conta
                account_config = self._domain_manager.domain_loader.load_client_config(domain_name, account_id)
                if account_config:
                    # Extrair a configuração do MCP da conta
                    mcp_config = account_config.get("integrations", {}).get("mcp", {})
                    if mcp_config:
                        logger.debug(f"Configuração do MCP encontrada para a conta {account_id}")
                        return mcp_config

            # Se não encontrou configuração específica da conta ou account_id não foi fornecido,
            # obter a configuração do domínio
            domain_config = self._domain_manager.get_domain_config(domain_name)

            # Extrair a configuração do MCP
            mcp_config = domain_config.get("integrations", {}).get("mcp", {})

            # Se não houver configuração de MCP, tentar usar a configuração do Odoo (para compatibilidade)
            if not mcp_config:
                logger.warning(f"Configuração de MCP não encontrada para {domain_name}, tentando usar configuração do Odoo")
                odoo_config = domain_config.get("integrations", {}).get("odoo", {})
                if odoo_config:
                    # Criar uma configuração de MCP a partir da configuração do Odoo
                    mcp_config = {
                        "type": "odoo-mcp",
                        "config": odoo_config
                    }

            # Verificar se a configuração do MCP é válida
            if not mcp_config:
                raise ConfigurationError(f"Configuração de MCP não encontrada para o domínio {domain_name}")

            if "type" not in mcp_config:
                raise ConfigurationError(f"Tipo de MCP não especificado para o domínio {domain_name}")

            if "config" not in mcp_config:
                raise ConfigurationError(f"Configuração do MCP não encontrada para o domínio {domain_name}")

            # Verificar se as credenciais estão completas com base no tipo de MCP
            mcp_type = mcp_config["type"]
            config = mcp_config["config"]

            if mcp_type == "odoo-mcp":
                required_fields = ["url", "db", "username", "password"]
            elif mcp_type == "sap-mcp":
                required_fields = ["url", "client", "username", "password"]
            elif mcp_type == "salesforce-mcp":
                required_fields = ["url", "client_id", "client_secret", "username", "password"]
            else:
                # Para outros tipos de MCP, verificar campos básicos
                required_fields = ["url", "username", "password"]

            for field in required_fields:
                if field not in config:
                    raise ConfigurationError(f"Campo obrigatório '{field}' não encontrado na configuração do MCP {mcp_type} para o domínio {domain_name}")

            # Armazenar no cache se disponível
            if self._redis_cache:
                self._redis_cache.set(cache_key, mcp_config)
                logger.debug(f"Configuração do MCP armazenada no cache para {domain_name}")

            return mcp_config

        except Exception as e:
            logger.error(f"Erro ao obter configuração do MCP para o domínio {domain_name}: {str(e)}")
            raise DataAccessError(f"Não foi possível obter configuração do MCP para o domínio {domain_name}: {str(e)}")

    def create_mcp_client(self, domain_name: str, account_id: str = None) -> Any:
        """
        Cria um cliente MCP para um domínio específico com base no tipo de MCP configurado.

        Args:
            domain_name: Nome do domínio
            account_id: ID da conta (opcional)

        Returns:
            Any: Cliente MCP configurado (OdooClient, SAPClient, etc.)
        """
        # Obter a configuração do MCP
        mcp_config = self.get_mcp_config(domain_name, account_id)
        mcp_type = mcp_config["type"]
        config = mcp_config["config"]

        # Criar o cliente apropriado com base no tipo de MCP
        try:
            if mcp_type == "odoo-mcp":
                # Usar o módulo MCP-Odoo para criar o cliente
                from src.mcp_odoo import get_odoo_client_for_account

                # Tentar criar o cliente usando o domínio e account_id
                client = get_odoo_client_for_account(domain_name, account_id, self._domain_manager)

                # Se não conseguir criar o cliente usando o domínio e account_id, usar a configuração direta
                if not client:
                    from src.mcp_odoo import get_odoo_client
                    client = get_odoo_client(config)

                logger.info(f"Cliente Odoo-MCP criado com sucesso para o domínio {domain_name}")
                return client

            # Adicionar suporte para outros tipos de MCP conforme necessário
            # elif mcp_type == "sap-mcp":
            #     client = SAPClient(
            #         url=config["url"],
            #         client=config["client"],
            #         username=config["username"],
            #         password=config["password"]
            #     )
            #     logger.info(f"Cliente SAP-MCP criado com sucesso para o domínio {domain_name}")
            #     return client
            #
            # elif mcp_type == "salesforce-mcp":
            #     client = SalesforceClient(
            #         url=config["url"],
            #         client_id=config["client_id"],
            #         client_secret=config["client_secret"],
            #         username=config["username"],
            #         password=config["password"]
            #     )
            #     logger.info(f"Cliente Salesforce-MCP criado com sucesso para o domínio {domain_name}")
            #     return client

            else:
                raise ConfigurationError(f"Tipo de MCP não suportado: {mcp_type}")

        except Exception as e:
            logger.error(f"Erro ao criar cliente MCP para o domínio {domain_name}: {str(e)}")
            raise DataAccessError(f"Não foi possível criar cliente MCP para o domínio {domain_name}: {str(e)}")

    def query_products(self, query_text: str, filters: Dict[str, Any] = None, domain_name: str = None, account_id: str = None) -> Dict[str, Any]:
        """
        Consulta produtos no Odoo.

        Args:
            query_text: Texto da consulta
            filters: Filtros adicionais
            domain_name: Nome do domínio
            account_id: ID da conta

        Returns:
            Dict[str, Any]: Resultados da consulta
        """
        start_time = time.time()

        try:
            # Determinar o domínio a ser usado
            if not domain_name and hasattr(self, '_current_domain'):
                domain_name = self._current_domain
                logger.debug(f"Usando domínio do contexto: {domain_name}")

            if not domain_name and self._domain_manager:
                domain_name = self._domain_manager.get_active_domain()
                logger.debug(f"Usando domínio ativo: {domain_name}")

            if not domain_name:
                raise ConfigurationError("Domínio não especificado e não foi possível determinar o domínio ativo")

            # Criar cliente MCP
            mcp_client = self.create_mcp_client(domain_name, account_id)

            # Construir o domínio de busca do Odoo
            search_domain = []

            # Adicionar filtros de texto se fornecidos
            if query_text:
                search_domain.append(['name', 'ilike', query_text])

            # Adicionar filtros adicionais se fornecidos
            if filters:
                for key, value in filters.items():
                    search_domain.append([key, '=', value])

            # Realizar a busca
            results = mcp_client.search_read(
                model_name="product.product",
                domain=search_domain,
                fields=["name", "description", "list_price", "qty_available", "default_code"]
            )

            # Formatar a resposta
            response = {
                "success": True,
                "query": query_text,
                "domain": domain_name,
                "results": results,
                "count": len(results)
            }

            # Atualizar estatísticas
            self._update_access_stats("products", time.time() - start_time)

            return response

        except Exception as e:
            logger.error(f"Erro ao consultar produtos: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query_text,
                "domain": domain_name
            }

    def query_customers(self, query_text: str, filters: Dict[str, Any] = None, domain_name: str = None, account_id: str = None) -> Dict[str, Any]:
        """
        Consulta clientes no Odoo.

        Args:
            query_text: Texto da consulta
            filters: Filtros adicionais
            domain_name: Nome do domínio
            account_id: ID da conta

        Returns:
            Dict[str, Any]: Resultados da consulta
        """
        start_time = time.time()

        try:
            # Determinar o domínio a ser usado
            if not domain_name and hasattr(self, '_current_domain'):
                domain_name = self._current_domain
                logger.debug(f"Usando domínio do contexto: {domain_name}")

            if not domain_name and self._domain_manager:
                domain_name = self._domain_manager.get_active_domain()
                logger.debug(f"Usando domínio ativo: {domain_name}")

            if not domain_name:
                raise ConfigurationError("Domínio não especificado e não foi possível determinar o domínio ativo")

            # Criar cliente MCP
            mcp_client = self.create_mcp_client(domain_name, account_id)

            # Construir o domínio de busca do Odoo
            search_domain = []

            # Adicionar filtros de texto se fornecidos
            if query_text:
                search_domain.append(['name', 'ilike', query_text])

            # Adicionar filtros adicionais se fornecidos
            if filters:
                for key, value in filters.items():
                    search_domain.append([key, '=', value])

            # Realizar a busca
            results = mcp_client.search_read(
                model_name="res.partner",
                domain=search_domain,
                fields=["name", "email", "phone", "street", "city", "country_id"]
            )

            # Formatar a resposta
            response = {
                "success": True,
                "query": query_text,
                "domain": domain_name,
                "results": results,
                "count": len(results)
            }

            # Atualizar estatísticas
            self._update_access_stats("customers", time.time() - start_time)

            return response

        except Exception as e:
            logger.error(f"Erro ao consultar clientes: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query_text,
                "domain": domain_name
            }

    def query_orders(self, query_text: str, filters: Dict[str, Any] = None, domain_name: str = None, account_id: str = None) -> Dict[str, Any]:
        """
        Consulta pedidos no Odoo.

        Args:
            query_text: Texto da consulta
            filters: Filtros adicionais
            domain_name: Nome do domínio
            account_id: ID da conta

        Returns:
            Dict[str, Any]: Resultados da consulta
        """
        start_time = time.time()

        try:
            # Determinar o domínio a ser usado
            if not domain_name and hasattr(self, '_current_domain'):
                domain_name = self._current_domain
                logger.debug(f"Usando domínio do contexto: {domain_name}")

            if not domain_name and self._domain_manager:
                domain_name = self._domain_manager.get_active_domain()
                logger.debug(f"Usando domínio ativo: {domain_name}")

            if not domain_name:
                raise ConfigurationError("Domínio não especificado e não foi possível determinar o domínio ativo")

            # Criar cliente MCP
            mcp_client = self.create_mcp_client(domain_name, account_id)

            # Construir o domínio de busca do Odoo
            search_domain = []

            # Adicionar filtros de texto se fornecidos
            if query_text:
                search_domain.append(['name', 'ilike', query_text])

            # Adicionar filtros adicionais se fornecidos
            if filters:
                for key, value in filters.items():
                    search_domain.append([key, '=', value])

            # Realizar a busca
            results = mcp_client.search_read(
                model_name="sale.order",
                domain=search_domain,
                fields=["name", "partner_id", "date_order", "amount_total", "state"]
            )

            # Formatar a resposta
            response = {
                "success": True,
                "query": query_text,
                "domain": domain_name,
                "results": results,
                "count": len(results)
            }

            # Atualizar estatísticas
            self._update_access_stats("orders", time.time() - start_time)

            return response

        except Exception as e:
            logger.error(f"Erro ao consultar pedidos: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query_text,
                "domain": domain_name
            }

    def query_business_rules(self, query_text: str, category: str = None, domain_name: str = None, account_id: str = None) -> Dict[str, Any]:
        """
        Consulta regras de negócio no Odoo.

        Args:
            query_text: Texto da consulta
            category: Categoria das regras
            domain_name: Nome do domínio
            account_id: ID da conta

        Returns:
            Dict[str, Any]: Resultados da consulta
        """
        start_time = time.time()

        try:
            # Determinar o domínio a ser usado
            if not domain_name and hasattr(self, '_current_domain'):
                domain_name = self._current_domain
                logger.debug(f"Usando domínio do contexto: {domain_name}")

            if not domain_name and self._domain_manager:
                domain_name = self._domain_manager.get_active_domain()
                logger.debug(f"Usando domínio ativo: {domain_name}")

            if not domain_name:
                raise ConfigurationError("Domínio não especificado e não foi possível determinar o domínio ativo")

            # Criar cliente MCP
            mcp_client = self.create_mcp_client(domain_name, account_id)

            # Construir o domínio de busca do Odoo
            search_domain = []

            # Adicionar filtros de texto se fornecidos
            if query_text:
                search_domain.append(['name', 'ilike', query_text])

            # Adicionar filtro de categoria se fornecido
            if category:
                search_domain.append(['category', '=', category])

            # Realizar a busca
            # Nota: Assumindo que existe um modelo 'business.rule' no Odoo
            # Se não existir, será necessário adaptar para o modelo correto
            results = mcp_client.search_read(
                model_name="business.rule",
                domain=search_domain,
                fields=["name", "description", "category", "active"]
            )

            # Formatar a resposta
            response = {
                "success": True,
                "query": query_text,
                "domain": domain_name,
                "results": results,
                "count": len(results)
            }

            # Atualizar estatísticas
            self._update_access_stats("business_rules", time.time() - start_time)

            return response

        except Exception as e:
            logger.error(f"Erro ao consultar regras de negócio: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query_text,
                "domain": domain_name
            }

    def fetch_data(self, data_type: str, query_params: Dict[str, Any] = None) -> Any:
        """
        Método unificado para busca de dados que encaminha para o método específico com base no tipo de dados.

        Args:
            data_type: O tipo de dados a ser consultado (ex: 'products', 'customers', 'orders', etc.)
            query_params: Parâmetros da consulta, variando conforme o tipo de dados

        Returns:
            Any: Resultados da consulta, formatados de acordo com o tipo de dados
        """
        if not query_params:
            query_params = {}

        # Log da requisição
        logger.debug(f"DataProxyAgentV2.fetch_data: tipo={data_type}, params={query_params}")

        try:
            # Extrair parâmetros comuns
            query_text = query_params.get('query', '')
            domain_name = query_params.get('domain')
            account_id = query_params.get('account_id')

            # Encaminhar para o método específico com base no tipo de dados
            if data_type == 'products':
                return self.query_products(
                    query_text=query_text,
                    filters=query_params.get('filters'),
                    domain_name=domain_name,
                    account_id=account_id
                )

            elif data_type == 'customers':
                return self.query_customers(
                    query_text=query_text,
                    filters=query_params.get('filters'),
                    domain_name=domain_name,
                    account_id=account_id
                )

            elif data_type == 'orders':
                return self.query_orders(
                    query_text=query_text,
                    filters=query_params.get('filters'),
                    domain_name=domain_name,
                    account_id=account_id
                )

            elif data_type == 'business_rules':
                return self.query_business_rules(
                    query_text=query_text,
                    category=query_params.get('category'),
                    domain_name=domain_name,
                    account_id=account_id
                )

            else:
                logger.warning(f"Tipo de dados desconhecido: {data_type}")
                return {"error": f"Tipo de dados não suportado: {data_type}"}

        except Exception as e:
            logger.error(f"Erro ao buscar dados do tipo {data_type}: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return {"error": f"Falha na busca de dados: {str(e)}"}

    def _update_access_stats(self, data_type, time_elapsed):
        """
        Atualiza as estatísticas de acesso para um tipo de dados.

        Args:
            data_type: O tipo de dados acessado
            time_elapsed: O tempo gasto na operação
        """
        if data_type in self._access_stats:
            stats = self._access_stats[data_type]
            count = stats["count"] + 1
            avg_time = ((stats["avg_time"] * stats["count"]) + time_elapsed) / count
            self._access_stats[data_type] = {"count": count, "avg_time": avg_time}

    @property
    def agent(self):
        """Obtém o agente CrewAI interno."""
        return self._crew_agent
