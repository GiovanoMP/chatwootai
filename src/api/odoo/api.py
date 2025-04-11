"""
API REST para integração com o módulo Odoo semantic_product_description.

Este módulo implementa endpoints REST para receber webhooks do módulo Odoo,
permitindo a sincronização de produtos e a geração de descrições semânticas.

Fluxo de trabalho:
1. Módulo Odoo envia webhook com metadados do produto
2. API valida o token de autenticação
3. API enfileira a tarefa para processamento assíncrono
4. Worker processa a tarefa e atualiza o Qdrant
5. API retorna confirmação de recebimento

Autor: Augment Agent
Data: 26/03/2025
"""

import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importações internas
from .schemas import TaskType, TaskStatus, WebhookRequest, WebhookResponse, TaskStatusResponse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Definição do lifespan da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código executado na inicialização
    logger.info("Iniciando API REST para integração com Odoo")

    # TODO: Inicializar conexão com RabbitMQ
    # TODO: Inicializar DomainManager

    logger.info("API REST para integração com Odoo iniciada com sucesso")

    yield

    # Código executado no encerramento
    logger.info("Encerrando API REST para integração com Odoo")

    # TODO: Fechar conexão com RabbitMQ

    logger.info("API REST para integração com Odoo encerrada com sucesso")

# Criar aplicação FastAPI com lifespan
app = FastAPI(
    title="ChatwootAI Odoo Integration API",
    description="API para integração com o módulo Odoo semantic_product_description",
    version="1.0.0",
    lifespan=lifespan
)

# Adicionar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar modelos de dados de schemas.py

# Funções auxiliares
def verify_token(authorization: str = Header(...)) -> bool:
    """
    Verifica se o token de autorização é válido.

    Args:
        authorization: Token de autorização no formato "Bearer {token}"

    Returns:
        bool: True se o token for válido, False caso contrário

    Raises:
        HTTPException: Se o token for inválido ou não fornecido
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorização inválido. Formato esperado: 'Bearer {token}'"
        )

    token = authorization.replace("Bearer ", "")

    # TODO: Implementar verificação real do token usando o DomainManager
    # Por enquanto, aceitar qualquer token não vazio
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorização não fornecido"
        )

    return True

def get_account_id_from_token(authorization: str) -> str:
    """
    Extrai o account_id do token de autorização.

    Args:
        authorization: Token de autorização no formato "Bearer {token}"

    Returns:
        str: account_id extraído do token
    """
    # TODO: Implementar extração real do account_id do token
    # Por enquanto, retornar um account_id fixo
    return "account_2"

def enqueue_task(task_type: TaskType, data: Dict[str, Any]) -> str:
    """
    Enfileira uma tarefa para processamento assíncrono.

    Args:
        task_type: Tipo da tarefa (ex: TaskType.SYNC_PRODUCT, TaskType.GENERATE_DESCRIPTION)
        data: Dados da tarefa

    Returns:
        str: ID da tarefa enfileirada
    """
    # TODO: Implementar enfileiramento real com RabbitMQ
    # Por enquanto, apenas logar a tarefa
    request_id = f"{task_type}_{int(time.time())}"
    logger.info(f"Enfileirando tarefa {request_id}: {task_type} - {json.dumps(data)}")
    return request_id

# Endpoints
@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está funcionando."""
    return {"message": "ChatwootAI Odoo Integration API"}

@app.post("/api/v1/webhook/product/sync", response_model=WebhookResponse)
async def sync_product(
    request: WebhookRequest,
    authorized: bool = Depends(verify_token)
):
    """
    Endpoint para sincronização de produtos.

    Recebe metadados de um produto do Odoo e enfileira uma tarefa para
    sincronização com o Qdrant.

    Args:
        request: Dados do webhook
        authorized: Resultado da verificação do token

    Returns:
        WebhookResponse: Resposta do webhook
    """
    try:
        # Extrair metadados
        metadata = request.metadata
        params = request.params

        # Verificar se os parâmetros necessários estão presentes
        if "product_id" not in params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parâmetro obrigatório 'product_id' não fornecido"
            )

        # Extrair account_id do token
        account_id = metadata.get("account_id") or get_account_id_from_token(
            Header(...).get("Authorization", "")
        )

        # Enfileirar tarefa para processamento assíncrono
        task_data = {
            "account_id": account_id,
            "product_id": params["product_id"],
            "metadata": metadata,
            "params": params
        }
        request_id = enqueue_task("sync_product", task_data)

        # Retornar resposta
        return WebhookResponse(
            success=True,
            message="Produto enfileirado para sincronização",
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Erro ao processar webhook de sincronização de produto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@app.post("/api/v1/webhook/product/description", response_model=WebhookResponse)
async def generate_description(
    request: WebhookRequest,
    authorized: bool = Depends(verify_token)
):
    """
    Endpoint para geração de descrição de produto.

    Recebe metadados de um produto do Odoo e enfileira uma tarefa para
    geração de descrição semântica.

    Args:
        request: Dados do webhook
        authorized: Resultado da verificação do token

    Returns:
        WebhookResponse: Resposta do webhook
    """
    try:
        # Extrair metadados
        metadata = request.metadata
        params = request.params

        # Verificar se os parâmetros necessários estão presentes
        if "product_id" not in params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parâmetro obrigatório 'product_id' não fornecido"
            )

        # Extrair account_id do token
        account_id = metadata.get("account_id") or get_account_id_from_token(
            Header(...).get("Authorization", "")
        )

        # Enfileirar tarefa para processamento assíncrono
        task_data = {
            "account_id": account_id,
            "product_id": params["product_id"],
            "metadata": metadata,
            "params": params
        }
        request_id = enqueue_task("generate_description", task_data)

        # Retornar resposta
        return WebhookResponse(
            success=True,
            message="Produto enfileirado para geração de descrição",
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Erro ao processar webhook de geração de descrição: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@app.get("/api/v1/webhook/status/{request_id}")
async def check_status(
    request_id: str,
    authorized: bool = Depends(verify_token)
):
    """
    Endpoint para verificar o status de uma tarefa.

    Args:
        request_id: ID da tarefa
        authorized: Resultado da verificação do token

    Returns:
        dict: Status da tarefa
    """
    # TODO: Implementar verificação real do status da tarefa
    # Por enquanto, retornar um status fixo
    return {
        "request_id": request_id,
        "status": "pending",
        "message": "Tarefa em processamento",
        "timestamp": datetime.now().isoformat()
    }

# Ponto de entrada para execução direta
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
