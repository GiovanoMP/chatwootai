"""
MCP-Odoo - Servidor MCP para integração com Odoo ERP

Este servidor implementa o protocolo MCP (Model Context Protocol) para permitir
que agentes de IA interajam com o Odoo ERP de forma padronizada.
"""

import os
import json
import xmlrpc.client
import fastmcp as mcp
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import redis
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp-odoo")

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Odoo
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# Configurações do Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redispassword")

# Cliente Redis para cache
redis_client = redis.Redis.from_url(
    REDIS_URL, 
    password=REDIS_PASSWORD,
    decode_responses=True
)

class OdooClient:
    """Cliente para comunicação com o Odoo via XML-RPC."""
    
    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Inicializa o cliente Odoo.
        
        Args:
            url: URL do servidor Odoo
            db: Nome do banco de dados
            username: Nome de usuário
            password: Senha
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self._models = None
        self._connect()
    
    def _connect(self):
        """Estabelece conexão com o servidor Odoo."""
        try:
            self._common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self.uid = self._common.authenticate(self.db, self.username, self.password, {})
            self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
            logger.info(f"Conectado ao Odoo {self.url} como {self.username} (uid: {self.uid})")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Odoo: {str(e)}")
            raise
    
    def execute(self, model: str, method: str, *args, **kwargs):
        """
        Executa um método em um modelo do Odoo.
        
        Args:
            model: Nome do modelo Odoo
            method: Nome do método a ser executado
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
        
        Returns:
            Resultado da execução do método
        """
        try:
            return self._models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs
            )
        except Exception as e:
            logger.error(f"Erro ao executar {model}.{method}: {str(e)}")
            raise
    
    def search_read(self, model: str, domain: List, fields: List[str], **kwargs):
        """
        Busca e lê registros de um modelo do Odoo.
        
        Args:
            model: Nome do modelo Odoo
            domain: Domínio de busca
            fields: Campos a serem retornados
            **kwargs: Argumentos adicionais (limit, offset, order)
        
        Returns:
            Lista de registros
        """
        try:
            return self.execute(model, 'search_read', domain, fields, **kwargs)
        except Exception as e:
            logger.error(f"Erro ao buscar registros de {model}: {str(e)}")
            raise
    
    def get_models(self) -> List[str]:
        """
        Obtém a lista de modelos disponíveis no Odoo.
        
        Returns:
            Lista de nomes de modelos
        """
        # Verificar cache
        cache_key = f"odoo:models:{self.db}"
        cached = redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        try:
            # Obter lista de modelos do Odoo
            models = self.execute('ir.model', 'search_read', [], ['model', 'name'])
            model_list = [{"model": m['model'], "name": m['name']} for m in models]
            
            # Armazenar em cache (1 hora)
            redis_client.setex(cache_key, 3600, json.dumps(model_list))
            
            return model_list
        except Exception as e:
            logger.error(f"Erro ao obter modelos: {str(e)}")
            raise
    
    def get_company_info(self, company_id: int = None) -> Dict[str, Any]:
        """
        Obtém informações da empresa.
        
        Args:
            company_id: ID da empresa (opcional)
        
        Returns:
            Informações da empresa
        """
        try:
            domain = [('id', '=', company_id)] if company_id else []
            fields = ['name', 'email', 'phone', 'website', 'vat', 'company_registry']
            
            companies = self.search_read('res.company', domain, fields)
            return companies[0] if companies else {}
        except Exception as e:
            logger.error(f"Erro ao obter informações da empresa: {str(e)}")
            raise
    
    def get_products(self, domain: List = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém lista de produtos.
        
        Args:
            domain: Domínio de busca (opcional)
            limit: Limite de registros (padrão: 100)
        
        Returns:
            Lista de produtos
        """
        try:
            domain = domain or [('sale_ok', '=', True)]
            fields = [
                'name', 'default_code', 'list_price', 'description_sale',
                'categ_id', 'qty_available', 'virtual_available'
            ]
            
            # Verificar se o módulo semantic_product_description está instalado
            semantic_fields = []
            module = self.search_read('ir.module.module', [('name', '=', 'semantic_product_description'), ('state', '=', 'installed')], ['name'])
            
            if module:
                # Adicionar campos semânticos
                semantic_fields = [
                    'semantic_description', 'main_features', 'use_cases',
                    'ai_sync_status', 'ai_sync_date'
                ]
                fields.extend(semantic_fields)
            
            products = self.search_read('product.product', domain, fields, limit=limit)
            
            # Processar categorias
            for product in products:
                if product.get('categ_id'):
                    product['categ_id'] = {
                        'id': product['categ_id'][0],
                        'name': product['categ_id'][1]
                    }
            
            return products
        except Exception as e:
            logger.error(f"Erro ao obter produtos: {str(e)}")
            raise
    
    def get_business_rules(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Obtém regras de negócio.
        
        Args:
            active_only: Retornar apenas regras ativas
        
        Returns:
            Lista de regras de negócio
        """
        try:
            # Verificar se o módulo business_rules2 está instalado
            module = self.search_read('ir.module.module', [('name', '=', 'business_rules2'), ('state', '=', 'installed')], ['name'])
            
            if not module:
                logger.warning("Módulo business_rules2 não está instalado")
                return []
            
            domain = [('active', '=', True)] if active_only else []
            fields = [
                'name', 'description', 'rule_type', 'priority', 
                'start_date', 'end_date', 'active'
            ]
            
            rules = self.search_read('business.rule', domain, fields)
            return rules
        except Exception as e:
            logger.error(f"Erro ao obter regras de negócio: {str(e)}")
            raise
    
    def get_company_services(self) -> Dict[str, Any]:
        """
        Obtém informações de serviços da empresa.
        
        Returns:
            Informações de serviços
        """
        try:
            # Verificar se o módulo company_services está instalado
            module = self.search_read('ir.module.module', [('name', '=', 'company_services'), ('state', '=', 'installed')], ['name'])
            
            if not module:
                logger.warning("Módulo company_services não está instalado")
                return {}
            
            # Obter configurações da empresa
            company_config = self.search_read('company.services.config', [], [
                'name', 'company_id', 'description', 'communication_style',
                'business_hours', 'active'
            ], limit=1)
            
            if not company_config:
                return {}
            
            config = company_config[0]
            
            # Obter serviços oferecidos
            services = self.search_read('company.service', [('config_id', '=', config['id'])], [
                'name', 'description', 'is_active'
            ])
            
            # Obter canais de comunicação
            channels = self.search_read('company.communication.channel', [('config_id', '=', config['id'])], [
                'name', 'channel_type', 'is_active'
            ])
            
            # Construir resposta
            result = {
                'company_name': config.get('name'),
                'description': config.get('description'),
                'communication_style': config.get('communication_style'),
                'business_hours': config.get('business_hours'),
                'services': services,
                'channels': channels
            }
            
            return result
        except Exception as e:
            logger.error(f"Erro ao obter serviços da empresa: {str(e)}")
            raise

# Criar cliente Odoo global
odoo_client = OdooClient(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

# Criar servidor MCP
app = mcp.FastMCP(
    title="MCP-Odoo",
    description="Servidor MCP para integração com Odoo ERP",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Endpoint raiz para verificação de saúde."""
    return {"status": "online", "service": "MCP-Odoo"}

@app.get("/health")
async def health_check():
    """Endpoint para verificação de saúde do serviço."""
    try:
        # Verificar conexão com Odoo
        odoo_client.get_company_info()
        
        # Verificar conexão com Redis
        redis_client.ping()
        
        return {
            "status": "healthy",
            "odoo_connection": "ok",
            "redis_connection": "ok"
        }
    except Exception as e:
        logger.error(f"Erro na verificação de saúde: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Recursos MCP

@app.resource("odoo://models")
def get_models() -> str:
    """
    Obtém a lista de modelos disponíveis no Odoo.
    
    Returns:
        JSON com a lista de modelos
    """
    models = odoo_client.get_models()
    return json.dumps(models, indent=2)

@app.resource("odoo://company-info")
def get_company_info(company_id: Optional[int] = None) -> str:
    """
    Obtém informações da empresa.
    
    Args:
        company_id: ID da empresa (opcional)
    
    Returns:
        JSON com informações da empresa
    """
    info = odoo_client.get_company_info(company_id)
    return json.dumps(info, indent=2)

@app.resource("odoo://products")
def get_products(query: Optional[str] = None, limit: int = 100) -> str:
    """
    Obtém lista de produtos.
    
    Args:
        query: Termo de busca (opcional)
        limit: Limite de registros (padrão: 100)
    
    Returns:
        JSON com lista de produtos
    """
    domain = []
    
    if query:
        domain = [
            '|', '|',
            ('name', 'ilike', query),
            ('default_code', 'ilike', query),
            ('description_sale', 'ilike', query)
        ]
    
    products = odoo_client.get_products(domain, limit)
    return json.dumps(products, indent=2)

@app.resource("odoo://business-rules")
def get_business_rules(active_only: bool = True) -> str:
    """
    Obtém regras de negócio.
    
    Args:
        active_only: Retornar apenas regras ativas
    
    Returns:
        JSON com lista de regras de negócio
    """
    rules = odoo_client.get_business_rules(active_only)
    return json.dumps(rules, indent=2)

@app.resource("odoo://company-services")
def get_company_services() -> str:
    """
    Obtém informações de serviços da empresa.
    
    Returns:
        JSON com informações de serviços
    """
    services = odoo_client.get_company_services()
    return json.dumps(services, indent=2)

@app.resource("odoo://product-details")
def get_product_details(product_id: int) -> str:
    """
    Obtém detalhes de um produto específico.
    
    Args:
        product_id: ID do produto
    
    Returns:
        JSON com detalhes do produto
    """
    domain = [('id', '=', product_id)]
    products = odoo_client.get_products(domain, 1)
    
    if not products:
        return json.dumps({"error": "Produto não encontrado"})
    
    return json.dumps(products[0], indent=2)

@app.resource("odoo://search-products")
def search_products(query: str, limit: int = 10) -> str:
    """
    Busca produtos por termo.
    
    Args:
        query: Termo de busca
        limit: Limite de resultados
    
    Returns:
        JSON com resultados da busca
    """
    domain = [
        '|', '|',
        ('name', 'ilike', query),
        ('default_code', 'ilike', query),
        ('description_sale', 'ilike', query)
    ]
    
    products = odoo_client.get_products(domain, limit)
    return json.dumps(products, indent=2)

if __name__ == "__main__":
    # Iniciar o servidor MCP
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Iniciando servidor MCP-Odoo em {host}:{port}")
    uvicorn.run(app, host=host, port=port)
