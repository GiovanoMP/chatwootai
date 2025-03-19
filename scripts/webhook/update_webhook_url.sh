#!/bin/bash
# Script para atualizar a URL do webhook na VPS
# Uso: ./update_webhook_url.sh <nova_url>
# Exemplo: ./update_webhook_url.sh https://12ab-123-456-789-012.ngrok-free.app/webhook

# Verificar se o argumento foi fornecido
if [ -z "$1" ]; then
    echo "Erro: URL não fornecida"
    echo "Uso: ./update_webhook_url.sh <nova_url>"
    echo "Exemplo: ./update_webhook_url.sh https://12ab-123-456-789-012.ngrok-free.app/webhook"
    exit 1
fi

# Definir a nova URL
NOVA_URL=$1

# Exibir informações
echo "Atualizando URL do webhook para: $NOVA_URL"
echo "Este script deve ser executado na VPS onde o serviço simple_webhook está implantado."
echo ""

# Comandos a serem executados na VPS
echo "Execute os seguintes comandos na VPS:"
echo "----------------------------------------"
echo "cd ~/simple_webhook"
echo "cp simple_webhook.py simple_webhook.py.bak"
echo "sed -i \"s|FORWARD_URL = \\\".*\\\"|FORWARD_URL = \\\"$NOVA_URL\\\"|g\" simple_webhook.py"
echo "docker build -t simple_webhook:latest ."
echo "docker service update --force simple_webhook_simple_webhook"
echo "docker service logs -f simple_webhook_simple_webhook"
echo "----------------------------------------"
echo ""
echo "Após executar esses comandos, verifique se o serviço está funcionando corretamente."
echo "Para testar, envie uma mensagem no Chatwoot e verifique se o webhook está sendo encaminhado para a nova URL."
