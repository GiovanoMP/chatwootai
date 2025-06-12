#!/usr/bin/env python3
"""
Exemplo de uso do adaptador dinâmico do MCP-Chatwoot.
Este script demonstra como descobrir e utilizar ferramentas do Chatwoot dinamicamente.
"""
import traceback

import os
import sys
import json
import logging
from dotenv import load_dotenv
from chatwoot_dynamic_adapter import ChatwootDynamicAdapter

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Cores para saída no terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_info(message):
    """Imprime mensagem informativa"""
    print(f"{YELLOW}ℹ️ {message}{RESET}")

def print_success(message):
    """Imprime mensagem de sucesso"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    """Imprime mensagem de erro"""
    print(f"{RED}❌ {message}{RESET}")

def print_section(title):
    """Imprime título de seção"""
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}== {title}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

def discover_chatwoot_tools():
    """Descobre e exibe as ferramentas disponíveis no MCP-Chatwoot"""
    print_section("DESCOBRINDO FERRAMENTAS DINÂMICAS DO MCP-CHATWOOT")
    
    # URL do MCP-Chatwoot
    chatwoot_url = os.getenv("MCP_CHATWOOT_URL", "http://localhost:8004")
    print_info(f"Conectando ao MCP-Chatwoot em: {chatwoot_url}")
    logging.info(f"URL do MCP-Chatwoot: {chatwoot_url}")
    
    try:
        # Conectar ao MCP-Chatwoot usando o adaptador dinâmico
        adapter = ChatwootDynamicAdapter(base_url=chatwoot_url)
        tools = adapter.tools
        
        print_success(f"Conectado ao MCP-Chatwoot! Ferramentas disponíveis: {len(tools)}")
        print_section("FERRAMENTAS DISPONÍVEIS")
        
        # Exibir detalhes de cada ferramenta
        for i, tool in enumerate(tools, 1):
            print(f"{GREEN}{i}. {tool.name}{RESET}")
            print(f"   {BLUE}Descrição:{RESET} {tool.description.split('\n')[0]}")
            print()
        
        return adapter, tools
    except Exception as e:
        print_error(f"Erro ao conectar ao MCP-Chatwoot: {str(e)}")
        return None, None

def test_tool_execution(adapter, tool_name, **params):
    """Testa a execução de uma ferramenta específica"""
    print_section(f"TESTANDO FERRAMENTA: {tool_name}")
    print_info(f"Parâmetros: {json.dumps(params, indent=2)}")
    
    try:
        # Encontrar a ferramenta pelo nome
        tool = next((t for t in adapter.tools if t.name == tool_name), None)
        if not tool:
            print_error(f"Ferramenta '{tool_name}' não encontrada!")
            return False
        
        # Executar a ferramenta
        print_info(f"Executando {tool_name}...")
        result = tool.func(**params)
        
        print_success("Execução concluída com sucesso!")
        print_section("RESULTADO")
        print(result)
        return True
    except Exception as e:
        print_error(f"Erro ao executar a ferramenta {tool_name}: {str(e)}")
        logging.exception("Erro detalhado:")
        return False

def main():
    """Função principal"""
    print_section("DEMONSTRAÇÃO DO ADAPTADOR DINÂMICO DO MCP-CHATWOOT")
    
    # Configurar logging mais detalhado para depuração
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Iniciando demonstração do adaptador dinâmico do Chatwoot")
    print_info("Iniciando demonstração do adaptador dinâmico do Chatwoot")
    
    try:
        # Descobrir ferramentas do MCP-Chatwoot
        print_info("Tentando descobrir ferramentas do MCP-Chatwoot...")
        adapter, tools = discover_chatwoot_tools()
        
        if not adapter or not tools:
            print_error("Falha ao descobrir ferramentas. Verifique se o MCP-Chatwoot está em execução.")
            return False
            
        # Perguntar ao usuário se deseja testar alguma ferramenta
        print_info("\nDeseja testar alguma ferramenta? (s/n): ")
        choice = input().lower()
        
        if choice == 's':
            # Listar ferramentas novamente para seleção
            print_info("Selecione uma ferramenta pelo número:")
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool.name}")
                
            try:
                tool_idx = int(input("Número da ferramenta: ")) - 1
                if 0 <= tool_idx < len(tools):
                    selected_tool = tools[tool_idx]
                    print_info(f"Ferramenta selecionada: {selected_tool.name}")
                    
                    # Solicitar parâmetros
                    print_info("Insira os parâmetros no formato JSON (ou deixe vazio para nenhum parâmetro):")
                    params_str = input()
                    params = json.loads(params_str) if params_str.strip() else {}
                    
                    # Testar a ferramenta
                    test_tool_execution(adapter, selected_tool.name, **params)
                else:
                    print_error("Número de ferramenta inválido!")
            except ValueError:
                print_error("Entrada inválida!")
            except json.JSONDecodeError:
                print_error("Formato JSON inválido para os parâmetros!")
        
        return True
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        logging.exception("Erro detalhado:")
        return False

if __name__ == "__main__":
    try:
        print("Iniciando script de teste do adaptador dinâmico do MCP-Chatwoot...")
        success = main()
        print("Script concluído.")
    except Exception as e:
        print(f"\n\n❌ ERRO CRÍTICO: {str(e)}")
        print("Stacktrace:")
        traceback.print_exc()
        sys.exit(1)
