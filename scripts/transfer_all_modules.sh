#!/bin/bash

echo "Transferindo todos os módulos personalizados..."

# Tornar todos os scripts executáveis
chmod +x /home/giovano/Projetos/ai_stack/scripts/transfer_*.sh

# Executar cada script de transferência
/home/giovano/Projetos/ai_stack/scripts/transfer_company_services.sh
/home/giovano/Projetos/ai_stack/scripts/transfer_business_rules2.sh
/home/giovano/Projetos/ai_stack/scripts/transfer_ai_agent_odoo.sh
/home/giovano/Projetos/ai_stack/scripts/transfer_llm_mcp.sh
/home/giovano/Projetos/ai_stack/scripts/transfer_product_ai_mass_management.sh
/home/giovano/Projetos/ai_stack/scripts/transfer_semantic_product_description.sh

echo "Todos os módulos foram transferidos com sucesso!"
echo "Não esqueça de reiniciar o servidor Odoo para aplicar as alterações."
echo "Para reiniciar o servidor Odoo, acesse o diretório do docker-compose e execute: docker-compose restart odoo"

exit 0
