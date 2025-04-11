#!/bin/bash

# Script para iniciar o serviço de vetorização

# Carregar variáveis de ambiente
if [ -f .env.vector-service ]; then
    echo "Carregando variáveis de ambiente de .env.vector-service"
    export $(grep -v '^#' .env.vector-service | xargs)
else
    echo "Arquivo .env.vector-service não encontrado. Usando valores padrão."
fi

# Verificar dependências
if ! command -v python3 &> /dev/null; then
    echo "Python 3 não encontrado. Por favor, instale o Python 3."
    exit 1
fi

# Verificar se o Qdrant está acessível
if ! curl -s "http://${QDRANT_HOST:-localhost}:${QDRANT_PORT:-6333}/collections" &> /dev/null; then
    echo "AVISO: Não foi possível conectar ao Qdrant em ${QDRANT_HOST:-localhost}:${QDRANT_PORT:-6333}."
    echo "Certifique-se de que o Qdrant está em execução antes de usar o serviço de vetorização."
fi

# Verificar se a chave da API OpenAI está configurada
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERRO: OPENAI_API_KEY não está configurada. Por favor, defina esta variável de ambiente."
    exit 1
fi

# Instalar dependências se necessário
if [ "$1" == "--install" ]; then
    echo "Instalando dependências..."
    pip install -r requirements.txt
fi

# Iniciar o serviço de vetorização
echo "Iniciando o serviço de vetorização..."
python -m src.vector_service.run

# Capturar código de saída
EXIT_CODE=$?

# Verificar se o serviço foi iniciado com sucesso
if [ $EXIT_CODE -eq 0 ]; then
    echo "Serviço de vetorização iniciado com sucesso."
else
    echo "Erro ao iniciar o serviço de vetorização. Código de saída: $EXIT_CODE"
    exit $EXIT_CODE
fi
