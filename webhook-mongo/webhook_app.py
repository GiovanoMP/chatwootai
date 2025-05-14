from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import uvicorn
import motor.motor_asyncio
import os
import logging
from datetime import datetime
import yaml

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("webhook-mongo")

app = FastAPI()

# Get MongoDB URI from environment variable or use default
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/config_service")
api_key = os.environ.get("API_KEY", "development-api-key")

# Connect to MongoDB
client = None

@app.on_event("startup")
async def startup_db_client():
    global client
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
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

class YAMLContent(BaseModel):
    yaml_content: str

async def get_api_key(x_api_key: str = Header(None)):
    if x_api_key != api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.post("/company-services/{account_id}/metadata")
async def receive_metadata(account_id: str, content: YAMLContent, api_key: str = Depends(get_api_key)):
    try:
        # Converter YAML para JSON
        try:
            config_data = yaml.safe_load(content.yaml_content)
        except Exception as e:
            logger.error(f"Erro ao converter YAML para JSON: {e}")
            raise HTTPException(status_code=400, detail=f"Erro ao processar YAML: {str(e)}")
        
        # Adicionar timestamp
        config_data["updated_at"] = datetime.now()
        
        # Salvar no MongoDB
        db = client.config_service
        
        # Store the YAML content in MongoDB
        await db.company_services.update_one(
            {"account_id": account_id},
            {"$set": config_data},
            upsert=True
        )
        logger.info(f"Dados recebidos para account_id: {account_id}")
        return {"success": True, "message": "Dados recebidos com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar dados: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados: {str(e)}")

@app.get("/")
async def root():
    return {"message": "MongoDB Webhook API is running"}

@app.get("/health")
async def health_check():
    try:
        # Verificar conexão com MongoDB
        await client.admin.command('ping')
        return {"status": "healthy", "mongodb": "connected"}
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    # Usar a porta 8003 para corresponder ao mapeamento no docker-compose.yml
    uvicorn.run(app, host="0.0.0.0", port=8003)
