# CrewAI para ChatwootAI

Este diretório contém a implementação das crews especializadas para o sistema ChatwootAI, utilizando o framework CrewAI e o protocolo MCP (Model Context Protocol).

## Estrutura do Projeto

```
crewai/
├── api.py                 # API principal que recebe webhooks e orquestra as crews
├── requirements.txt       # Dependências do projeto
├── Dockerfile             # Configuração para containerização
├── whatsapp_crew/         # Crew especializada para WhatsApp
│   └── main.py            # Implementação da WhatsAppCrew
├── facebook_crew/         # Crew especializada para Facebook (futura implementação)
└── email_crew/            # Crew especializada para Email (futura implementação)
```

## Arquitetura

O sistema utiliza uma arquitetura baseada em agentes especializados, organizados em crews por canal de comunicação. Cada crew é responsável por processar mensagens recebidas de um canal específico (WhatsApp, Facebook, Email, etc.) e gerar respostas apropriadas.

### Componentes Principais

1. **API RESTful**: Ponto de entrada para webhooks do Chatwoot, distribui mensagens para as crews apropriadas.

2. **Crews Especializadas**: Conjuntos de agentes organizados por canal de comunicação.

3. **Agentes Especializados**:
   - **Agente de Intenção**: Identifica a intenção do cliente
   - **Agente de Produtos**: Especialista em informações sobre produtos
   - **Agente de Suporte**: Especialista em resolver problemas técnicos
   - **Agente de Finalização**: Formata a resposta final

4. **Integração MCP**:
   - **MCP-MongoDB**: Acesso a configurações da empresa
   - **MCP-Qdrant**: Busca semântica de produtos e procedimentos
   - **MCP-Odoo**: Consultas em tempo real ao ERP

## Fluxo de Processamento

1. O Chatwoot recebe uma mensagem de um cliente via WhatsApp, Facebook, etc.
2. O Chatwoot envia a mensagem para o endpoint `/webhook` da API CrewAI
3. A API identifica o tenant (account_id) e o canal, e encaminha para a crew apropriada
4. A crew carrega as configurações específicas do tenant via MCP-MongoDB
5. Os agentes processam a mensagem sequencialmente:
   - Identificação da intenção
   - Busca de informações relevantes via MCP-Qdrant e MCP-Odoo
   - Geração da resposta
   - Formatação final
6. A resposta é enviada de volta ao cliente via Chatwoot

## Multi-tenant

O sistema é projetado para suportar múltiplos tenants (clientes), onde cada tenant é identificado por um `account_id` único. Este identificador é usado para:

- Carregar configurações específicas do tenant do MongoDB
- Acessar coleções vetoriais específicas do tenant no Qdrant
- Consultar o banco de dados Odoo específico do tenant

## Execução Local

Para executar o serviço localmente:

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export MCP_ODOO_URL=http://localhost:8000
export MCP_MONGODB_URL=http://localhost:8001
export MCP_QDRANT_URL=http://localhost:8002
export OPENAI_API_KEY=your_openai_api_key

# Iniciar o servidor
python api.py
```

## Execução com Docker

O serviço pode ser executado como parte do docker-compose definido no diretório `/docker`:

```bash
cd ../../docker
docker-compose up -d
```

## Desenvolvimento de Novas Crews

Para adicionar suporte a um novo canal de comunicação:

1. Crie um novo diretório para a crew (ex: `instagram_crew/`)
2. Implemente a classe principal seguindo o padrão da `WhatsAppCrew`
3. Atualize a função `get_crew_for_tenant()` na API para suportar o novo canal
