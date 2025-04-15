#!/bin/bash

# Definir cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando atualização dos módulos...${NC}"

# Verificar se o usuário tem permissões de sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Este script precisa ser executado como root ou com sudo.${NC}"
  exit 1
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

# Limpar o cache do Odoo
echo -e "${YELLOW}Limpando o cache do Odoo...${NC}"
# Diretório de cache do Odoo
ODOO_CACHE_DIR="/var/cache/odoo"
if [ -d "$ODOO_CACHE_DIR" ]; then
  rm -rf $ODOO_CACHE_DIR/*
  echo -e "${GREEN}Cache do Odoo limpo com sucesso.${NC}"
else
  echo -e "${YELLOW}Diretório de cache do Odoo não encontrado. Pulando esta etapa.${NC}"
fi

# Executar atualização dos módulos via comando odoo-bin
echo -e "${YELLOW}Atualizando módulos via odoo-bin...${NC}"
# Ajuste o caminho do odoo-bin conforme necessário
ODOO_BIN="/usr/bin/odoo"
ODOO_CONF="/etc/odoo/odoo.conf"

if [ -f "$ODOO_BIN" ]; then
  $ODOO_BIN -c $ODOO_CONF -d account_1 -u ai_credentials_manager,business_rules --stop-after-init
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

echo -e "${GREEN}Atualização concluída com sucesso!${NC}"
echo -e "${YELLOW}Agora você pode acessar o Odoo e verificar se as alterações foram aplicadas.${NC}"
