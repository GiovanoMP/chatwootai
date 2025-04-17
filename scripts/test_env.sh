#!/bin/bash
# Script para testar o carregamento de variáveis de ambiente

# Configurar diretório de logs
mkdir -p logs

# Iniciar o teste
echo -e "\n======================================================================="
echo "🔍 TESTANDO CARREGAMENTO DE VARIÁVEIS DE AMBIENTE"
echo "======================================================================="

# Verificar se o arquivo .env existe
if [ -f ".env" ]; then
    echo "✅ Arquivo .env encontrado"
    
    # Exibir o conteúdo do arquivo .env (sem mostrar valores sensíveis)
    echo "📋 Conteúdo do arquivo .env (chaves apenas):"
    grep -v "^#" .env | cut -d= -f1
    
    # Carregar variáveis de ambiente do arquivo .env
    echo "🔄 Carregando variáveis de ambiente..."
    set -a  # Ativa o modo de exportação automática
    source .env
    set +a  # Desativa o modo de exportação automática
    
    # Verificar se o token do ngrok está configurado
    if [ -z "$NGROK_AUTH_TOKEN" ]; then
        echo "❌ Token de autenticação do Ngrok não configurado"
    else
        echo "✅ Token de autenticação do Ngrok configurado"
        echo "   Primeiros 5 caracteres: ${NGROK_AUTH_TOKEN:0:5}..."
    fi
    
    # Verificar outras variáveis importantes
    echo -e "\n📊 Status de outras variáveis importantes:"
    
    if [ -z "$WEBHOOK_PORT" ]; then
        echo "❌ WEBHOOK_PORT não configurado"
    else
        echo "✅ WEBHOOK_PORT configurado: $WEBHOOK_PORT"
    fi
    
    if [ -z "$CHATWOOT_API_KEY" ]; then
        echo "❌ CHATWOOT_API_KEY não configurado"
    else
        echo "✅ CHATWOOT_API_KEY configurado"
    fi
    
    if [ -z "$CHATWOOT_BASE_URL" ]; then
        echo "❌ CHATWOOT_BASE_URL não configurado"
    else
        echo "✅ CHATWOOT_BASE_URL configurado: $CHATWOOT_BASE_URL"
    fi
else
    echo "❌ Arquivo .env não encontrado"
    echo "   Procurando em: $(pwd)/.env"
fi

echo -e "\n======================================================================="
echo "✅ TESTE CONCLUÍDO"
echo "======================================================================="
