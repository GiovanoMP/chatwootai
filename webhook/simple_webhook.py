#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Webhook Forwarder para Chatwoot

Este script implementa um servidor webhook simples que recebe webhooks do Chatwoot
e os encaminha para uma URL específica. É útil para desenvolvimento local quando
o Chatwoot está hospedado em um servidor remoto.

Autor: Giovano Panatta
Data: Março de 2025
"""

import os
import json
import logging
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8002"))
FORWARD_URL = "https://226e-2804-2610-6721-6300-5711-32d8-fa30-3587.ngrok-free.app/webhook"

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint para receber webhooks do Chatwoot e encaminhá-los.
    
    Args:
        request (Request): A requisição recebida
        
    Returns:
        JSONResponse: Resposta indicando o status do processamento
    """
    # Registrar cabeçalhos recebidos
    headers = dict(request.headers)
    print(f"Cabeçalhos recebidos: {headers}")
    
    # Obter o corpo da requisição
    body = await request.body()
    body_str = body.decode("utf-8")
    print(f"Corpo recebido: {body_str[:200]}...")
    
    try:
        # Encaminhar a requisição para a URL configurada
        response = requests.post(
            FORWARD_URL,
            headers={"Content-Type": "application/json"},
            data=body
        )
        print(f"Encaminhado para {FORWARD_URL} - Resposta: {response.status_code}")
        
        # Retornar resposta de sucesso
        return JSONResponse(
            content={
                "status": "success",
                "message": f"Webhook encaminhado com sucesso para {FORWARD_URL}",
                "response_code": response.status_code
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Erro ao encaminhar webhook: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Erro ao encaminhar webhook: {str(e)}"
            },
            status_code=500
        )

if __name__ == "__main__":
    print(f"Iniciando servidor webhook simples na porta {WEBHOOK_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=WEBHOOK_PORT)
