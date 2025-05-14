from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import os
import json
import yaml
from datetime import datetime
import logging
import uvicorn

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("webhook-mongo")

# Carregar variáveis de ambiente
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://config_user:config_password@localhost:27017/config_service")
API_KEY = os.getenv("API_KEY", "development-api-key")

app = FastAPI(title="Webhook MongoDB", description="Webhook para receber dados do módulo company_services e armazená-los no MongoDB")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexão com o MongoDB
client = None

@app.on_event("startup")
async def startup_db_client():
    global client
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        # Verificar conexão
        await client.admin.command('ping')
        logger.info("Conectado ao MongoDB com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao conectar ao MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        logger.info("Conexão com MongoDB fechada")

# Modelos
class CompanyServiceData(BaseModel):
    yaml_content: str

# Dependência para verificar API Key
async def verify_api_key(x_api_key: str = Header(...), x_security_token: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return x_api_key, x_security_token

# Rotas
@app.get("/")
async def root():
    return {"message": "Webhook MongoDB para company_services"}

@app.get("/health")
async def health_check():
    try:
        # Verificar conexão com MongoDB
        await client.admin.command('ping')
        return {"status": "healthy", "mongodb": "connected"}
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return {"status": "unhealthy", "error": str(e)}

# Rota para receber dados do módulo company_services
@app.post("/company-services/{account_id}/metadata")
async def receive_company_services_data(
    account_id: str,
    data: CompanyServiceData,
    auth: tuple = Depends(verify_api_key)
):
    _, security_token = auth
    
    try:
        # Converter YAML para JSON
        try:
            config_data = yaml.safe_load(data.yaml_content)
        except Exception as e:
            logger.error(f"Erro ao converter YAML para JSON: {e}")
            raise HTTPException(status_code=400, detail=f"Erro ao processar YAML: {str(e)}")
        
        # Verificar se o account_id no path corresponde ao account_id no payload
        if config_data.get("account_id") != account_id:
            logger.error(f"account_id no path ({account_id}) não corresponde ao account_id no payload ({config_data.get('account_id')})")
            raise HTTPException(status_code=400, detail="account_id no path não corresponde ao account_id no payload")
        
        # Verificar token de segurança
        if security_token and config_data.get("security_token") != security_token:
            logger.error("Token de segurança inválido")
            raise HTTPException(status_code=401, detail="Token de segurança inválido")
        
        # Adicionar timestamp
        config_data["updated_at"] = datetime.now()
        
        # Salvar no MongoDB
        db = client.config_service
        
        # Verificar se já existe um documento para este account_id
        existing = await db.company_services.find_one({"account_id": account_id})
        
        if existing:
            # Atualizar documento existente
            result = await db.company_services.update_one(
                {"account_id": account_id},
                {"$set": config_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Documento atualizado para account_id: {account_id}")
                return {"success": True, "message": "Dados atualizados com sucesso"}
            else:
                logger.warning(f"Nenhuma modificação feita para account_id: {account_id}")
                return {"success": True, "message": "Nenhuma modificação necessária"}
        else:
            # Criar novo documento
            result = await db.company_services.insert_one(config_data)
            
            if result.inserted_id:
                logger.info(f"Novo documento criado para account_id: {account_id}")
                return {"success": True, "message": "Dados inseridos com sucesso"}
            else:
                logger.error(f"Erro ao inserir documento para account_id: {account_id}")
                raise HTTPException(status_code=500, detail="Erro ao inserir documento no MongoDB")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar dados: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8003, reload=True)
