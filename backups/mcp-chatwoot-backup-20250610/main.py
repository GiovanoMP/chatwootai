import os
import time
import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import httpx
import redis
import json
import hmac
import hashlib
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from fastmcp.server.server import FastMCP
from src.common.config import MCP_TRANSPORT, MCP_PORT, MCP_HOST
from src.tools import tools
from src.tools.registry import format_tools_for_api

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcp_chatwoot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mcp-chatwoot")

# Inicializar FastAPI
app = FastAPI(title="MCP-Chatwoot", description="MCP para integração com Chatwoot")

# Adicionar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar servidor MCP
try:
    # Configurar transporte SSE para o servidor MCP
    from mcp.server.sse import SseServerTransport
    sse_transport = SseServerTransport("/messages/")
    logger.info("Transporte SSE configurado com endpoint de mensagens em /messages/")
    
    # Inicializar servidor MCP com o transporte SSE
    mcp_server = FastMCP(
        name="MCP-Chatwoot",
        description="Servidor MCP para integração com Chatwoot",
        transport=sse_transport,  # Usar o transporte SSE em vez de MCP_TRANSPORT
        tools=tools
    )
    
    logger.info(f"Servidor MCP inicializado com transporte SSE")
    logger.info(f"Ferramentas MCP disponíveis: {len(tools)}")
    for tool in tools:
        logger.info(f"  - {tool.name}")
except Exception as e:
    logger.error(f"Erro ao inicializar servidor MCP: {e}")
    raise


# Configurações - usando as variáveis já carregadas do config.py
from src.common.config import (
    CHATWOOT_BASE_URL, CHATWOOT_ACCESS_TOKEN, CHATWOOT_HMAC_KEY, CHATWOOT_INBOX_IDENTIFIER,
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
    MCP_CREW_URL, MCP_CREW_TOKEN
)

# Conexão com Redis
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    redis_client.ping()
    logger.info(f"Conectado ao Redis: {REDIS_HOST}:{REDIS_PORT}")
    redis_available = True
except Exception as e:
    logger.error(f"Erro ao conectar ao Redis: {e}")
    redis_client = None
    redis_available = False

# Cliente HTTP para comunicação com Chatwoot e MCP-Crew
http_client = httpx.AsyncClient(timeout=30.0)

# Modelos de dados
class ChatwootMessage(BaseModel):
    account_id: int
    message_type: str
    content: Optional[str] = None
    conversation_id: int
    inbox_id: int
    user: Optional[Dict[str, Any]] = None
    contact: Optional[Dict[str, Any]] = None

class ChatwootWebhook(BaseModel):
    event: str
    data: Optional[Dict[str, Any]] = None
    conversation: Optional[Dict[str, Any]] = None
    message: Optional[Dict[str, Any]] = None
    account: Optional[Dict[str, Any]] = None
    inbox: Optional[Dict[str, Any]] = None
    contact: Optional[Dict[str, Any]] = None
    changed_attributes: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        extra = "allow"  # Permite campos adicionais no JSON

# Verificação de HMAC para webhooks do Chatwoot
async def verify_chatwoot_hmac(request: Request):
    # Modo de depuração - desabilitar verificação HMAC temporariamente durante testes
    # Remova esta linha em produção
    DEBUG_DISABLE_HMAC = True
    
    if DEBUG_DISABLE_HMAC:
        logger.warning("AVISO: Verificação HMAC desabilitada para testes!")
        return True
    
    if not CHATWOOT_HMAC_KEY:
        logger.warning("CHATWOOT_HMAC_KEY não configurada, pulando verificação")
        return True
    
    body = await request.body()
    signature = request.headers.get("X-Chatwoot-Signature", "")
    
    logger.info(f"Headers recebidos: {request.headers}")
    
    if not signature:
        logger.error("Assinatura X-Chatwoot-Signature não fornecida nos headers")
        raise HTTPException(status_code=401, detail="Assinatura não fornecida")
    
    computed_signature = hmac.new(
        CHATWOOT_HMAC_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    logger.info(f"Assinatura recebida: {signature}")
    logger.info(f"Assinatura calculada: {computed_signature}")
    
    if not hmac.compare_digest(computed_signature, signature):
        logger.error("Assinatura HMAC inválida")
        raise HTTPException(status_code=401, detail="Assinatura inválida")
    
    logger.info("Verificação HMAC bem-sucedida")
    return True

# Rotas
@app.get("/health")
async def health_check():
    health = {
        "status": "ok",
        "redis": "ok" if redis_client is not None else "error",
    }
    
    # Verificar se podemos nos comunicar com o Chatwoot
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{CHATWOOT_BASE_URL}/api/v1/health_check")
            health["chatwoot"] = "ok" if response.status_code == 200 else "error"
    except Exception as e:
        health["chatwoot"] = f"error: {str(e)}"
    
    # Status geral
    if "error" in health.values():
        return {"status": "unhealthy", "details": health}
    
    return health

@app.post("/webhook", dependencies=[Depends(verify_chatwoot_hmac)])
async def chatwoot_webhook(webhook: ChatwootWebhook):
    logger.info(f"Webhook recebido: {webhook.event}")
    
    # Log detalhado do payload completo para depuração
    try:
        logger.info(f"Payload completo: {webhook.dict()}")
    except Exception as e:
        logger.error(f"Erro ao registrar payload completo: {e}")
    
    # Processar apenas eventos de mensagem
    if webhook.event == "message_created":
        # Verificar se é uma mensagem de entrada (do cliente)
        message_type = None
        content = None
        account_id = None
        conversation_id = None
        inbox_id = None
        source_id = None
        
        try:
            
            # Extrair informações do novo formato de webhook
            if webhook.message:
                message_type = webhook.message.get("message_type")
                content = webhook.message.get("content")
                source_id = webhook.message.get("source_id")
            
            # Extrair do objeto account
            if webhook.account:
                account_id = webhook.account.get("id")
            
            # Extrair do objeto conversation
            if webhook.conversation:
                conversation_id = webhook.conversation.get("display_id")
            
            # Extrair do objeto inbox
            if webhook.inbox:
                inbox_id = webhook.inbox.get("id")
            
            # Formato alternativo (campos no nível raiz)
            if not message_type and hasattr(webhook, "message_type"):
                message_type = getattr(webhook, "message_type")
            
            if not content and hasattr(webhook, "content"):
                content = getattr(webhook, "content")
            
            if not account_id and hasattr(webhook, "account_id"):
                account_id = getattr(webhook, "account_id")
            
            if not conversation_id and hasattr(webhook, "conversation_id"):
                conversation_id = getattr(webhook, "conversation_id")
            
            if not inbox_id and hasattr(webhook, "inbox_id"):
                inbox_id = getattr(webhook, "inbox_id")
            
            if not source_id and hasattr(webhook, "source_id"):
                source_id = getattr(webhook, "source_id")
            
            # Registrar informações extraídas
            logger.info(f"Mensagem recebida: event={webhook.event}, message_type={message_type}")
            logger.info(f"Conteúdo: {content}")
            logger.info(f"ID da conta: {account_id}")
            logger.info(f"ID da conversa: {conversation_id}")
            logger.info(f"ID da caixa de entrada: {inbox_id}")
            logger.info(f"ID da fonte: {source_id}")
            
            # Verificar se temos as informações mínimas necessárias
            if not account_id or not conversation_id or not content:
                logger.warning("Dados incompletos no webhook")
                return {"status": "error", "message": "Dados incompletos"}
            
            # Processar apenas mensagens de entrada
            if message_type != "incoming":
                logger.info(f"Ignorando mensagem não-incoming: {message_type}")
                return {"status": "ok", "message": "Mensagem não-incoming ignorada"}
            
            # Obter informações sobre o tipo de caixa de entrada (WhatsApp, Facebook, etc.)
            inbox_info = {}
            channel_type = ""
            try:
                if inbox_id:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(
                            f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/inboxes/{inbox_id}",
                            headers={"api_access_token": CHATWOOT_ACCESS_TOKEN}
                        )
                        if response.status_code == 200:
                            inbox_info = response.json()
                            channel_type = inbox_info.get('channel_type', '')
                            logger.info(f"Tipo de caixa de entrada: {channel_type}")
            except Exception as e:
                logger.error(f"Erro ao obter informações da caixa de entrada: {e}")
            
            # Armazenar mensagem no Redis para processamento (se disponível)
            message_key = f"chatwoot:message:{account_id}:{conversation_id}"
            
            # Preparar dados para armazenamento
            message_data = webhook.dict()
            
            if redis_available and redis_client is not None:
                try:
                    redis_client.set(message_key, json.dumps(message_data), ex=3600)
                    # Adicionar à fila de processamento
                    redis_client.lpush("chatwoot:message_queue", message_key)
                    logger.info(f"Mensagem armazenada no Redis: {message_key}")
                except Exception as e:
                    logger.error(f"Erro ao armazenar mensagem no Redis: {e}")
            else:
                logger.warning("Redis não disponível, pulando armazenamento da mensagem")
            
            # Determinar o tipo de fonte baseado nas informações da caixa de entrada
            source = "chatwoot"
            if channel_type:
                source = f"chatwoot-{channel_type}"
            
            # Enviar mensagem para o MCP-Crew
            crew_url = f"{MCP_CREW_URL}/process_message"
            crew_headers = {"Authorization": f"Bearer {MCP_CREW_TOKEN}"}
            
            crew_payload = {
                "account_id": account_id,
                "conversation_id": conversation_id,
                "message": content,
                "source": source,
                "inbox_id": inbox_id,
                "source_id": source_id,
                "channel_type": channel_type,
                "metadata": {
                    "webhook_data": message_data,
                    "inbox_info": inbox_info
                }
            }
            
            # Envio assíncrono para o MCP-Crew
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(crew_url, json=crew_payload, headers=crew_headers)
                if response.status_code == 200:
                    logger.info(f"Mensagem enviada com sucesso para o MCP-Crew: {message_key}")
                else:
                    logger.error(f"Erro ao enviar mensagem para MCP-Crew: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Exceção ao enviar mensagem para MCP-Crew: {str(e)}")
            # Mesmo com erro, mantemos a mensagem na fila para processamento posterior
        
        return {"status": "success", "message": "Mensagem recebida e enfileirada"}
    
    return {"status": "ignored", "message": "Evento não processado"}

@app.get("/conversations/{account_id}/{conversation_id}")
async def get_conversation(account_id: int, conversation_id: int):
    if not CHATWOOT_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="Token de acesso do Chatwoot não configurado")
    
    try:
        url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        headers = {"api_access_token": CHATWOOT_ACCESS_TOKEN}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
    except Exception as e:
        logger.error(f"Erro ao obter conversa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter conversa: {str(e)}")

@app.post("/reply/{account_id}/{conversation_id}")
async def reply_to_conversation(account_id: int, conversation_id: int, content: str):
    if not CHATWOOT_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="Token de acesso do Chatwoot não configurado")
    
    try:
        url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        headers = {"api_access_token": CHATWOOT_ACCESS_TOKEN}
        data = {
            "content": content,
            "message_type": "outgoing"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return response.json()
    except Exception as e:
        logger.error(f"Erro ao responder conversa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao responder conversa: {str(e)}")

# Inicialização
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando MCP-Chatwoot...")
    
    # Verificar conexões
    if redis_client is None:
        logger.warning("Redis não está disponível")
    
    # Verificar configurações do Chatwoot
    if not CHATWOOT_ACCESS_TOKEN:
        logger.warning("Token de acesso do Chatwoot não configurado")
    
    if not CHATWOOT_HMAC_KEY:
        logger.warning("Chave HMAC do Chatwoot não configurada")
    
    logger.info("MCP-Chatwoot iniciado com sucesso")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Encerrando MCP-Chatwoot...")
    await http_client.aclose()
    logger.info("MCP-Chatwoot encerrado")

# Endpoint para listar ferramentas disponíveis
@app.get("/tools")
async def get_tools():
    """Retorna a lista de ferramentas disponíveis no servidor MCP-Chatwoot."""
    try:
        tools_info = format_tools_for_api(tools)
        logger.info(f"Endpoint /tools chamado, retornando {len(tools_info)} ferramentas")
        return {"tools": tools_info}
    except Exception as e:
        logger.error(f"Erro ao obter lista de ferramentas: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao obter lista de ferramentas: {str(e)}"})

# Endpoint SSE para MCP
@app.get("/sse")
async def sse_endpoint(request: Request):
    """
    Endpoint SSE (Server-Sent Events) para comunicação com o MCP.
    Este endpoint é usado pelo MCPAdapt para descobrir e utilizar as ferramentas MCP.
    """
    logger.info("Conexão SSE iniciada")
    
    try:
        # Usar o SseServerTransport para gerenciar a conexão SSE
        session_id = f"{hash(request)}_{int(time.time())}"
        logger.info(f"Criando sessão SSE com ID: {session_id}")
        
        # Enviar evento de endpoint com URL de mensagens
        message_url = f"/messages/?session_id={session_id}"
        logger.info(f"URL de mensagens: {message_url}")
        
        # Criar resposta SSE no formato esperado pelo MCPAdapt
        async def event_stream():
            # O MCPAdapt espera apenas a URL como valor do evento endpoint
            # Não é necessário enviar um objeto JSON-RPC completo
            # A URL deve ser absoluta, incluindo o host
            full_url = f"http://{request.headers.get('host')}{message_url}"
            yield f"event: endpoint\ndata: {full_url}\n\n"
            # Adicionar ping para manter conexão viva
            while True:
                await asyncio.sleep(30)  # Enviar ping a cada 30 segundos
                yield f": ping - {datetime.now(timezone.utc)}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error(f"Erro no endpoint SSE: {e}")
        raise

@app.post("/messages/")
async def handle_messages(request: Request):
    """
    Endpoint para receber mensagens do cliente MCP após a conexão SSE.
    Este endpoint recebe solicitações JSON-RPC do MCPAdapt e retorna respostas JSON-RPC.
    """
    try:
        session_id = request.query_params.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id parameter")
            
        logger.info(f"Recebendo mensagem para sessão: {session_id}")
        
        # Processar a mensagem recebida
        body = await request.json()
        logger.info(f"Mensagem recebida: {body}")
        
        # Verificar se a mensagem é uma solicitação JSON-RPC válida
        if not isinstance(body, dict) or "jsonrpc" not in body or "method" not in body:
            error_response = {
                "jsonrpc": "2.0",
                "id": body.get("id", None),
                "error": {
                    "code": -32600,
                    "message": "Invalid JSON-RPC request"
                }
            }
            logger.error(f"Solicitação JSON-RPC inválida: {body}")
            return error_response
        
        # Tratamento especial para a mensagem de inicialização
        if body.get("method") == "initialize":
            logger.info("Recebida mensagem de inicialização do MCPAdapt")
            # Construir resposta de inicialização de acordo com o protocolo MCP
            initialize_response = {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "serverInfo": {
                        "name": "MCP-Chatwoot",
                        "version": "1.0.0",
                        "protocolVersion": "2025-03-26"
                    },
                    "capabilities": {
                        "tools": True,
                        "resources": False,
                        "prompts": False
                    }
                }
            }
            logger.info(f"Enviando resposta de inicialização: {initialize_response}")
            return initialize_response
        
        # Processar outras mensagens com o servidor MCP
        try:
            response = await mcp_server.handle_jsonrpc(body)
            logger.info(f"Resposta do MCP: {response}")
            return response
        except Exception as e:
            # Garantir que erros sejam retornados no formato JSON-RPC
            error_response = {
                "jsonrpc": "2.0",
                "id": body.get("id", None),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            logger.error(f"Erro ao processar solicitação JSON-RPC: {e}")
            return error_response
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        # Retornar erro no formato JSON-RPC mesmo para erros não relacionados ao protocolo
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        }

# Endpoint REST para MCP (compatibilidade com versões anteriores)
@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Dict[str, Any]:
    """
    Endpoint REST para comunicação com o MCP.
    Este endpoint é usado para compatibilidade com sistemas que não suportam SSE.
    """
    body = await request.json()
    response = await mcp_server.handle_request(body)
    return response

# Ponto de entrada para execução direta
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=MCP_PORT, reload=True)
