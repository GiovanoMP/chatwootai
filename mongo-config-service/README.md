# MongoDB Config Service

Este serviço fornece armazenamento e gerenciamento de configurações para o sistema ChatwootAI, utilizando MongoDB como banco de dados principal.

## Componentes

1. **MongoDB**: Banco de dados NoSQL para armazenamento de configurações em formato JSON
   - **Porta**: 27017
   - **Contêiner**: chatwoot-mongodb
   - **Credenciais**: 
     - Admin: admin / chatwoot_mongodb_password
     - Usuário da aplicação: config_user / config_password

2. **Mongo Express**: Interface web para visualização e gerenciamento dos dados no MongoDB
   - **Porta**: 8082
   - **URL**: http://localhost:8082
   - **Contêiner**: chatwoot-mongo-express
   - **Credenciais**: admin / express_password

3. **Webhook MongoDB**: API REST para receber dados do módulo Odoo company_services
   - **Porta**: 8003
   - **URL**: http://localhost:8003
   - **Contêiner**: chatwoot-webhook-mongo
   - **API Key**: development-api-key (configurável via variável de ambiente)

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

-1. Docker e Docker Compose instalados
2. Porta 27017 disponível para o MongoDB
3. Porta 8082 disponível para o Mongo Express
4. Porta 8003 disponível para o webhook

### Passos para Instalação

1. Navegue até o diretório do serviço:
   ```bash
   cd /home/giovano/Projetos/ai_stack/mongo-config-service
   ```

2. Inicie os serviços:
   ```bash
   docker-compose up -d
   ```

3. Verifique se os contêineres estão em execução:
   ```bash
   docker ps | grep chatwoot
   ```

4. Acesse o Mongo Express para visualizar os dados:
   ```
   http://localhost:8082
   ```
   Credenciais: admin / express_password

### Verificação da Instalação

1. Abra o navegador e acesse o Mongo Express:
   - URL: http://localhost:8082
   - Você deverá ver a interface do Mongo Express com o banco de dados `config_service`

2. Verifique se o webhook está funcionando:
   ```bash
   curl -X GET http://localhost:8003/health -H "X-API-Key: development-api-key"
   ```
   Deve retornar: `{"status": "ok"}`

## Integração com o Módulo Odoo

O módulo Odoo `company_services` deve ser configurado para enviar dados para o webhook. Configure os seguintes parâmetros no módulo:

1. **URL do Serviço de Configuração**: `http://localhost:8003`
2. **Chave de API**: `development-api-key` (ou o valor definido em `.env`)
3. **ID da Conta**: Identificador único para cada cliente (ex: `account_1`, `account_2`, etc.)
4. **Token de Segurança**: Token único para autenticação

O webhook receberá os dados via POST e os armazenará no MongoDB na coleção `company_services`, usando o `account_id` como identificador único.

## Consulta de Configurações

As configurações podem ser consultadas diretamente no MongoDB ou através de uma API que será implementada no MCP-MongoDB.

### Exemplo de Consulta no MongoDB via Mongo Express

1. Acesse o Mongo Express em http://localhost:8082
2. Faça login com as credenciais: admin / express_password
3. Selecione o banco de dados `config_service`
4. Clique na coleção `company_services`
5. Visualize ou edite os documentos conforme necessário

### Exemplo de Consulta via Terminal

```bash
# Conectar ao MongoDB
docker exec -it chatwoot-mongodb mongosh -u config_user -p config_password --authenticationDatabase config_service

# Consultar configurações
use config_service
db.company_services.findOne({ account_id: "account_1" })
```

### Endpoints de Consulta do Webhook

```
GET /api/config/{account_id}
```

Exemplo:
```bash
curl -X GET http://localhost:8003/api/config/account_1 \
  -H "X-API-Key: development-api-key"
```

## Segurança

- O MongoDB está configurado com autenticação
- O webhook requer um token de segurança para cada cliente e uma API Key para autenticação
- As comunicações devem ser feitas em uma rede segura
- Credenciais são configuráveis via variáveis de ambiente

## Variáveis de Ambiente

O serviço suporta as seguintes variáveis de ambiente:

- `MONGO_ROOT_PASSWORD`: Senha do usuário admin do MongoDB (padrão: chatwoot_mongodb_password)
- `MONGO_EXPRESS_USER`: Usuário do Mongo Express (padrão: admin)
- `MONGO_EXPRESS_PASSWORD`: Senha do Mongo Express (padrão: express_password)
- `MONGO_CONFIG_API_KEY`: Chave de API para o webhook (padrão: development-api-key)

## Manutenção

### Backup do MongoDB

```bash
docker exec -it chatwoot-mongodb mongodump --authenticationDatabase admin -u admin -p chatwoot_mongodb_password --db config_service --out /dump
docker cp chatwoot-mongodb:/dump ./backup
```

### Restauração do MongoDB

```bash
docker cp ./backup chatwoot-mongodb:/dump
docker exec -it chatwoot-mongodb mongorestore --authenticationDatabase admin -u admin -p chatwoot_mongodb_password /dump
```

### Logs dos Contêineres

```bash
# Logs do MongoDB
docker logs chatwoot-mongodb

# Logs do Mongo Express
docker logs chatwoot-mongo-express

# Logs do Webhook
docker logs chatwoot-webhook-mongo
```

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
