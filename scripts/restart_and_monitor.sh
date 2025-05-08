#!/bin/bash

# Script para reiniciar o servidor e monitorar logs automaticamente
# Este script combina a reinicialização do servidor e o monitoramento de logs
# em um único terminal usando screen

# Verificar se o screen está instalado
SCREEN_INSTALLED=true
if ! command -v screen &> /dev/null; then
    SCREEN_INSTALLED=false
    echo "❌ O comando 'screen' não está instalado."
    echo "Por favor, instale-o com: sudo apt-get install screen"
    echo ""
    echo "Deseja instalar o screen agora? (s/n)"
    read -r resposta
    if [ "$resposta" = "s" ] || [ "$resposta" = "S" ]; then
        echo "Executando: sudo apt-get install screen"
        sudo apt-get install screen

        # Verificar se a instalação foi bem-sucedida
        if ! command -v screen &> /dev/null; then
            echo "❌ Falha ao instalar o screen. Continuando sem screen..."
            SCREEN_INSTALLED=false
        else
            echo "✅ Screen instalado com sucesso!"
            SCREEN_INSTALLED=true
        fi
    else
        echo "⚠️ Continuando sem screen. O servidor será executado no terminal atual."
        echo "⚠️ NOTA: Se você fechar este terminal, o servidor será encerrado."
    fi
fi

# Diretório base do projeto
BASE_DIR="/home/giovano/Projetos/Chatwoot V4"
cd "$BASE_DIR" || exit 1

echo -e "\n======================================================================="
echo "🚀 REINICIANDO E MONITORANDO SERVIDOR UNIFICADO"
echo "======================================================================="

# Encontrar e matar o processo do servidor
echo "🔍 Procurando processos do servidor..."
SERVER_PID=$(ps aux | grep "main.py" | grep -v grep | awk '{print $2}')

if [ -n "$SERVER_PID" ]; then
    echo "🛑 Matando processo do servidor (PID: $SERVER_PID)..."
    kill -9 $SERVER_PID
    sleep 2
    echo "✅ Processo do servidor finalizado"
else
    echo "ℹ️ Nenhum processo do servidor encontrado para finalizar"
fi

# Configurar sistema de logs
echo "🔧 Configurando sistema de logs..."
python scripts/setup_logging.py

# Iniciar o servidor (com ou sem screen)
if [ "$SCREEN_INSTALLED" = true ]; then
    # Usar screen para iniciar o servidor em segundo plano
    echo "🖥️ Criando sessão screen para servidor..."
    screen -dmS server_session bash -c "
        echo '🚀 Iniciando servidor unificado...';
        python main.py 2>&1 | tee -a logs/server.log;
        echo 'Servidor encerrado. Pressione qualquer tecla para sair.';
        read -n 1;
    "

    # Aguardar o servidor iniciar
    echo "⏳ Aguardando o servidor iniciar (5 segundos)..."
    sleep 5

    # Verificar se o servidor está rodando
    if curl -s http://localhost:8001/health > /dev/null; then
        echo "✅ Servidor iniciado com sucesso!"
    else
        echo "⚠️ Servidor pode não ter iniciado corretamente. Verifique os logs."
    fi

    # Iniciar monitoramento de logs
    echo "🔍 Iniciando monitoramento de logs..."
    python scripts/monitor_logs.py --all

    # Instruções para reconectar à sessão screen
    echo -e "\n======================================================================="
    echo "ℹ️ INFORMAÇÕES IMPORTANTES"
    echo "======================================================================="
    echo "O servidor está rodando em uma sessão screen."
    echo "Para reconectar à sessão do servidor, use: screen -r server_session"
    echo "Para sair da sessão sem encerrar o servidor: Ctrl+A, D"
    echo "Para encerrar o servidor: Ctrl+C na sessão do servidor"
    echo "======================================================================="
else
    # Método alternativo sem screen (terminal dividido)
    echo "🚀 Iniciando servidor unificado no terminal atual..."
    echo "⚠️ NOTA: Não feche este terminal ou o servidor será encerrado."
    echo "⚠️ Para monitorar logs, abra outro terminal e execute: python scripts/monitor_logs.py --all"
    echo -e "\n======================================================================="
    echo "🚀 INICIANDO SERVIDOR UNIFICADO"
    echo "======================================================================="

    # Iniciar o servidor no terminal atual
    python main.py 2>&1 | tee -a logs/server.log

    echo -e "\n======================================================================="
    echo "👋 SERVIDOR ENCERRADO"
    echo "======================================================================="
fi
