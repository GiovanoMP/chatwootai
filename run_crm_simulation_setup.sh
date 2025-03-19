#!/bin/bash

# Script para configurar a simulação do CRM
# Este script executa o SQL para criar as tabelas necessárias para a simulação do CRM

# Carrega as variáveis de ambiente
if [ -f .env ]; then
    source .env
    echo "Variáveis de ambiente carregadas do arquivo .env"
    
    # Ajusta as variáveis para o formato esperado pelo script
    export POSTGRES_HOST="postgres"
    export POSTGRES_PORT="5432"
    export POSTGRES_DATABASE="$POSTGRES_DB"
    export POSTGRES_USERNAME="$POSTGRES_USER"
    export POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
else
    echo "Arquivo .env não encontrado. Usando valores padrão."
    export POSTGRES_HOST="localhost"
    export POSTGRES_PORT="5432"
    export POSTGRES_DATABASE="chatwoot"
    export POSTGRES_USERNAME="postgres"
    export POSTGRES_PASSWORD="postgres"
fi

echo "Configurando a simulação do CRM..."

# Executa o SQL para criar as tabelas
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USERNAME" -d "$POSTGRES_DATABASE" -f init-scripts/04_create_crm_simulation_tables.sql

# Verifica se a execução foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "Tabelas do CRM simulado criadas com sucesso!"
else
    echo "Erro ao criar as tabelas do CRM simulado."
    exit 1
fi

echo "Simulação do CRM configurada com sucesso!"
echo "Você pode agora usar o serviço CRMContextService para gerenciar o contexto das conversas."
