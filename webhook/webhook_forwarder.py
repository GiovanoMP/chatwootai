import os
import requests
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

# URL do seu ambiente local via ngrok (você atualizará isso depois)
FORWARD_URL = 'https://cfae-2804-2610-6721-6300-447f-32cf-cd06-94ab.ngrok-free.app/webhook'
AUTH_TOKEN = os.getenv('WEBHOOK_AUTH_TOKEN', 'efetivia_webhook_secret_token_2025')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Função verify_token modificada para aceitar qualquer requisição
async def verify_token(request: Request):
    # Registrar todos os cabeçalhos para debug
    print(f"Cabeçalhos recebidos: {dict(request.headers)}")
    
    # Desativando temporariamente a verificação de autenticação
    print("MODO DE TESTE: Autenticação desativada temporariamente")
    return "test_token"  # Retorna um token fictício
    
    # Código original comentado
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    scheme, token = auth_header.split()
    if scheme.lower() != 'bearer':
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return token
    """

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook_handler(request: Request):  # Removido Depends(verify_token)
    try:
        # Verificação de token desativada temporariamente
        await verify_token(request)
        
        # Receber o corpo da requisição
        body = await request.json()
        print(f"Recebido evento: {json.dumps(body)[:200]}...")
        
        # Encaminhar o evento para o ambiente local
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {AUTH_TOKEN}'
        }
        
        response = requests.post(FORWARD_URL, json=body, headers=headers)
        print(f"Evento encaminhado para {FORWARD_URL}. Resposta: {response.status_code}")
        
        return {"status": "forwarded", "destination": FORWARD_URL}
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.getenv('WEBHOOK_PORT', 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
