#!/usr/bin/env python3
"""
Check database tables script - Verifica e lista as tabelas existentes no banco de dados.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Adicionar o diretório raiz do projeto ao sys.path para poder importar os módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar após configurar o sys.path
from src.services.data.data_service_hub import DataServiceHub

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Função principal que verifica as tabelas no banco de dados.
    """
    # Carregar variáveis de ambiente
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
    print(f"Carregando variáveis de ambiente de: {env_path}")

    # Criar conexão com banco de dados
    hub = DataServiceHub()

    try:
        # Verificar tabelas relacionadas a conversações
        result = hub.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%conversation%';",
            {}
        )
        
        print("\nTabelas relacionadas a conversação:")
        if result and len(result) > 0:
            for row in result:
                print(f"- {row['table_name']}")
        else:
            print("Nenhuma tabela relacionada a conversação encontrada.")
            
        # Verificar todas as tabelas
        result = hub.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';",
            {}
        )
        
        print("\nTodas as tabelas:")
        if result and len(result) > 0:
            for row in result:
                print(f"- {row['table_name']}")
        else:
            print("Nenhuma tabela encontrada.")
            
    except Exception as e:
        logger.error(f"Erro ao verificar tabelas: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
