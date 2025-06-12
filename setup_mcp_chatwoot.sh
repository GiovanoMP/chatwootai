#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Configurando MCP-Chatwoot...${NC}"

# Verificar se o diretório mcp-chatwoot existe
if [ ! -d "./mcp-chatwoot" ]; then
    echo -e "${YELLOW}📁 Diretório mcp-chatwoot não encontrado. Criando...${NC}"
    mkdir -p ./mcp-chatwoot
else
    echo -e "${GREEN}✅ Diretório mcp-chatwoot já existe${NC}"
fi

# Verificar se já existe um Dockerfile
if [ ! -f "./mcp-chatwoot/Dockerfile" ]; then
    echo -e "${YELLOW}📄 Criando Dockerfile para mcp-chatwoot...${NC}"
    cat > ./mcp-chatwoot/Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de requisitos e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
    echo -e "${GREEN}✅ Dockerfile criado${NC}"
else
    echo -e "${GREEN}✅ Dockerfile já existe${NC}"
fi

# Criar arquivo requirements.txt se não existir
if [ ! -f "./mcp-chatwoot/requirements.txt" ]; then
    echo -e "${YELLOW}📄 Criando requirements.txt...${NC}"
    cat > ./mcp-chatwoot/requirements.txt << 'EOF'
fastapi==0.95.0
uvicorn==0.21.1
pydantic==1.10.7
pymongo==4.3.3
redis==4.5.4
httpx==0.24.0
python-dotenv==1.0.0
python-multipart==0.0.6
fastmcp==0.1.0
cryptography==40.0.2
EOF
    echo -e "${GREEN}✅ requirements.txt criado${NC}"
else
    echo -e "${GREEN}✅ requirements.txt já existe${NC}"
fi

# Criar arquivo main.py básico se não existir
if [ ! -f "./mcp-chatwoot/main.py" ]; then
    echo -e "${YELLOW}📄 Criando main.py básico...${NC}"
    cat > ./mcp-chatwoot/main.py << 'EOF'
import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import redis
import pymongo
import json
import hmac
import hashlib
import logging
from typing import Dict, List, Optional, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
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

# Configurações
CHATWOOT_BASE_URL = os.environ.get("CHATWOOT_BASE_URL", "http://chatwoot:3000")
CHATWOOT_ACCESS_TOKEN = os.environ.get("CHATWOOT_ACCESS_TOKEN", "")
CHATWOOT_HMAC_KEY = os.environ.get("CHATWOOT_HMAC_KEY", "")
CHATWOOT_INBOX_IDENTIFIER = os.environ.get("CHATWOOT_INBOX_IDENTIFIER", "")
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://mongodb:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "chatwoot_mcp")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
MCP_CREW_URL = os.environ.get("MCP_CREW_URL", "http://mcp-crew:8000")
MCP_CREW_TOKEN = os.environ.get("MCP_CREW_TOKEN", "")

# Conexão com MongoDB
try:
    mongo_client = pymongo.MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DB]
    logger.info(f"Conectado ao MongoDB: {MONGODB_URI}")
except Exception as e:
    logger.error(f"Erro ao conectar ao MongoDB: {e}")
    db = None

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
except Exception as e:
    logger.error(f"Erro ao conectar ao Redis: {e}")
    redis_client = None

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
    data: Dict[str, Any]

# Verificação de HMAC para webhooks do Chatwoot
async def verify_chatwoot_hmac(request: Request):
    if not CHATWOOT_HMAC_KEY:
        return True
    
    body = await request.body()
    signature = request.headers.get("X-Chatwoot-Signature", "")
    
    if not signature:
        raise HTTPException(status_code=401, detail="Assinatura não fornecida")
    
    computed_signature = hmac.new(
        CHATWOOT_HMAC_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(computed_signature, signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida")
    
    return True

# Rotas
@app.get("/health")
async def health_check():
    health = {
        "status": "ok",
        "mongodb": "ok" if db else "error",
        "redis": "ok" if redis_client else "error",
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
    
    # Processar apenas eventos de mensagem
    if webhook.event == "message_created" and webhook.data.get("message_type") == "incoming":
        account_id = webhook.data.get("account_id")
        conversation_id = webhook.data.get("conversation_id")
        content = webhook.data.get("content")
        
        if not account_id or not conversation_id or not content:
            logger.warning("Dados incompletos no webhook")
            return {"status": "error", "message": "Dados incompletos"}
        
        # Armazenar mensagem no Redis para processamento
        message_key = f"chatwoot:message:{account_id}:{conversation_id}"
        redis_client.set(message_key, json.dumps(webhook.data), ex=3600)
        
        # Adicionar à fila de processamento
        redis_client.lpush("chatwoot:message_queue", message_key)
        
        logger.info(f"Mensagem adicionada à fila: {message_key}")
        
        # Aqui você adicionaria a lógica para enviar a mensagem ao MCP-Crew
        # Por enquanto, apenas logamos que recebemos
        
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
    if not db:
        logger.warning("MongoDB não está disponível")
    
    if not redis_client:
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

# Ponto de entrada para execução direta
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
EOF
    echo -e "${GREEN}✅ main.py criado${NC}"
else
    echo -e "${GREEN}✅ main.py já existe${NC}"
fi

# Criar arquivo README.md se não existir
if [ ! -f "./mcp-chatwoot/README.md" ]; then
    echo -e "${YELLOW}📄 Criando README.md...${NC}"
    cat > ./mcp-chatwoot/README.md << 'EOF'
# MCP-Chatwoot

Plugin multi-tenant para integração segura com Chatwoot via API Channel.

## Funcionalidades

- Integração com Chatwoot via API e webhooks
- Suporte multi-tenant usando account_id como chave universal
- Armazenamento de configurações em MongoDB
- Cache e gerenciamento de estado com Redis
- Comunicação com MCP-Crew para processamento de IA

## Variáveis de Ambiente

```
CHATWOOT_BASE_URL=http://chatwoot:3000
CHATWOOT_ACCESS_TOKEN=seu_token_aqui
CHATWOOT_HMAC_KEY=sua_chave_hmac_aqui
CHATWOOT_INBOX_IDENTIFIER=identificador_inbox
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DB=chatwoot_mcp
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=sua_senha_redis
MCP_CREW_URL=http://mcp-crew:8000
MCP_CREW_TOKEN=seu_token_mcp_crew
```

## Endpoints

- `GET /health`: Verificação de saúde do serviço
- `POST /webhook`: Webhook para receber eventos do Chatwoot
- `GET /conversations/{account_id}/{conversation_id}`: Obter mensagens de uma conversa
- `POST /reply/{account_id}/{conversation_id}`: Responder a uma conversa

## Instalação

1. Configure as variáveis de ambiente
2. Execute `docker-compose up -d mcp-chatwoot`
3. Configure o webhook no Chatwoot apontando para `http://seu-servidor:8004/webhook`
EOF
    echo -e "${GREEN}✅ README.md criado${NC}"
else
    echo -e "${GREEN}✅ README.md já existe${NC}"
fi

# Verificar se o serviço está no docker-compose
if grep -q "mcp-chatwoot:" docker-compose.ai-stack.yml; then
    echo -e "${GREEN}✅ Serviço mcp-chatwoot já está configurado no docker-compose.ai-stack.yml${NC}"
else
    echo -e "${RED}❌ Serviço mcp-chatwoot não encontrado no docker-compose.ai-stack.yml${NC}"
    echo -e "${YELLOW}⚠️ Verifique se o serviço está configurado corretamente no arquivo docker-compose.ai-stack.yml${NC}"
fi

# Verificar variáveis de ambiente necessárias
echo -e "${YELLOW}📋 Verificando variáveis de ambiente necessárias...${NC}"
env_file=".env"

if [ -f "$env_file" ]; then
    missing_vars=()
    
    # Lista de variáveis necessárias
    required_vars=(
        "CHATWOOT_ACCESS_TOKEN"
        "CHATWOOT_HMAC_KEY"
        "CHATWOOT_INBOX_IDENTIFIER"
        "REDIS_PASSWORD"
        "MCP_CREW_TOKEN"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ Todas as variáveis de ambiente necessárias estão configuradas${NC}"
    else
        echo -e "${RED}❌ As seguintes variáveis de ambiente estão faltando no arquivo .env:${NC}"
        for var in "${missing_vars[@]}"; do
            echo -e "${YELLOW}   - $var${NC}"
        done
        echo -e "${YELLOW}⚠️ Adicione estas variáveis ao arquivo .env antes de iniciar o serviço${NC}"
    fi
else
    echo -e "${RED}❌ Arquivo .env não encontrado${NC}"
    echo -e "${YELLOW}⚠️ Crie um arquivo .env com as variáveis necessárias${NC}"
fi

echo -e "${BLUE}🚀 Configuração do MCP-Chatwoot concluída${NC}"
echo -e "${YELLOW}📋 Para iniciar o serviço, execute:${NC}"
echo -e "${GREEN}   docker-compose -f docker-compose.ai-stack.yml up -d mcp-chatwoot${NC}"
