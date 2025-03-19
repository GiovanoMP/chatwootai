#!/usr/bin/env python3
"""
Script para atualizar e verificar as conexões com os serviços,
garantindo que as variáveis de ambiente corretas sejam usadas.
"""

import os
import sys
import redis
import requests
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Forçar o recarregamento das variáveis de ambiente
print("Recarregando variáveis de ambiente...")
dotenv_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path, override=True)
print(f"Variáveis de ambiente recarregadas de: {dotenv_path}")

# Importar o serviço de dados após recarregar as variáveis de ambiente
from services.data.data_service_hub import DataServiceHub

class ConnectionReset:
    """Classe para redefinir e verificar conexões com serviços."""
    
    def __init__(self):
        """Inicializa o reset de conexões."""
        print("Inicializando reset de conexões...")
        self.hub = None
        
        # Verificar e corrigir as variáveis de ambiente
        self.verify_and_fix_env_vars()
        
        # Recarregar as variáveis de ambiente para garantir que as alterações sejam aplicadas
        print("Recarregando variáveis de ambiente após correções...")
        load_dotenv(dotenv_path, override=True)
        
        # Inicializar o hub depois de corrigir as variáveis de ambiente
        self.hub = DataServiceHub()
    
    def verify_and_fix_env_vars(self):
        """Verifica e corrige as variáveis de ambiente."""
        print("\n===== Verificando variáveis de ambiente =====\n")
        
        # Verificar variáveis do Redis
        redis_url = os.environ.get('REDIS_URL', '')
        redis_host = os.environ.get('REDIS_HOST', '')
        redis_port = os.environ.get('REDIS_PORT', '')
        
        print(f"Redis configurações atuais:")
        print(f"  REDIS_URL: {redis_url}")
        print(f"  REDIS_HOST: {redis_host}")
        print(f"  REDIS_PORT: {redis_port}")
        
        # Verificar variáveis do Qdrant
        qdrant_url = os.environ.get('QDRANT_URL', '')
        print(f"Qdrant configurações atuais:")
        print(f"  QDRANT_URL: {qdrant_url}")
        
        # Verificar se há inconsistências no Redis
        if "172.24.0.5" in redis_url and redis_host == "172.24.0.3":
            print("\n⚠️ Inconsistência detectada: REDIS_URL contém IP 172.24.0.5 mas REDIS_HOST é 172.24.0.3")
            print("   Corrigindo REDIS_URL para usar o mesmo IP que REDIS_HOST...")
            self.update_env_var('REDIS_URL', f"redis://{redis_host}:{redis_port}/0")
        
        # Verificar inconsistências no Qdrant
        if "qdrant" in qdrant_url:
            print("\n⚠️ Inconsistência detectada: QDRANT_URL usa nome de host 'qdrant' em vez de IP")
            print("   Corrigindo QDRANT_URL para usar o IP 172.24.0.4...")
            self.update_env_var('QDRANT_URL', 'http://172.24.0.4:6333')
    
    def update_env_var(self, var_name, new_value):
        """Atualiza uma variável de ambiente no arquivo .env."""
        try:
            env_file_path = dotenv_path
            
            # Ler o conteúdo atual do arquivo .env
            with open(env_file_path, 'r') as file:
                lines = file.readlines()
            
            # Atualizar a variável
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{var_name}="):
                    lines[i] = f"{var_name}={new_value}\n"
                    updated = True
                    break
            
            # Se a variável não existir, adicione-a
            if not updated:
                lines.append(f"{var_name}={new_value}\n")
            
            # Escrever as alterações de volta no arquivo
            with open(env_file_path, 'w') as file:
                file.writelines(lines)
            
            # Atualizar também a variável de ambiente no processo atual
            os.environ[var_name] = new_value
            
            print(f"✅ Variável {var_name} atualizada para {new_value}")
            return True
        except Exception as e:
            print(f"❌ Erro ao atualizar variável {var_name}: {str(e)}")
            return False
    
    def test_redis_connection(self):
        """Testa a conexão com o Redis."""
        print("\n===== Testando conexão com Redis =====\n")
        
        redis_host = os.environ.get('REDIS_HOST', '')
        redis_port = os.environ.get('REDIS_PORT', '')
        redis_db = os.environ.get('REDIS_DB', '0')
        
        try:
            # Tentar conectar diretamente sem usar o hub
            client = redis.Redis(
                host=redis_host,
                port=int(redis_port),
                db=int(redis_db),
                socket_timeout=5,
                decode_responses=True
            )
            
            client.ping()
            client.set('test_reset_key', 'Conexão restabelecida com sucesso!')
            value = client.get('test_reset_key')
            
            print(f"✅ Conexão direta com Redis bem-sucedida: {redis_host}:{redis_port}")
            print(f"   Teste SET/GET: {value}")
            
            # Verificar se o hub tem uma conexão Redis válida
            if self.hub and hasattr(self.hub, 'redis_client') and self.hub.redis_client:
                try:
                    self.hub.redis_client.ping()
                    self.hub.redis_client.set('test_hub_key', 'Conexão via Hub restabelecida!')
                    hub_value = self.hub.redis_client.get('test_hub_key')
                    print(f"✅ Conexão Redis via Hub bem-sucedida")
                    print(f"   Teste SET/GET via Hub: {hub_value}")
                except Exception as e:
                    print(f"❌ Erro na conexão Redis via Hub: {str(e)}")
                    print("   Reinicializando conexão Redis no Hub...")
                    self.hub._redis_client = client
                    print("   Conexão Redis no Hub redefinida.")
            else:
                print("❌ O Hub não tem uma conexão Redis inicializada")
                if self.hub:
                    print("   Definindo conexão Redis no Hub...")
                    self.hub._redis_client = client
                    print("   Conexão Redis adicionada ao Hub.")
            
            return True
        except Exception as e:
            print(f"❌ Erro na conexão direta com Redis: {str(e)}")
            return False
    
    def test_qdrant_connection(self):
        """Testa a conexão com o Qdrant."""
        print("\n===== Testando conexão com Qdrant =====\n")
        
        qdrant_url = os.environ.get('QDRANT_URL', '')
        
        try:
            # Verificar se a URL é válida
            if not qdrant_url or "qdrant" in qdrant_url:
                print(f"⚠️ URL do Qdrant inválida: {qdrant_url}")
                qdrant_url = 'http://172.24.0.4:6333'
                print(f"   Usando URL alternativa: {qdrant_url}")
                self.update_env_var('QDRANT_URL', qdrant_url)
            
            # Testar a conexão
            response = requests.get(f"{qdrant_url}/collections", timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Conexão com Qdrant bem-sucedida: {qdrant_url}")
                collections = response.json()
                
                if 'result' in collections and 'collections' in collections['result']:
                    collections_list = collections['result']['collections']
                    if collections_list:
                        print(f"   Coleções encontradas: {len(collections_list)}")
                    else:
                        print("   Nenhuma coleção encontrada.")
                
                return True
            else:
                print(f"❌ Erro na conexão com Qdrant: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro na conexão com Qdrant: {str(e)}")
            return False
    
    def reset_connections(self):
        """Reinicializa todas as conexões do sistema."""
        print("\n===== Resetando conexões do sistema =====\n")
        
        redis_success = self.test_redis_connection()
        qdrant_success = self.test_qdrant_connection()
        
        # Força a reinicialização do hub se necessário
        if not redis_success or not qdrant_success:
            print("\nReinicializando o DataServiceHub para aplicar as alterações...")
            self.hub = None
            time.sleep(1)  # Pequena pausa para limpar conexões
            self.hub = DataServiceHub()
            
            # Testar novamente após a reinicialização
            print("\n===== Verificando conexões após reinicialização =====")
            redis_success = self.test_redis_connection()
            qdrant_success = self.test_qdrant_connection()
        
        print("\n===== Resumo das conexões =====")
        print(f"Redis: {'✅ Conectado' if redis_success else '❌ Falha'}")
        print(f"Qdrant: {'✅ Conectado' if qdrant_success else '❌ Falha'}")
        
        if redis_success and qdrant_success:
            print("\n✅ Todas as conexões foram reconfiguradas com sucesso!")
            return True
        else:
            print("\n⚠️ Alguns serviços ainda apresentam falhas de conexão.")
            return False

def main():
    """Função principal."""
    print("\n" + "=" * 80)
    print("REINICIALIZAÇÃO DE CONEXÕES DO SISTEMA")
    print("=" * 80)
    
    reset = ConnectionReset()
    success = reset.reset_connections()
    
    if success:
        print("\nSistema pronto para uso! 👍")
        sys.exit(0)
    else:
        print("\nAlgumas conexões ainda precisam ser corrigidas. Verifique as configurações manualmente. 🔧")
        sys.exit(1)

if __name__ == "__main__":
    main()
