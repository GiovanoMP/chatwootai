#!/bin/bash

# Script para iniciar o MCP-Odoo

# Carregar variáveis de ambiente
if [ -f .env.mcp-odoo ]; then
    echo "Carregando variáveis de ambiente de .env.mcp-odoo"
    export $(grep -v '^#' .env.mcp-odoo | xargs)
else
    echo "Arquivo .env.mcp-odoo não encontrado. Usando valores padrão."
fi

# Verificar dependências
if ! command -v python3 &> /dev/null; then
    echo "Python 3 não encontrado. Por favor, instale o Python 3."
    exit 1
fi

# Verificar se a chave da API OpenAI está configurada
if [ -z "$OPENAI_API_KEY" ]; then
    echo "AVISO: OPENAI_API_KEY não está configurada. Algumas funcionalidades podem não funcionar corretamente."
fi

# Verificar se as credenciais do Odoo estão configuradas
if [ -z "$ODOO_HOST" ] || [ -z "$ODOO_PORT" ] || [ -z "$ODOO_DB" ] || [ -z "$ODOO_USER" ] || [ -z "$ODOO_PASSWORD" ]; then
    echo "AVISO: Credenciais do Odoo não estão completamente configuradas."
    echo "Certifique-se de definir ODOO_HOST, ODOO_PORT, ODOO_DB, ODOO_USER e ODOO_PASSWORD."
fi

# Instalar dependências se necessário
if [ "$1" == "--install" ]; then
    echo "Instalando dependências..."
    pip install -r requirements.txt
fi

# Iniciar o MCP-Odoo
echo "Iniciando o MCP-Odoo..."
python -m src.mcp_odoo

# Capturar código de saída
EXIT_CODE=$?

# Verificar se o serviço foi iniciado com sucesso
if [ $EXIT_CODE -eq 0 ]; then
    echo "MCP-Odoo encerrado normalmente."
else
    echo "Erro ao executar o MCP-Odoo. Código de saída: $EXIT_CODE"
    exit $EXIT_CODE
fi
