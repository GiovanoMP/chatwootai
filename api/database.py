"""
Configuração do banco de dados para a API de simulação do Odoo.
"""

import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("odoo_simulation_api.database")

# Configurações do banco de dados
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "chatwootai")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Configuração do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def wait_for_db(max_retries=30, retry_interval=2):
    """
    Aguarda a disponibilidade do banco de dados PostgreSQL.
    
    Args:
        max_retries (int): Número máximo de tentativas
        retry_interval (int): Intervalo entre tentativas em segundos
        
    Returns:
        bool: True se o banco de dados estiver disponível, False caso contrário
    """
    logger.info(f"Aguardando disponibilidade do PostgreSQL em {POSTGRES_HOST}:{POSTGRES_PORT}...")
    
    for attempt in range(max_retries):
        try:
            # Tenta conectar ao banco de dados
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                logger.info("Conexão com o PostgreSQL estabelecida com sucesso!")
                return True
        except Exception as e:
            logger.warning(f"Tentativa {attempt + 1}/{max_retries} falhou: {str(e)}")
            time.sleep(retry_interval)
    
    logger.error(f"Não foi possível conectar ao PostgreSQL após {max_retries} tentativas")
    return False

def get_db():
    """
    Dependência para obter a sessão do banco de dados.
    Usado pelo FastAPI para injeção de dependência.
    
    Yields:
        Session: Sessão do SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Inicializa o banco de dados, verificando se as tabelas existem.
    Esta função é chamada na inicialização da aplicação.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    try:
        # Verifica se o banco de dados está disponível
        if not wait_for_db():
            return False
        
        # Verifica se as tabelas existem
        with engine.connect() as connection:
            # Lista de tabelas que devem existir
            required_tables = [
                "product_categories", "products", "inventory", 
                "service_categories", "services", "customers", 
                "orders", "order_items", "appointments", 
                "professionals", "professional_services", 
                "business_rules", "product_enrichment", 
                "service_enrichment", "customer_interactions"
            ]
            
            # Verifica cada tabela
            for table in required_tables:
                result = connection.execute(text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                )).fetchone()
                
                if not result[0]:
                    logger.warning(f"Tabela '{table}' não encontrada no banco de dados")
                    return False
            
            logger.info("Todas as tabelas necessárias estão presentes no banco de dados")
            return True
            
    except Exception as e:
        logger.error(f"Erro ao inicializar o banco de dados: {str(e)}")
        return False
