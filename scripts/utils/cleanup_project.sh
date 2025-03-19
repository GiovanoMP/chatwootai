#!/bin/bash

# Script para limpar arquivos duplicados e obsoletos do projeto
# Este script deve ser executado após confirmar que a nova organização do projeto está funcionando corretamente

# Cores para saída
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Diretório base do projeto
PROJECT_DIR="$(pwd)"

echo -e "${YELLOW}Iniciando limpeza do projeto...${NC}"
echo -e "${YELLOW}Diretório do projeto: ${PROJECT_DIR}${NC}"

# Função para confirmar ação
confirm() {
    read -p "Deseja continuar? (s/n): " choice
    case "$choice" in 
        s|S ) return 0;;
        * ) return 1;;
    esac
}

# 1. Remover arquivos de webhook da raiz
echo -e "${YELLOW}1. Removendo arquivos de webhook da raiz do projeto...${NC}"
echo "Os seguintes arquivos serão removidos:"
echo "- webhook_forwarder.py"
echo "- webhook_forwarder_corrected.py"
echo "- webhook_test_server.py"
echo "- test_webhook_server.py"
echo "- simple_webhook.py (já foi copiado para o diretório webhook/)"

if confirm; then
    rm -f "${PROJECT_DIR}/webhook_forwarder.py"
    rm -f "${PROJECT_DIR}/webhook_forwarder_corrected.py"
    rm -f "${PROJECT_DIR}/webhook_test_server.py"
    rm -f "${PROJECT_DIR}/test_webhook_server.py"
    rm -f "${PROJECT_DIR}/simple_webhook.py"
    echo -e "${GREEN}Arquivos de webhook removidos com sucesso.${NC}"
else
    echo -e "${RED}Operação cancelada.${NC}"
fi

# 2. Remover arquivos de configuração da raiz
echo -e "${YELLOW}2. Removendo arquivos de configuração da raiz do projeto...${NC}"
echo "Os seguintes arquivos serão removidos (já foram copiados para o diretório config/):"
echo "- .env.temp"
echo "- .env.chatwoot.example"
echo "- docker-compose.yml"
echo "- docker-stack.yml"
echo "- docker-swarm.yml"
echo "- Dockerfile"
echo "- Dockerfile.api"

if confirm; then
    # Não remover o .env principal, apenas os arquivos de exemplo
    rm -f "${PROJECT_DIR}/.env.temp"
    rm -f "${PROJECT_DIR}/.env.chatwoot.example"
    rm -f "${PROJECT_DIR}/docker-compose.yml"
    rm -f "${PROJECT_DIR}/docker-stack.yml"
    rm -f "${PROJECT_DIR}/docker-swarm.yml"
    rm -f "${PROJECT_DIR}/Dockerfile"
    rm -f "${PROJECT_DIR}/Dockerfile.api"
    echo -e "${GREEN}Arquivos de configuração removidos com sucesso.${NC}"
else
    echo -e "${RED}Operação cancelada.${NC}"
fi

# 3. Remover documentação obsoleta
echo -e "${YELLOW}3. Removendo documentação obsoleta...${NC}"
echo "O seguinte arquivo será removido (já foi consolidado em webhook_integration.md):"
echo "- README.webhook.md"

if confirm; then
    rm -f "${PROJECT_DIR}/README.webhook.md"
    echo -e "${GREEN}Documentação obsoleta removida com sucesso.${NC}"
else
    echo -e "${RED}Operação cancelada.${NC}"
fi

# 4. Remover scripts duplicados
echo -e "${YELLOW}4. Removendo scripts duplicados...${NC}"
echo "Os scripts já foram organizados em subdiretórios. Deseja remover os scripts originais?"

if confirm; then
    # Remover apenas os scripts que foram copiados para subdiretórios
    find "${PROJECT_DIR}/scripts" -maxdepth 1 -type f -not -name "README.md" -exec rm -f {} \;
    echo -e "${GREEN}Scripts duplicados removidos com sucesso.${NC}"
else
    echo -e "${RED}Operação cancelada.${NC}"
fi

echo -e "${GREEN}Limpeza concluída com sucesso!${NC}"
echo "O projeto agora está organizado com a seguinte estrutura:"
echo "- config/ - Arquivos de configuração"
echo "- docs/ - Documentação"
echo "- scripts/ - Scripts utilitários"
echo "- src/ - Código-fonte principal"
echo "- webhook/ - Implementações de webhook"

echo -e "${YELLOW}Nota: Certifique-se de atualizar quaisquer referências a caminhos de arquivo em seu código.${NC}"
