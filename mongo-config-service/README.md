# MongoDB Config Service

Este microsserviço fornece armazenamento de configurações em MongoDB para o sistema ChatwootAI, recebendo dados JSON do módulo Odoo `company_services`.

## Componentes

1. **MongoDB**: Banco de dados NoSQL para armazenamento de configurações em formato JSON
2. **Mongo Express**: Interface web para visualização e gerenciamento dos dados no MongoDB
3. **Webhook MongoDB**: API REST para receber dados do módulo Odoo company_services

## Estrutura de Dados

O MongoDB armazena as configurações em uma única coleção:

**company_services**: Configurações completas de cada cliente (tenant)
   - `account_id`: Identificador único do cliente (usado como chave primária)
   - `security_token`: Token de segurança para autenticação
   - `name`: Nome da empresa
   - `description`: Descrição da empresa
   - `version`: Versão da configuração (incrementada a cada atualização)
   - `updated_at`: Data da última atualização
   - `enabled_modules`: Lista de módulos habilitados
   - `modules`: Objeto contendo todas as configurações específicas do cliente
     - `company_info`: Informações da empresa
     - `service_settings`: Configurações de atendimento
     - `enabled_services`: Serviços habilitados
     - `mcp`: Configurações de conexão com o MCP
     - `channels`: Canais de comunicação habilitados

## Instalação e Execução

### Pré-requisitos

- Docker
- Docker Compose

### Configuração

1. Edite o arquivo `.env` para configurar senhas e outras variáveis de ambiente:
   ```
   MONGO_ROOT_PASSWORD=sua_senha_segura
   MONGO_EXPRESS_USER=seu_usuario
   MONGO_EXPRESS_PASSWORD=sua_senha_express
   ```

2. Execute o script de inicialização:
   ```bash
   ./start-services.sh
   ```

3. Acesse o Mongo Express para visualizar os dados:
   ```
   http://localhost:8081
   ```

## Integração com o Módulo Odoo

O módulo Odoo `company_services` deve ser configurado para enviar dados para o webhook. Configure os seguintes parâmetros no módulo:

1. **URL do Serviço de Configuração**: `http://localhost:8003`
2. **Chave de API**: `development-api-key` (ou o valor definido em `.env`)
3. **ID da Conta**: Identificador único para cada cliente (ex: `account_1`, `account_2`, etc.)
4. **Token de Segurança**: Token único para autenticação

O webhook receberá os dados via POST e os armazenará no MongoDB na coleção `company_services`, usando o `account_id` como identificador único.

## Estrutura de Diretórios

```
mongo-config-service/
├── docker-compose.yml    # Configuração do Docker Compose
├── .env                  # Variáveis de ambiente
├── mongo-init/           # Scripts de inicialização do MongoDB
│   └── init-mongo.js     # Script para criar usuários, coleções e índices
├── start-services.sh     # Script para iniciar os serviços
└── README.md             # Esta documentação

webhook-mongo/
├── app.py                # Aplicação FastAPI para o webhook
├── Dockerfile            # Configuração do Docker para o webhook
├── requirements.txt      # Dependências do webhook
└── .env                  # Variáveis de ambiente para o webhook
```

## Acesso ao MongoDB

- **URI**: `mongodb://config_user:config_password@localhost:27017/config_service`
- **Banco de Dados**: `config_service`
- **Coleção**: `company_services`

## Acesso ao Mongo Express

- **URL**: `http://localhost:8081`
- **Usuário**: Definido em `.env` (padrão: `admin`)
- **Senha**: Definida em `.env` (padrão: `express_password`)
