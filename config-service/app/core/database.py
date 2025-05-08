from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# URL de conexão com o banco de dados
# Forçar a URL correta para evitar problemas com variáveis de ambiente do sistema
DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/config_service"
print(f"Conectando ao banco de dados: {DATABASE_URL}")

# Criar engine do SQLAlchemy
engine = create_engine(DATABASE_URL)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos declarativos
Base = declarative_base()

# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
