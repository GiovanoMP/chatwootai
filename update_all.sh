#!/bin/bash

# Definir cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando atualização completa dos módulos...${NC}"

# Executar scripts de instalação
echo -e "${YELLOW}Executando script de instalação do módulo ai_credentials_manager...${NC}"
./install_ai_credentials_manager.sh
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Instalação do módulo ai_credentials_manager concluída com sucesso.${NC}"
else
  echo -e "${RED}Falha na instalação do módulo ai_credentials_manager.${NC}"
  exit 1
fi

echo -e "${YELLOW}Executando script de instalação do módulo business_rules...${NC}"
./install_business_rules.sh
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Instalação do módulo business_rules concluída com sucesso.${NC}"
else
  echo -e "${RED}Falha na instalação do módulo business_rules.${NC}"
  exit 1
fi

# Verificar se o usuário tem permissões de sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Este script precisa de permissões de sudo para reiniciar o serviço Odoo.${NC}"
  echo -e "${YELLOW}Por favor, execute os seguintes comandos manualmente:${NC}"
  echo -e "${GREEN}sudo systemctl restart odoo${NC}"
  echo -e "${GREEN}sudo -u odoo /usr/bin/odoo -c /etc/odoo/odoo.conf -d account_1 -u ai_credentials_manager,business_rules --stop-after-init${NC}"
  echo -e "${GREEN}sudo systemctl restart odoo${NC}"
  exit 0
fi

# Reiniciar o serviço Odoo
echo -e "${YELLOW}Reiniciando o serviço Odoo...${NC}"
systemctl restart odoo
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Serviço Odoo reiniciado com sucesso.${NC}"
else
  echo -e "${RED}Falha ao reiniciar o serviço Odoo.${NC}"
  exit 1
fi

# Aguardar o serviço iniciar completamente
echo -e "${YELLOW}Aguardando o serviço iniciar (10 segundos)...${NC}"
sleep 10

# Executar atualização dos módulos via comando odoo-bin
echo -e "${YELLOW}Atualizando módulos via odoo-bin...${NC}"
# Ajuste o caminho do odoo-bin conforme necessário
ODOO_BIN="/usr/bin/odoo"
ODOO_CONF="/etc/odoo/odoo.conf"

if [ -f "$ODOO_BIN" ]; then
  sudo -u odoo $ODOO_BIN -c $ODOO_CONF -d account_1 -u ai_credentials_manager,business_rules --stop-after-init
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Módulos atualizados com sucesso.${NC}"
  else
    echo -e "${RED}Falha ao atualizar os módulos.${NC}"
    exit 1
  fi
else
  echo -e "${RED}Executável do Odoo não encontrado em $ODOO_BIN.${NC}"
  exit 1
fi

# Reiniciar o serviço Odoo novamente
echo -e "${YELLOW}Reiniciando o serviço Odoo novamente...${NC}"
systemctl restart odoo
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Serviço Odoo reiniciado com sucesso.${NC}"
else
  echo -e "${RED}Falha ao reiniciar o serviço Odoo.${NC}"
  exit 1
fi

echo -e "${GREEN}Atualização completa concluída com sucesso!${NC}"
echo -e "${YELLOW}Agora você pode acessar o Odoo e verificar se as alterações foram aplicadas.${NC}"
