from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base, get_db
from app.api.mapping import router as mapping_router
from app.api.config import router as config_router
from app.api.odoo_webhook import router as odoo_webhook_router
from app.api.company_services import router as company_services_router
from app.core.config import settings
import logging
import uvicorn
import os

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "config_service.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("config-service-api")
logger.info("Iniciando API do serviço de configuração...")

# Criar tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(mapping_router)
app.include_router(config_router)
app.include_router(odoo_webhook_router)
app.include_router(company_services_router)

@app.get("/health")
def health_check():
    """
    Endpoint para verificar a saúde do serviço.

    Returns:
        Status do serviço
    """
    return {"status": "healthy"}

@app.get("/")
def root():
    """
    Endpoint raiz.

    Returns:
        Informações sobre a API
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs",
    }

if __name__ == "__main__":
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
