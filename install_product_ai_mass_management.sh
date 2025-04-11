#!/bin/bash

# Diretório de origem (onde estamos criando os arquivos)
SRC_DIR="./addons/product_ai_mass_management"

# Diretório de destino (onde o Odoo procura por módulos)
DEST_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons/product_ai_mass_management"

# Criar diretório de destino se não existir
mkdir -p "$DEST_DIR/models"
mkdir -p "$DEST_DIR/views"
mkdir -p "$DEST_DIR/wizards"
mkdir -p "$DEST_DIR/security"

# Verificar se os diretórios foram criados
echo "Verificando diretórios criados:"
ls -la "$DEST_DIR"

# Copiar arquivos
echo "Copiando arquivos para $DEST_DIR..."
cp "$SRC_DIR/__manifest__.py" "$DEST_DIR/"
cp "$SRC_DIR/__init__.py" "$DEST_DIR/"
cp "$SRC_DIR/models/__init__.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/product_template.py" "$DEST_DIR/models/"
cp "$SRC_DIR/views/product_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/menu_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/wizards/__init__.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/adjust_ai_prices_wizard.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/adjust_ai_prices_wizard_views.xml" "$DEST_DIR/wizards/"
cp "$SRC_DIR/security/ir.model.access.csv" "$DEST_DIR/security/"
cp "$SRC_DIR/security/security.xml" "$DEST_DIR/security/"

# Verificar se os arquivos foram copiados
echo "Verificando arquivos copiados:"
ls -la "$DEST_DIR/security/"

# Definir permissões
echo "Definindo permissões..."
chmod -R 755 "$DEST_DIR"

echo "Instalação concluída!"
echo "Agora você pode atualizar a lista de módulos no Odoo e instalar 'Gerenciamento em Massa de Produtos no Sistema de IA'"

# Reiniciar o serviço Odoo para limpar o cache
echo "Reiniciando o serviço Odoo..."
sudo service odoo restart

echo ""
echo "=== INSTRUÇÕES ADICIONAIS ==="
echo "1. Para atualizar a lista de módulos no Odoo:"
echo "   - Acesse Configurações > Aplicativos > Atualizar Lista de Aplicativos"
echo "   - Busque por 'Gerenciamento em Massa' e instale o módulo"
echo ""
echo "2. Para verificar os logs do módulo:"
echo "   - Logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log | grep product_ai_mass"
echo ""
echo "3. Se encontrar erros durante a instalação:"
echo "   - Verifique os logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log"
echo "   - Desinstale o módulo antes de tentar novamente: sudo rm -rf $DEST_DIR"
