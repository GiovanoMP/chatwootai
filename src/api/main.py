"""
Ponto de entrada principal para a API REST.

Este módulo inicializa a aplicação FastAPI e registra todas as rotas.

Autor: Augment Agent
Data: 26/03/2025
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar rotas
from .odoo import app as odoo_app

# Criar aplicação principal
app = FastAPI(
    title="ChatwootAI API",
    description="API REST para integração com sistemas externos",
    version="1.0.0"
)

# Adicionar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar aplicações
app.mount("/odoo", odoo_app)

# Rota raiz
@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está funcionando."""
    return {
        "message": "ChatwootAI API",
        "version": "1.0.0",
        "endpoints": [
            "/odoo - Integração com Odoo"
        ]
    }

# Ponto de entrada para execução direta
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
