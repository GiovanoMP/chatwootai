import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        # Receber o corpo da requisição
        body = await request.json()
        print(f"Recebido evento do Chatwoot: {json.dumps(body, indent=2)}")
        
        # Aqui você pode adicionar lógica para processar o evento
        
        return {"status": "received", "message": "Evento recebido com sucesso"}
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.getenv('WEBHOOK_PORT', 8001))
    print(f"Iniciando servidor webhook de teste na porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
