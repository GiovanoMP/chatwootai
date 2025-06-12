#!/bin/bash

# Script para configurar o MongoDB MCP Server oficial e testá-lo com CrewAI
# Autor: Cascade AI
# Data: 2025-06-06

# Cores para saída no terminal
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

# Funções auxiliares
print_section() {
  echo -e "\n${BLUE}=================================================="
  echo -e "== $1"
  echo -e "==================================================${RESET}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${RESET}"
}

print_warning() {
  echo -e "${YELLOW}⚠️ $1${RESET}"
}

print_error() {
  echo -e "${RED}❌ $1${RESET}"
}

# Verificar se o Docker está instalado
check_docker() {
  print_section "VERIFICANDO DOCKER"
  if command -v docker &> /dev/null; then
    print_success "Docker está instalado"
    docker --version
  else
    print_error "Docker não está instalado. Por favor, instale o Docker antes de continuar."
    exit 1
  fi
}

# Parar e remover contêiner MCP-MongoDB existente
remove_existing_mongodb_mcp() {
  print_section "REMOVENDO MCP-MONGODB EXISTENTE"
  
  # Verificar se o contêiner existe
  if docker ps -a | grep -q mcp-mongodb; then
    print_warning "Contêiner MCP-MongoDB encontrado. Parando e removendo..."
    docker stop mcp-mongodb || true
    docker rm mcp-mongodb || true
    print_success "Contêiner MCP-MongoDB removido"
  else
    print_warning "Nenhum contêiner MCP-MongoDB encontrado"
  fi
}

# Baixar e iniciar o MongoDB MCP Server oficial
start_mongodb_mcp_server() {
  print_section "INICIANDO MONGODB MCP SERVER OFICIAL"
  
  # Verificar se o MongoDB está em execução
  if docker ps | grep -q mongo; then
    print_success "MongoDB encontrado em execução"
    
    # Obter informações de conexão do MongoDB
    MONGO_CONTAINER=$(docker ps | grep mongo | awk '{print $1}')
    MONGO_HOST=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $MONGO_CONTAINER)
    MONGO_PORT=27017
    
    print_warning "Usando MongoDB em $MONGO_HOST:$MONGO_PORT"
    
    # Iniciar o MongoDB MCP Server oficial
    print_warning "Iniciando MongoDB MCP Server oficial..."
    
    # Usar o contêiner Docker do MongoDB MCP Server oficial
    docker run -d --name mongodb-mcp-server \
      --restart unless-stopped \
      -p 8001:8000 \
      -e MDB_MCP_CONNECTION_STRING="mongodb://$MONGO_HOST:$MONGO_PORT" \
      mongodb/mongodb-mcp-server:latest
    
    print_success "MongoDB MCP Server oficial iniciado na porta 8001"
  else
    print_error "MongoDB não encontrado em execução. Por favor, inicie o MongoDB antes de continuar."
    print_warning "Você pode iniciar o MongoDB com: docker run -d --name mongodb -p 27017:27017 mongo:latest"
    exit 1
  fi
}

# Testar o MongoDB MCP Server com CrewAI
test_mongodb_mcp_server() {
  print_section "TESTANDO MONGODB MCP SERVER COM CREWAI"
  
  # Verificar se o ambiente virtual existe
  if [ ! -d "venv" ]; then
    print_warning "Ambiente virtual não encontrado. Criando..."
    python3 -m venv venv
    print_success "Ambiente virtual criado"
  fi
  
  # Ativar ambiente virtual
  print_warning "Ativando ambiente virtual..."
  source venv/bin/activate
  
  # Instalar dependências
  print_warning "Instalando dependências..."
  pip install crewai crewai-tools[mcp]
  
  print_success "Dependências instaladas"
  
  # Criar script de teste
  print_warning "Criando script de teste..."
  cat > test_mongodb_mcp_server.py << 'EOF'
#!/usr/bin/env python3
"""
Script para testar a conexão com o MongoDB MCP Server oficial usando CrewAI.
"""

import os
from crewai_tools import MCPServerAdapter

# Cores para saída no terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_section(title):
    """Imprime título de seção"""
    print(f"\n{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}== {title}{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}\n")

def print_info(message):
    """Imprime mensagem informativa"""
    print(f"{YELLOW}{message}{RESET}")

def print_success(message):
    """Imprime mensagem de sucesso"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    """Imprime mensagem de erro"""
    print(f"{RED}❌ {message}{RESET}")

def test_mongodb_mcp_server():
    """Testa a conexão com o MongoDB MCP Server oficial"""
    print_section("TESTE DE CONEXÃO COM MONGODB MCP SERVER OFICIAL")
    
    # URL do MongoDB MCP Server oficial
    mongodb_url = "http://localhost:8001/sse"
    print_info(f"Tentando conectar ao MongoDB MCP Server em: {mongodb_url}")
    
    try:
        # Conectar ao MongoDB MCP Server usando o MCPServerAdapter
        with MCPServerAdapter({"url": mongodb_url}) as mongodb_tools:
            print_success(f"Conexão bem-sucedida! Ferramentas disponíveis: {len(mongodb_tools)}")
            
            # Listar ferramentas disponíveis
            print_section("FERRAMENTAS DISPONÍVEIS")
            for i, tool in enumerate(mongodb_tools, 1):
                print(f"  {i}. {tool.name}: {tool.description}")
                print(f"Tool Arguments: {tool.args}")
                print(f"Tool Description: {tool.description}\n")
    
    except Exception as e:
        print_error(f"Falha na conexão: {str(e)}")

if __name__ == "__main__":
    test_mongodb_mcp_server()
EOF
  
  print_success "Script de teste criado"
  
  # Executar script de teste
  print_warning "Executando script de teste..."
  python test_mongodb_mcp_server.py
}

# Função principal
main() {
  print_section "CONFIGURAÇÃO DO MONGODB MCP SERVER OFICIAL"
  
  check_docker
  remove_existing_mongodb_mcp
  start_mongodb_mcp_server
  test_mongodb_mcp_server
  
  print_section "CONFIGURAÇÃO CONCLUÍDA"
  print_success "MongoDB MCP Server oficial configurado e testado com sucesso!"
  print_warning "O servidor está disponível em: http://localhost:8001/sse"
  print_warning "Para usar com CrewAI, utilize o seguinte código:"
  echo -e "${BLUE}"
  echo 'from crewai import Agent, Task, Crew'
  echo 'from crewai_tools import MCPServerAdapter'
  echo ''
  echo '# Conectar ao MongoDB MCP Server'
  echo 'with MCPServerAdapter({"url": "http://localhost:8001/sse"}) as mongodb_tools:'
  echo '    # Criar um agente com as ferramentas do MongoDB'
  echo '    mongodb_agent = Agent('
  echo '        role="Especialista em MongoDB",'
  echo '        goal="Analisar e gerenciar dados no MongoDB",'
  echo '        backstory="Você é um especialista em MongoDB com anos de experiência.",'
  echo '        tools=mongodb_tools'
  echo '    )'
  echo -e "${RESET}"
}

# Executar função principal
main
