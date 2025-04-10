#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório do módulo
MODULE_DIR="./addons/semantic_product_inline"

# Função para exibir mensagens
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função para verificar se um comando foi bem-sucedido
check_result() {
    if [ $1 -eq 0 ]; then
        log "$2"
        return 0
    else
        error "$3"
        return 1
    fi
}

# Título
echo "============================================="
echo "  Teste do Módulo Descrições Inteligentes de Produtos"
echo "============================================="
echo ""

# 1. Verificar estrutura de diretórios
log "Verificando estrutura de diretórios..."
DIRS_TO_CHECK=("$MODULE_DIR" "$MODULE_DIR/models" "$MODULE_DIR/views")
DIRS_OK=true

for dir in "${DIRS_TO_CHECK[@]}"; do
    if [ -d "$dir" ]; then
        log "✓ Diretório $dir existe"
    else
        error "✗ Diretório $dir não existe"
        DIRS_OK=false
    fi
done

if [ "$DIRS_OK" = true ]; then
    log "Estrutura de diretórios OK"
else
    error "Problemas na estrutura de diretórios"
fi

echo ""

# 2. Verificar arquivos obrigatórios
log "Verificando arquivos obrigatórios..."
FILES_TO_CHECK=(
    "$MODULE_DIR/__init__.py"
    "$MODULE_DIR/__manifest__.py"
    "$MODULE_DIR/models/__init__.py"
    "$MODULE_DIR/models/product_template.py"
    "$MODULE_DIR/views/product_template_views.xml"
)
FILES_OK=true

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        log "✓ Arquivo $file existe"
    else
        error "✗ Arquivo $file não existe"
        FILES_OK=false
    fi
done

if [ "$FILES_OK" = true ]; then
    log "Arquivos obrigatórios OK"
else
    error "Arquivos obrigatórios ausentes"
fi

echo ""

# 3. Verificar sintaxe Python
log "Verificando sintaxe Python..."
PYTHON_FILES=(
    "$MODULE_DIR/__init__.py"
    "$MODULE_DIR/models/__init__.py"
    "$MODULE_DIR/models/product_template.py"
)
PYTHON_OK=true

for file in "${PYTHON_FILES[@]}"; do
    python3 -m py_compile "$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        log "✓ Sintaxe Python OK em $file"
    else
        error "✗ Erro de sintaxe Python em $file"
        PYTHON_OK=false
    fi
done

if [ "$PYTHON_OK" = true ]; then
    log "Sintaxe Python OK em todos os arquivos"
else
    error "Erros de sintaxe Python encontrados"
fi

echo ""

# 4. Verificar XML
log "Verificando sintaxe XML..."
XML_FILES=(
    "$MODULE_DIR/views/product_template_views.xml"
)
XML_OK=true

for file in "${XML_FILES[@]}"; do
    python3 validate_xml.py "$file" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        log "✓ Sintaxe XML OK em $file"
    else
        error "✗ Erro de sintaxe XML em $file"
        XML_OK=false
    fi
done

if [ "$XML_OK" = true ]; then
    log "Sintaxe XML OK em todos os arquivos"
else
    error "Erros de sintaxe XML encontrados"
fi

echo ""

# 5. Verificar dependências
log "Verificando dependências..."
DEPENDS=$(grep -o "'[^']*'" "$MODULE_DIR/__manifest__.py" | grep -A10 "'depends'" | tail -n +2 | grep -v "]" | tr -d "', ")
log "Dependências declaradas: $DEPENDS"

echo ""

# 6. Resumo
echo "============================================="
echo "  Resumo dos Testes"
echo "============================================="

if [ "$DIRS_OK" = true ] && [ "$FILES_OK" = true ] && [ "$PYTHON_OK" = true ] && [ "$XML_OK" = true ]; then
    log "✅ Todos os testes passaram! O módulo parece estar pronto para implantação."
    echo ""
    log "Para implantar o módulo, execute:"
    echo "  ./deploy_module.sh"
else
    error "❌ Alguns testes falharam. Corrija os problemas antes de implantar o módulo."
fi

echo ""
