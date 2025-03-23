#!/usr/bin/env python3
"""
Script Simplificado para Iniciar Ngrok e Configurar Webhook

Este script:
1. Inicia o Ngrok para expor o servidor webhook local
2. Obtém a URL pública gerada pelo Ngrok
3. Atualiza o webhook no Chatwoot API
4. Fornece instruções para atualização manual do proxy na VPS
"""

import os
import sys
import subprocess
import time
import json
import requests
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ngrok_script')

def load_env_vars():
    """Carrega variáveis de ambiente do arquivo .env."""
    # Encontrar o diretório raiz do projeto
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent.parent  # Subir dois níveis: webhook/scripts -> projeto raiz
    
    # Caminho para o arquivo .env
    env_path = root_dir / '.env'
    
    if env_path.exists():
        print(f"📁 Carregando variáveis de ambiente de {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"⚠️ Arquivo .env não encontrado em {env_path}")

def get_ngrok_url():
    """Obtém a URL pública do ngrok consultando sua API local."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
    except Exception as e:
        print(f"❌ Erro ao obter URL do ngrok: {str(e)}")
    return None

def update_chatwoot_webhook(webhook_url):
    """Atualiza a configuração do webhook no Chatwoot API."""
    api_key = os.environ.get("CHATWOOT_API_KEY")
    base_url = os.environ.get("CHATWOOT_BASE_URL")
    account_id = os.environ.get("CHATWOOT_ACCOUNT_ID")
    
    if not api_key or not base_url or not account_id:
        print("❌ Credenciais do Chatwoot não encontradas no arquivo .env")
        return False
    
    print(f"🔄 Atualizando webhook no Chatwoot...")
    print(f"   URL Base: {base_url}")
    print(f"   Conta ID: {account_id}")
    print(f"   Nova URL: {webhook_url}")
    
    # Endpoint para atualizar as configurações da conta
    url = f"{base_url}/accounts/{account_id}/webhook_settings"
    
    # Cabeçalhos da requisição
    headers = {
        "api_access_token": api_key,
        "Content-Type": "application/json"
    }
    
    # Dados para atualizar o webhook
    data = {
        "webhook_url": webhook_url
    }
    
    try:
        # Enviar requisição para atualizar o webhook
        response = requests.put(url, headers=headers, json=data)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            print("✅ Webhook atualizado com sucesso no Chatwoot!")
            return True
        else:
            print(f"❌ Erro ao atualizar webhook no Chatwoot: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao comunicar com a API do Chatwoot: {str(e)}")
        return False

def print_vps_instructions(webhook_url):
    """Exibe instruções para atualização manual do proxy na VPS."""
    vps_host = os.environ.get("VPS_HOST", "srv692745.hstgr.cloud")
    vps_user = os.environ.get("VPS_USER", "root")
    container_name = os.environ.get("PROXY_CONTAINER_NAME", "05abfcd7e2aa")
    proxy_file_path = os.environ.get("PROXY_FILE_PATH", "/app/simple_webhook.py")
    
    print("\n" + "="*80)
    print("📝 INSTRUÇÕES PARA ATUALIZAÇÃO MANUAL DO PROXY NA VPS")
    print("="*80)
    print(f"1. Conecte-se à VPS via SSH:")
    print(f"   ssh {vps_user}@{vps_host}")
    print(f"   (Digite a senha quando solicitado)")
    print()
    print(f"2. Verifique se o container existe:")
    print(f"   docker ps -a | grep {container_name}")
    print()
    print(f"3. Se o container estiver parado, inicie-o:")
    print(f"   docker start {container_name}")
    print()
    print(f"4. Verifique se o arquivo do proxy existe:")
    print(f"   docker exec {container_name} ls -la {proxy_file_path}")
    print()
    print(f"5. Faça backup do arquivo atual:")
    print(f"   docker exec {container_name} cp {proxy_file_path} {proxy_file_path}.bak")
    print()
    print(f"6. Atualize a URL no arquivo (COPIE E COLE ESTE COMANDO EXATAMENTE COMO ESTÁ):")
    print(f"   docker exec {container_name} sed -i \"s|FORWARD_URL *= *[\\\"'][^\\\"']*[\\\"']|FORWARD_URL = '{webhook_url}'|g\" {proxy_file_path}")
    print()
    print(f"7. Verifique se a atualização foi bem-sucedida:")
    print(f"   docker exec {container_name} grep -A 1 -B 1 FORWARD_URL {proxy_file_path}")
    print()
    print(f"8. Reinicie o container para aplicar as mudanças:")
    print(f"   docker restart {container_name}")
    print("="*80)

def main():
    """Função principal para iniciar e monitorar o ngrok."""
    try:
        # Carregar variáveis de ambiente
        load_env_vars()
        
        print("\n" + "="*80)
        print("🚀 INICIANDO NGROK PARA O WEBHOOK")
        print("="*80)
        
        # Verificar se o ngrok já está em execução
        try:
            existing_url = get_ngrok_url()
            if existing_url:
                print(f"🔍 Ngrok já está em execução!")
                print(f"🌐 URL atual: {existing_url}")
                
                # Perguntar se deseja usar a URL existente
                use_existing = input("\n❓ Deseja usar esta URL existente? (s/n): ").lower()
                if use_existing == 's' or use_existing == 'sim':
                    ngrok_url = existing_url
                else:
                    print("\n🔄 Encerrando o ngrok existente...")
                    subprocess.run(["pkill", "-f", "ngrok"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(2)
                    ngrok_url = None
            else:
                ngrok_url = None
        except Exception:
            ngrok_url = None
        
        # Iniciar o ngrok se necessário
        if not ngrok_url:
            # Obter configurações
            ngrok_token = os.environ.get("NGROK_AUTH_TOKEN")
            webhook_port = os.environ.get("WEBHOOK_PORT", "8001")
            webhook_host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
            
            if not ngrok_token:
                print("❌ Token de autenticação do ngrok não encontrado no arquivo .env")
                return
            
            print(f"\n🚀 Iniciando ngrok para o servidor webhook ({webhook_host}:{webhook_port})...")
            
            # Iniciar o ngrok em segundo plano
            ngrok_command = f"ngrok http {webhook_host}:{webhook_port} --log=stdout"
            subprocess.Popen(
                ngrok_command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Aguardar o ngrok iniciar
            print("⏳ Aguardando o ngrok iniciar (isso pode levar alguns segundos)...")
            time.sleep(5)
            
            # Obter a URL do ngrok
            for i in range(5):
                ngrok_url = get_ngrok_url()
                if ngrok_url:
                    break
                print(f"⏳ Tentativa {i+1}/5: Aguardando URL do ngrok...")
                time.sleep(2)
            
            if not ngrok_url:
                print("❌ Não foi possível obter a URL do ngrok após várias tentativas")
                return
        
        # Construir a URL completa do webhook
        webhook_url = f"{ngrok_url}/webhook"
        
        print("\n" + "="*80)
        print("✅ NGROK INICIADO COM SUCESSO!")
        print("="*80)
        print(f"🌐 URL do Ngrok: {ngrok_url}")
        print(f"🔗 URL do Webhook: {webhook_url}")
        print("="*80)
        
        # Perguntar se deseja atualizar o webhook no Chatwoot
        print("\n" + "="*80)
        print("🔄 ATUALIZAÇÃO DO WEBHOOK NO CHATWOOT")
        print("="*80)
        update_chatwoot = input("❓ Deseja atualizar o webhook no Chatwoot? (s/n): ").lower()
        
        if update_chatwoot == 's' or update_chatwoot == 'sim':
            update_chatwoot_webhook(webhook_url)
        else:
            print("⏭️ Atualização do Chatwoot ignorada pelo usuário.")
        
        # Exibir instruções para atualização manual do proxy na VPS
        print_vps_instructions(webhook_url)
        
        # Exibir mensagem de conclusão
        print("\n" + "="*80)
        print("🎉 RESUMO DA CONFIGURAÇÃO")
        print("="*80)
        print(f"🌐 URL do Ngrok: {ngrok_url}")
        print(f"🔗 URL do Webhook: {webhook_url}")
        
        if update_chatwoot == 's' or update_chatwoot == 'sim':
            print("✅ Chatwoot: Webhook atualizado")
        else:
            print("⏭️ Chatwoot: Atualização ignorada")
        
        print("⚠️ VPS: Instruções fornecidas para atualização manual")
        print("="*80)
        
        # Manter o script em execução para monitorar o ngrok
        print("\n⏳ Monitorando o ngrok... Pressione Ctrl+C para encerrar.")
        
        # Loop para manter o script em execução
        while True:
            time.sleep(60)  # Verificar a cada minuto
            current_url = get_ngrok_url()
            if not current_url:
                print("\n⚠️ Ngrok não está mais em execução!")
                break
            elif current_url != ngrok_url:
                print(f"\n⚠️ URL do ngrok mudou: {current_url}")
                ngrok_url = current_url
                webhook_url = f"{ngrok_url}/webhook"
                print(f"🔗 Nova URL do webhook: {webhook_url}")
                
                # Perguntar se deseja atualizar com a nova URL
                update_new = input("\n❓ A URL do ngrok mudou. Deseja atualizar os webhooks? (s/n): ").lower()
                if update_new == 's' or update_new == 'sim':
                    # Atualizar o webhook no Chatwoot
                    update_chatwoot_webhook(webhook_url)
                    # Exibir instruções para atualização manual do proxy na VPS
                    print_vps_instructions(webhook_url)
    
    except KeyboardInterrupt:
        print("\n👋 Encerrando o script...")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        import traceback
        print(f"📋 Detalhes do erro:\n{traceback.format_exc()}")
    finally:
        print("\n👋 Script encerrado.")
        
        # Perguntar se deseja encerrar o ngrok
        stop_ngrok = input("\n❓ Deseja encerrar o ngrok? (s/n): ").lower()
        if stop_ngrok == 's' or stop_ngrok == 'sim':
            print("🔄 Encerrando o ngrok...")
            subprocess.run(["pkill", "-f", "ngrok"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✅ Ngrok encerrado.")
        else:
            print("ℹ️ O ngrok continuará em execução em segundo plano.")
            print("   Para encerrá-lo manualmente, execute: pkill -f ngrok")

if __name__ == "__main__":
    main()
