#!/bin/bash

# Diretório de origem (onde estamos criando os arquivos)
SRC_DIR="./addons/product_ai_management"

# Diretório de destino (onde o Odoo procura por módulos)
DEST_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons/product_ai_management"

# Criar diretório de destino se não existir
mkdir -p "$DEST_DIR/models"
mkdir -p "$DEST_DIR/views"
mkdir -p "$DEST_DIR/wizards"
mkdir -p "$DEST_DIR/security"
mkdir -p "$DEST_DIR/tests"
mkdir -p "$DEST_DIR/static/description"

# Copiar arquivos
echo "Copiando arquivos para $DEST_DIR..."
cp "$SRC_DIR/__manifest__.py" "$DEST_DIR/"
cp "$SRC_DIR/__init__.py" "$DEST_DIR/"

# Copiar modelos
cp "$SRC_DIR/models/__init__.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/product_template.py" "$DEST_DIR/models/"

# Copiar vistas
cp "$SRC_DIR/views/product_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/menu_views.xml" "$DEST_DIR/views/"

# Copiar wizards
cp "$SRC_DIR/wizards/__init__.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/price_adjustment_wizard.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/price_adjustment_wizard_views.xml" "$DEST_DIR/wizards/"

# Copiar arquivos de segurança
cp "$SRC_DIR/security/ir.model.access.csv" "$DEST_DIR/security/"

# Copiar testes
cp "$SRC_DIR/tests/__init__.py" "$DEST_DIR/tests/"
cp "$SRC_DIR/tests/test_product_ai_management.py" "$DEST_DIR/tests/"

# Definir permissões
echo "Definindo permissões..."
chmod -R 755 "$DEST_DIR"

echo "Instalação concluída!"
echo "Agora você pode atualizar a lista de módulos no Odoo e instalar 'Gerenciamento de Produtos com IA'"

# Criar diretório de logs se não existir
echo "Configurando diretório de logs..."
sudo mkdir -p /var/log/odoo
sudo chown -R $(whoami) /var/log/odoo

# Verificar se o Odoo está rodando como serviço ou Docker
echo "Verificando como reiniciar o Odoo..."
if systemctl is-active --quiet odoo; then
    echo "Reiniciando o serviço Odoo..."
    sudo service odoo restart
elif [ -x "$(command -v docker)" ] && docker ps | grep -q odoo; then
    echo "Reiniciando o container Docker do Odoo..."
    docker restart $(docker ps | grep odoo | awk '{print $1}')
else
    echo "AVISO: Não foi possível detectar como reiniciar o Odoo automaticamente."
    echo "Por favor, reinicie o Odoo manualmente para aplicar as alterações."
fi

echo ""
echo "=== INSTRUÇÕES ADICIONAIS ==="
echo "1. Para atualizar a lista de módulos no Odoo:"
echo "   - Acesse Configurações > Aplicativos > Atualizar Lista de Aplicativos"
echo "   - Busque por 'Gerenciamento de Produtos com IA' e instale o módulo"
echo ""
echo "2. Para verificar os logs do módulo:"
echo "   - Logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log | grep product_ai_management"
echo "   - Logs específicos do módulo: sudo tail -f /var/log/odoo/product_ai_management.log"
echo ""
echo "3. Se encontrar erros durante a instalação:"
echo "   - Verifique os logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log"
echo "   - Desinstale o módulo antes de tentar novamente: sudo rm -rf $DEST_DIR"
