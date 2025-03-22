"""
Servidor webhook para receber eventos do Chatwoot.

Este servidor recebe notificações do Chatwoot quando eventos ocorrem
(como novas mensagens) e os processa usando o sistema de crews.
"""

import os
import sys
import logging
import json
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from datetime import datetime

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importa o sistema de debug_logger
from src.utils.debug_logger import DebugLogger, get_logger, log_function_call, TRACE

# Configura o logger com nível mais detalhado para depuração
logger = get_logger('webhook_server', level=logging.DEBUG)

# Carrega variáveis de ambiente
load_dotenv()

# Importa o gerenciador de instâncias
from src.api.multi_instance_handler import MultiInstanceManager

# Cria uma instância simples do gerenciador
instance_manager = MultiInstanceManager()

# Importa os componentes necessários
from src.api.chatwoot.client import ChatwootWebhookHandler, ChatwootClient
from src.core.hub import HubCrew  # Importa HubCrew do core.hub em vez de crews.hub_crew
from src.core.crew_registry import CrewRegistry

# Cria a aplicação FastAPI
app = FastAPI(title="Chatwoot Webhook Server", description="Servidor para receber webhooks do Chatwoot")

# Adiciona middleware CORS para permitir requisições de diferentes origens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique as origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis globais para armazenar as instâncias das crews
crew_registry = None
webhook_handler = None

def get_webhook_handler():
    """
    Obtém o handler de webhook.
    
    Returns:
        ChatwootWebhookHandler: Handler de webhook
    """
    global webhook_handler
    if webhook_handler is None:
        initialize_crews()
    return webhook_handler

def initialize_crews():
    """
    Inicializa as crews e o handler de webhook.
    """
    global crew_registry, webhook_handler
    
    # Obtém as variáveis de ambiente
    chatwoot_base_url = os.getenv('CHATWOOT_BASE_URL')
    chatwoot_api_key = os.getenv('CHATWOOT_API_KEY')
    chatwoot_account_id = int(os.getenv('CHATWOOT_ACCOUNT_ID', '1'))
    
    if not all([chatwoot_base_url, chatwoot_api_key]):
        raise ValueError("Variáveis de ambiente CHATWOOT_BASE_URL e CHATWOOT_API_KEY devem estar definidas")
    
    # Inicializa o cliente do Chatwoot
    chatwoot_client = ChatwootClient(
        base_url=chatwoot_base_url,
        api_key=chatwoot_api_key
    )
    
    # Inicializa o registro de crews
    crew_registry = CrewRegistry()
    
    # Inicializa os componentes necessários para o HubCrew
    from redis import Redis
    from src.core.memory import MemorySystem
    from src.tools.vector_tools import QdrantVectorSearchTool
    from src.tools.database_tools import PGSearchTool
    from src.tools.cache_tools import CacheTool
    from src.core.cache.agent_cache import RedisAgentCache
    
    # Cria instâncias dos componentes necessários
    memory_system = MemorySystem()
    
    # Inicializa ferramentas (usando valores padrão para desenvolvimento)
    vector_tool = QdrantVectorSearchTool(
        qdrant_url=os.getenv('QDRANT_URL', 'http://localhost:6333'),
        collection_name=os.getenv('QDRANT_COLLECTION', 'chatwoot_vectors')
    )
    
    db_tool = PGSearchTool(
        db_uri=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/chatwoot_ai'),
        table_name=['customers', 'products']
    )
    
    # Configura o Redis usando o endereço IP direto do contêiner
    # Usar diretamente o IP, ignorando a variável de ambiente para garantir que funcione
    redis_url = 'redis://172.24.0.5:6379/0'
    logger.info(f"Conectando ao Redis usando URL: {redis_url}")
    try:
        redis_client = Redis.from_url(redis_url)
        redis_info = redis_client.info()
        logger.info(f"Conexão Redis estabelecida com sucesso: {redis_info.get('redis_version', 'desconhecido')}")
    except Exception as e:
        logger.error(f"Erro ao conectar ao Redis: {e}")
        # Tentar com o host local como fallback
        redis_url = 'redis://localhost:6379/0'
        logger.info(f"Tentando conectar ao Redis com fallback: {redis_url}")
        try:
            redis_client = Redis.from_url(redis_url)
            redis_info = redis_client.info()
            logger.info(f"Conexão Redis fallback estabelecida com sucesso")
        except Exception as e2:
            logger.error(f"Erro ao conectar ao Redis fallback: {e2}")
            # Última tentativa - criar um cliente Redis sem parametros
            redis_client = Redis()
    
    cache_tool = CacheTool(
        redis_client=redis_client,
        prefix='chatwoot_ai:'
    )
    
    # Inicializa o cache de agentes
    agent_cache = RedisAgentCache(
        redis_client=redis_client,
        prefix='agent_cache:'
    )
    
    # Inicializa o DataServiceHub para obter o data_proxy_agent
    from src.core.data_service_hub import DataServiceHub
    data_service_hub = DataServiceHub()
    data_proxy_agent = data_service_hub.get_data_proxy_agent()
    
    # Inicializa a hub crew com os parâmetros corretos
    hub_crew = HubCrew(
        memory_system=memory_system,
        data_proxy_agent=data_proxy_agent,  # Adicionado data_proxy_agent
        vector_tool=vector_tool,
        db_tool=db_tool,
        cache_tool=cache_tool,
        agent_cache=agent_cache,
        data_service_hub=data_service_hub  # Adicionado data_service_hub
    )
    
    # Registra as crews
    crew_registry.register_crew("hub", hub_crew)
    
    # Inicializa o handler de webhook com acesso ao registro de crews
    webhook_handler = ChatwootWebhookHandler(hub_crew, crew_registry)
    
    logger.info("Crews e handler de webhook inicializados com sucesso")

@app.on_event("startup")
async def startup_event():
    """
    Evento executado na inicialização do servidor.
    """
    logger.info("Iniciando servidor webhook...")
    initialize_crews()
    
    # Obtém informações do ambiente para exibir a URL do webhook
    webhook_domain = os.getenv('WEBHOOK_DOMAIN', 'localhost')
    webhook_port = int(os.getenv('WEBHOOK_PORT', '8001'))
    use_https = os.getenv('WEBHOOK_USE_HTTPS', 'false').lower() == 'true'
    
    protocol = "https" if use_https else "http"
    port_str = f":{webhook_port}" if (not use_https and webhook_port != 80) or (use_https and webhook_port != 443) else ""
    
    webhook_url = f"{protocol}://{webhook_domain}{port_str}/webhook"
    
    logger.info("Servidor webhook iniciado com sucesso")
    logger.info(f"URL do webhook: {webhook_url}")
    logger.info("Configure esta URL no painel de administração do Chatwoot")

@app.get("/")
async def root():
    """
    Rota raiz para verificar se o servidor está funcionando.
    """
    # Obtém informações do ambiente para exibir a URL do webhook
    webhook_domain = os.getenv('WEBHOOK_DOMAIN', 'localhost')
    webhook_port = int(os.getenv('WEBHOOK_PORT', '8001'))
    use_https = os.getenv('WEBHOOK_USE_HTTPS', 'false').lower() == 'true'
    
    protocol = "https" if use_https else "http"
    port_str = f":{webhook_port}" if (not use_https and webhook_port != 80) or (use_https and webhook_port != 443) else ""
    
    webhook_url = f"{protocol}://{webhook_domain}{port_str}/webhook"
    
    return {
        "status": "online", 
        "message": "Chatwoot Webhook Server está funcionando",
        "webhook_url": webhook_url
    }
    
@app.get("/health")
async def health_check():
    """
    Endpoint de verificação de saúde (health check) para monitoramento.
    
    Este endpoint é usado para verificar se o servidor webhook está funcionando
    corretamente. É útil para monitoramento e verificações automáticas de status.
    
    Returns:
        Dict: Status do servidor e timestamp atual
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "webhook_server",
        "version": "1.0.0",
        "instances": len(instance_manager.instances) if hasattr(instance_manager, 'instances') else 1
    }

@app.post("/webhook")
@log_function_call(level=TRACE)
async def webhook(request: Request, handler: ChatwootWebhookHandler = Depends(get_webhook_handler)):
    """
    Endpoint para receber webhooks do Chatwoot.
    
    Este endpoint é o ponto de entrada para todos os eventos enviados pelo Chatwoot.
    Quando o Chatwoot detecta uma nova mensagem ou mudança de status em uma conversa,
    ele envia uma notificação para este endpoint.
    
    O fluxo de processamento é:
    1. Verificar o token de autenticação
    2. Receber os dados JSON do webhook
    3. Identificar o tipo de evento (message_created, conversation_created, etc.)
    4. Encaminhar para o handler apropriado
    5. Processar o evento e retornar uma resposta
    
    Args:
        request: Requisição HTTP contendo os dados do webhook
        handler: Handler de webhook que processa os diferentes tipos de eventos
        
    Returns:
        Resposta do processamento do webhook
        
    Raises:
        HTTPException: Se ocorrer um erro durante o processamento ou autenticação falhar
    """
    try:
        # Verificar o token de autenticação
        auth_header = request.headers.get('Authorization')
        expected_token = os.getenv('WEBHOOK_AUTH_TOKEN')
        
        # Registrar informações detalhadas da requisição para debug
        logger.info(f"Requisição recebida de {request.client.host}")
        logger.debug(f"Headers recebidos: {dict(request.headers)}")
        
        # Verificar se estamos em modo de desenvolvimento
        dev_mode = os.getenv('ENVIRONMENT', 'development').lower() == 'development'
        
        # Se o token estiver configurado, verificar a autenticação
        if expected_token and not dev_mode:
            is_authenticated = False
            
            # Verificar se o token está no cabeçalho de autorização
            if auth_header:
                # Caso 1: Formato "Bearer token"
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ", 1)[1]
                    if token == expected_token:
                        is_authenticated = True
                # Caso 2: Apenas o token sem o prefixo "Bearer"
                elif auth_header == expected_token:
                    is_authenticated = True
            
            # Caso 3: Verificar se o token está nos parâmetros da consulta
            if not is_authenticated:
                query_token = request.query_params.get('token')
                if query_token and query_token == expected_token:
                    is_authenticated = True
            
            # Se nenhuma forma de autenticação for bem-sucedida, rejeitar a requisição
            if not is_authenticated:
                logger.warning(f"Tentativa de acesso não autorizado ao webhook. IP: {request.client.host}")
                logger.debug(f"Cabeçalho de autorização recebido: {auth_header}")
                raise HTTPException(
                    status_code=401, 
                    detail="Não autorizado. Token de autenticação inválido ou ausente."
                )
            
            logger.debug("Autenticação do webhook bem-sucedida")
        else:
            if dev_mode:
                logger.info("Modo de desenvolvimento: Autenticação desativada")
            else:
                logger.warning("Webhook está sendo executado sem autenticação. Recomenda-se configurar WEBHOOK_AUTH_TOKEN.")
        
        # Obtém os dados do webhook (formato JSON)
        data = await request.json()
        
        # Registra o recebimento do webhook no log com detalhes
        event_type = data.get('event')
        timestamp_received = datetime.now().isoformat()
        logger.info(f"Webhook recebido: {event_type} de {request.client.host} em {timestamp_received}")
        
        # Log detalhado do payload para depuração
        try:
            # Usa a função log_dict do DebugLogger para formatar o JSON
            logger.log_dict(logging.DEBUG, "Payload do webhook", data)
        except Exception as log_err:
            logger.warning(f"Erro ao logar payload completo: {log_err}")
        
        # Exemplo de estrutura de dados para evento 'message_created':
        # {
        #   "event": "message_created",
        #   "account": { "id": 1, "name": "Conta de Exemplo" },
        #   "conversation": { "id": 123, ... },
        #   "message": { 
        #     "id": 456, 
        #     "content": "Olá, preciso de ajuda",
        #     "message_type": 0,  # 0 = mensagem recebida
        #     ... 
        #   }
        # }
        
        # Marca o início do processamento para medir performance
        start_time = datetime.now()
        
        # Processa o webhook usando o handler apropriado
        # O handler.handle_webhook irá direcionar para o método específico
        # com base no tipo de evento (ex: _handle_message_created)
        response = handler.handle_webhook(data)
        
        # Calcula e registra o tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Tempo de processamento do webhook {event_type}: {processing_time:.3f}s")
        
        # Adiciona o tempo de processamento à resposta
        if isinstance(response, dict):
            response["processing_time"] = f"{processing_time:.3f}s"
        
        return response
    
    except HTTPException:
        # Re-lança exceções HTTP para manter o código de status correto
        raise
    
    except json.JSONDecodeError as e:
        # Log detalhado para erro de JSON inválido
        logger.error(f"Erro de JSON inválido no webhook: {e}")
        body = await request.body()
        logger.error(f"Corpo da requisição: {body.decode('utf-8', errors='replace')}")
        raise HTTPException(status_code=400, detail=f"JSON inválido: {str(e)}")
    
    except Exception as e:
        # Registra o erro de forma detalhada usando o logger avançado
        logger.error(f"Erro ao processar webhook: {type(e).__name__}: {str(e)}")
        logger.log_exception(e, context="processamento do webhook")
        # Retorna um erro HTTP 500 com a mensagem de erro
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """
    Função principal para iniciar o servidor.
    """
    # Obtém a porta do ambiente ou usa 8001 como padrão
    port = int(os.getenv('WEBHOOK_PORT', '8001'))
    
    logger.info(f"Iniciando servidor webhook na porta {port}")
    
    # Inicia o servidor
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
