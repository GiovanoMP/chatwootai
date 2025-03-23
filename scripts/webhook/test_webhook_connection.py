#!/usr/bin/env python3
"""
Script para testar a conexão do webhook com o Chatwoot e a VPS

Este script:
1. Verifica se o servidor webhook está rodando
2. Simula o recebimento de uma mensagem do Chatwoot
3. Registra logs detalhados de todo o processo
4. Verifica a conexão com a VPS
"""

import os
import sys
import json
import time
import requests
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('webhook_test.log')
    ]
)
logger = logging.getLogger('webhook_test')

def load_env_vars():
    """Carrega variáveis de ambiente do arquivo .env."""
    # Encontrar o diretório raiz do projeto
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent.parent  # Subir dois níveis: webhook/scripts -> projeto raiz
    
    # Caminho para o arquivo .env
    env_path = root_dir / '.env'
    
    if env_path.exists():
        logger.info(f"📁 Carregando variáveis de ambiente de {env_path}")
        load_dotenv(dotenv_path=env_path)
        return True
    else:
        logger.error(f"❌ Arquivo .env não encontrado em {env_path}")
        return False

def get_ngrok_url():
    """Obtém a URL pública do ngrok consultando sua API local."""
    try:
        logger.info("🔍 Verificando URL do Ngrok...")
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                logger.info(f"✅ URL do Ngrok encontrada: {tunnel['public_url']}")
                return tunnel["public_url"]
    except Exception as e:
        logger.error(f"❌ Erro ao obter URL do ngrok: {str(e)}")
    return None

def check_webhook_server():
    """Verifica se o servidor webhook está rodando."""
    logger.info("🔍 Verificando se o servidor webhook está rodando...")
    
    # Obter a porta do webhook do arquivo .env
    webhook_port = os.environ.get("WEBHOOK_PORT", "8001")
    webhook_host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
    
    try:
        # Verificar se a porta está em uso
        result = subprocess.run(
            f"lsof -i:{webhook_port}", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Servidor webhook rodando na porta {webhook_port}")
            return True
        else:
            logger.warning(f"⚠️ Servidor webhook não encontrado na porta {webhook_port}")
            
            # Verificar processos Python em execução
            python_processes = subprocess.run(
                "ps aux | grep python | grep -v grep", 
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            logger.info(f"📋 Processos Python em execução:\n{python_processes.stdout}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao verificar servidor webhook: {str(e)}")
        return False

def test_webhook_endpoint(webhook_url):
    """Testa o endpoint do webhook enviando uma mensagem de teste."""
    logger.info(f"🔄 Testando endpoint do webhook: {webhook_url}")
    
    # Criar uma mensagem de teste similar ao formato do Chatwoot
    test_message = {
        "event": "message_created",
        "account": {
            "id": 1
        },
        "message": {
            "id": 123456,
            "content": "Mensagem de teste do script de verificação",
            "message_type": 0,
            "content_type": "text"
        },
        "conversation": {
            "id": 789012,
            "inbox_id": 345678
        },
        "contact": {
            "id": 901234,
            "name": "Usuário de Teste"
        }
    }
    
    try:
        # Adicionar cabeçalho de autenticação se configurado
        headers = {}
        auth_token = os.environ.get("WEBHOOK_AUTH_TOKEN")
        if auth_token:
            logger.info("🔐 Adicionando token de autenticação ao cabeçalho")
            headers["X-Auth-Token"] = auth_token
        
        # Enviar requisição POST para o webhook
        logger.info(f"📤 Enviando mensagem de teste para: {webhook_url}")
        logger.debug(f"📋 Conteúdo da mensagem: {json.dumps(test_message, indent=2)}")
        
        response = requests.post(
            webhook_url,
            json=test_message,
            headers=headers,
            timeout=10
        )
        
        # Verificar resposta
        logger.info(f"📥 Resposta recebida: Código {response.status_code}")
        logger.debug(f"📋 Conteúdo da resposta: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ Teste do webhook bem-sucedido!")
            return True
        else:
            logger.error(f"❌ Falha no teste do webhook: Código {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao testar webhook: {str(e)}")
        return False

def check_vps_connection():
    """Verifica a conexão com a VPS."""
    logger.info("🔍 Verificando conexão com a VPS...")
    
    # Obter credenciais da VPS
    vps_host = os.environ.get("VPS_HOST")
    
    if not vps_host:
        logger.error("❌ Host da VPS não encontrado no arquivo .env")
        return False
    
    try:
        # Tentar fazer um ping na VPS
        logger.info(f"🔄 Testando conexão com {vps_host}...")
        
        ping_process = subprocess.run(
            f"ping -c 3 {vps_host}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if ping_process.returncode == 0:
            logger.info(f"✅ Conexão com a VPS estabelecida: {vps_host}")
            logger.debug(f"📋 Resultado do ping:\n{ping_process.stdout}")
            return True
        else:
            logger.error(f"❌ Falha ao conectar com a VPS: {vps_host}")
            logger.debug(f"📋 Erro do ping:\n{ping_process.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao verificar conexão com a VPS: {str(e)}")
        return False

def main():
    """Função principal para testar a conexão do webhook."""
    try:
        print("\n" + "="*80)
        print("🧪 TESTE DE CONEXÃO DO WEBHOOK")
        print("="*80)
        
        # Carregar variáveis de ambiente
        if not load_env_vars():
            print("❌ Falha ao carregar variáveis de ambiente. Abortando teste.")
            return
        
        # Verificar se o Ngrok está rodando
        ngrok_url = get_ngrok_url()
        if not ngrok_url:
            print("❌ Ngrok não está rodando. Inicie o Ngrok primeiro com o script simple_ngrok_starter.py")
            return
        
        webhook_url = f"{ngrok_url}/webhook"
        print(f"🌐 URL do Webhook: {webhook_url}")
        
        # Verificar se o servidor webhook está rodando
        if not check_webhook_server():
            print("\n⚠️ Servidor webhook não detectado!")
            start_server = input("❓ Deseja iniciar o servidor webhook agora? (s/n): ").lower()
            
            if start_server == 's' or start_server == 'sim':
                print("\n🚀 Iniciando servidor webhook...")
                
                # Iniciar o servidor webhook em segundo plano
                server_command = "python src/webhook/server.py"
                subprocess.Popen(
                    server_command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                print("⏳ Aguardando o servidor iniciar...")
                time.sleep(5)
            else:
                print("⚠️ O teste continuará, mas o servidor webhook não está rodando!")
        
        # Verificar conexão com a VPS
        vps_connected = check_vps_connection()
        
        # Testar o endpoint do webhook
        webhook_working = test_webhook_endpoint(webhook_url)
        
        # Exibir resumo dos testes
        print("\n" + "="*80)
        print("📊 RESUMO DOS TESTES")
        print("="*80)
        print(f"🌐 Ngrok: {'✅ Funcionando' if ngrok_url else '❌ Não detectado'}")
        print(f"🖥️ Servidor Webhook: {'✅ Rodando' if check_webhook_server() else '❌ Não detectado'}")
        print(f"🔌 Conexão VPS: {'✅ Estabelecida' if vps_connected else '❌ Falhou'}")
        print(f"🧪 Teste Webhook: {'✅ Bem-sucedido' if webhook_working else '❌ Falhou'}")
        print("="*80)
        
        # Exibir próximos passos
        print("\n" + "="*80)
        print("📝 PRÓXIMOS PASSOS")
        print("="*80)
        
        if not check_webhook_server():
            print("1. Inicie o servidor webhook com o comando:")
            print("   python src/webhook/server.py")
        
        if not vps_connected:
            print("1. Verifique a conexão com a VPS:")
            print(f"   ping {os.environ.get('VPS_HOST')}")
        
        if not webhook_working:
            print("1. Verifique os logs do servidor webhook para identificar problemas.")
            print("2. Certifique-se de que o servidor está configurado para receber requisições na rota /webhook")
        
        if ngrok_url and check_webhook_server() and vps_connected and webhook_working:
            print("✅ Todos os testes passaram! O sistema parece estar funcionando corretamente.")
            print("📋 Consulte o arquivo webhook_test.log para ver logs detalhados.")
        
        print("="*80)
    
    except KeyboardInterrupt:
        print("\n👋 Teste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        import traceback
        print(f"📋 Detalhes do erro:\n{traceback.format_exc()}")
    finally:
        print("\n👋 Teste concluído.")
        print("📋 Consulte o arquivo webhook_test.log para ver logs detalhados.")

if __name__ == "__main__":
    main()
