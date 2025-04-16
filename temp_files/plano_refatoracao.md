Arquitetura do Sistema
O projeto consiste em dois componentes principais que atualmente funcionam como sistemas separados:

Sistema de Webhook (src/webhook/)
Implementado em FastAPI
Recebe e processa webhooks do Chatwoot (mensagens de chat)
Processa eventos de sincronização de credenciais
Utiliza uma arquitetura hub-and-spoke para encaminhar mensagens para o sistema de IA
Está exposto à internet via ngrok
API Odoo (odoo_api/)
Implementado em FastAPI
Fornece endpoints para interação com módulos Odoo
Inclui endpoints específicos para cada módulo (business_rules, product_management, etc.)
Contém o endpoint /api/v1/business-rules/sync que o módulo Odoo precisa acessar
Não está atualmente exposto à internet
Problema Atual
O módulo Odoo business_rules está tentando acessar o endpoint /api/v1/business-rules/sync através do URL do webhook (ngrok), mas este endpoint está implementado no sistema odoo_api, não no sistema de webhook. Isso resulta em erros 404 (Not Found).

Os logs mostram que:

O webhook está processando corretamente mensagens do Chatwoot
O webhook está processando corretamente eventos de sincronização de credenciais
Mas não está encaminhando solicitações para endpoints da API Odoo
Tentativa Inicial de Solução
Começamos a implementar um proxy reverso no servidor webhook para encaminhar solicitações que começam com /api/v1/ para o servidor odoo_api. Embora esta solução possa funcionar, foi identificado que não é a abordagem mais profissional e sustentável a longo prazo.

Solução Proposta
Após análise, decidimos implementar uma Arquitetura de Servidor Unificado com Rotas Bem Definidas. Esta abordagem unifica os dois servidores em um único aplicativo FastAPI, mantendo a separação lógica entre os diferentes tipos de endpoints.

Benefícios da Solução Proposta
Simplicidade: Um único servidor para gerenciar e implantar
Organização: Código bem estruturado com responsabilidades claras
Manutenção: Fácil de manter e estender
Profissionalismo: Arquitetura limpa e bem definida
Escalabilidade: Pode evoluir para uma arquitetura de microserviços no futuro, se necessário



Plano de Implementação
1. Refatoração do Código
1.1 Reorganizar o Código do Webhook
Mover as rotas do webhook para um módulo separado (src/webhook/routes.py)
Extrair a lógica de inicialização para um módulo separado (src/webhook/init.py)
Manter a lógica de processamento no webhook_handler.py
1.2 Reorganizar o Código da API Odoo
Verificar se as rotas já estão bem organizadas em módulos separados
Garantir que cada módulo tenha seu próprio roteador FastAPI
2. Criar o Servidor Unificado
2.1 Implementar o Novo Arquivo Principal
Criar um novo arquivo main.py na raiz do projeto
Incluir os roteadores de ambos os sistemas
Configurar middleware, eventos de inicialização, etc.

# main.py (exemplo)
from fastapi import FastAPI
from src.webhook.routes import router as webhook_router
from odoo_api.modules.business_rules.routes import router as business_rules_router
from odoo_api.modules.product_management.routes import router as product_management_router
# Importar outros roteadores conforme necessário

app = FastAPI(title="Sistema Integrado Odoo-AI")

# Configurar middleware, eventos, etc.

# Incluir roteadores
app.include_router(webhook_router, prefix="/webhook")
app.include_router(business_rules_router, prefix="/api/v1")
app.include_router(product_management_router, prefix="/api/v1")
# Incluir outros roteadores conforme necessário



2.2 Configurar Ambiente e Dependências
Unificar as dependências dos dois sistemas
Garantir que variáveis de ambiente sejam carregadas corretamente
Configurar logging unificado
3. Atualizar Configurações e Documentação
3.1 Atualizar Configurações de Implantação
Atualizar scripts de inicialização
Configurar ngrok para apontar para o novo servidor unificado
Atualizar configurações do módulo Odoo para usar o novo endpoint
3.2 Atualizar Documentação
Documentar a nova arquitetura em @ARCHITECTURE.md
Atualizar instruções de implantação
Documentar fluxos de comunicação entre componentes
Documentos Importantes para Referência
1. Estrutura do Projeto
 src/webhook/server.py: Implementação atual do servidor webhook
src/webhook/webhook_handler.py: Lógica de processamento de webhooks
odoo_api/main.py: Implementação atual do servidor API Odoo
odoo_api/modules/business_rules/routes.py: Rotas para o módulo business_rules
odoo_api/modules/business_rules/services.py: Serviços para o módulo business_rules
2. Endpoints Críticos
/webhook: Recebe webhooks do Chatwoot
/api/v1/business-rules/sync: Endpoint para sincronização de regras de negócio
3. Fluxos de Comunicação
Chatwoot → Webhook → HubCrew → Processamento de mensagens
Módulo Odoo → API Odoo → Processamento de regras de negócio
4. Configurações
O webhook está configurado para rodar na porta 8000
A API Odoo está configurada para rodar na porta 8001 (mas não está sendo iniciada automaticamente)
O ngrok está configurado para expor a porta 8000
Considerações Adicionais
Segurança
Implementar autenticação para endpoints da API
Verificar tokens de acesso para solicitações do módulo Odoo
Considerar a implementação de rate limiting
Monitoramento e Logging
Implementar logging unificado
Considerar a adição de métricas de desempenho
Implementar rastreamento de solicitações entre componentes
Escalabilidade Futura
A arquitetura unificada pode evoluir para microserviços no futuro
Considerar a implementação de um API Gateway real (como Kong ou Traefik)
Planejar para containerização com Docker
Próximos Passos Imediatos
Implementar a refatoração do código do webhook
Implementar a refatoração do código da API Odoo
Criar o servidor unificado
Testar a integração com o módulo Odoo
Atualizar a documentação