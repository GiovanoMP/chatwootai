from fastapi import FastAPI, HTTPException, Header, Request
from common.config import MCP_HOST, MCP_PORT
from common.models import WebhookPayload, MessageResponse
from common.chatwoot import ChatwootClient
from common.tenant import TenantManager
from common.health import register_health_endpoint
import uvicorn

app = FastAPI()
chatwoot = ChatwootClient()
tenant_manager = TenantManager()

# Registrar o endpoint de saúde
register_health_endpoint(app)

@app.post("/webhook", response_model=MessageResponse)
async def webhook(
    request: Request,
    payload: WebhookPayload,
    x_hub_signature: str = Header(None)
):
    """Webhook para receber eventos do Chatwoot API Channel."""
    # 1. Validação da assinatura HMAC
    body = await request.body()
    if not chatwoot.verify_webhook_signature(body, x_hub_signature):
        raise HTTPException(
            status_code=403,
            detail="Assinatura HMAC inválida"
        )

    # 2. Validação do tenant
    if not tenant_manager.validate_tenant_access(payload.account_id, payload.inbox_id):
        raise HTTPException(
            status_code=403,
            detail=f"Tenant {payload.account_id} não tem acesso à inbox {payload.inbox_id}"
        )

    # 3. Processamento do evento
    try:
        # TODO: Implementar lógica de processamento específica por evento
        # Por exemplo, enviar para MCP-Crew para processamento
        return MessageResponse(
            success=True,
            message=f"Evento {payload.event} processado com sucesso"
        )
    except Exception as e:
        return MessageResponse(
            success=False,
            message="Erro ao processar evento",
            error=str(e)
        )

@app.post("/conversations", response_model=MessageResponse)
async def create_conversation(
    request: Request,
    x_hub_signature: str = Header(None)
):
    """Cria uma nova conversa via API Channel."""
    # 1. Validação da assinatura HMAC
    body = await request.body()
    if not chatwoot.verify_webhook_signature(body, x_hub_signature):
        raise HTTPException(
            status_code=403,
            detail="Assinatura HMAC inválida"
        )

    # 2. Criar contato e conversa
    try:
        data = await request.json()
        account_id = data.get('account_id')
        source_id = data.get('source_id')
        contact_name = data.get('contact_name', 'Usuário')

        # Criar contato
        contact = chatwoot.create_contact(
            account_id=account_id,
            name=contact_name,
            identifier=source_id
        )
        if not contact:
            raise HTTPException(
                status_code=400,
                detail="Erro ao criar contato"
            )

        # Criar conversa
        conversation = chatwoot.create_conversation(
            account_id=account_id,
            contact_id=contact['id'],
            source_id=source_id
        )
        if not conversation:
            raise HTTPException(
                status_code=400,
                detail="Erro ao criar conversa"
            )

        return MessageResponse(
            success=True,
            message="Conversa criada com sucesso"
        )
    except Exception as e:
        return MessageResponse(
            success=False,
            message="Erro ao criar conversa",
            error=str(e)
        )

@app.get("/health")
async def health():
    """Endpoint de health check."""
    return {"status": "healthy"}

def main():
    """Função principal que inicia o servidor."""
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
