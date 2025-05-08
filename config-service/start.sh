#!/bin/bash

# Script para iniciar o microserviço de configuração

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar o ambiente virtual
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Verificar se o banco de dados PostgreSQL está disponível
echo "Verificando conexão com o banco de dados..."
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/config_service')

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.close()
    print('Conexão com o banco de dados estabelecida com sucesso!')
except Exception as e:
    print(f'Erro ao conectar ao banco de dados: {str(e)}')
    exit(1)
"

# Iniciar o servidor
echo "Iniciando o servidor..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
