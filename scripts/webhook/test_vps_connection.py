#!/usr/bin/env python3
"""
Script para testar a conexão com a VPS e a atualização do proxy.
Este script testa apenas a função update_vps_proxy do start_ngrok.py.
"""

import os
import sys
import logging
import dotenv
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_vps_connection")

# Adicionar o diretório raiz ao path para importações
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

# Importar a função que queremos testar
from scripts.webhook.start_ngrok import update_vps_proxy, load_env_vars

def main():
    """Função principal para testar a conexão com a VPS."""
    # Carregar variáveis de ambiente
    load_env_vars()
    
    # URL de teste
    test_url = "https://test-connection-url.ngrok-free.app/webhook"
    
    print("\n" + "="*70)
    print("🧪 TESTE DE CONEXÃO COM A VPS")
    print("="*70)
    
    # Mostrar as variáveis de ambiente relevantes (sem a senha)
    print(f"🔍 Variáveis de ambiente:")
    print(f"  - VPS_HOST: {os.environ.get('VPS_HOST')}")
    print(f"  - VPS_USER: {os.environ.get('VPS_USER')}")
    print(f"  - VPS_PASSWORD: {'*' * 8 if os.environ.get('VPS_PASSWORD') else 'Não definida'}")
    print(f"  - VPS_KEY_PATH: {os.environ.get('VPS_KEY_PATH') or 'Não definida'}")
    print(f"  - PROXY_CONTAINER_NAME: {os.environ.get('PROXY_CONTAINER_NAME')}")
    print(f"  - PROXY_FILE_PATH: {os.environ.get('PROXY_FILE_PATH')}")
    print(f"  - URL de teste: {test_url}")
    print("="*70)
    
    # Testar a atualização do proxy
    print("\n🔄 Testando conexão com a VPS e atualização do proxy...")
    result = update_vps_proxy(test_url)
    
    if result:
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("A conexão com a VPS e a atualização do proxy funcionaram corretamente.")
    else:
        print("\n❌ TESTE FALHOU!")
        print("Não foi possível conectar à VPS ou atualizar o proxy.")
        print("Verifique os logs acima para mais detalhes sobre o erro.")
    
    print("="*70)

if __name__ == "__main__":
    main()
