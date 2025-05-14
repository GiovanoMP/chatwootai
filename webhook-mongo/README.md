# Webhook MongoDB para Company Services

Este serviço recebe dados do módulo `company_services` do Odoo e os armazena no MongoDB. Ele funciona como uma ponte entre o Odoo e o banco de dados MongoDB, permitindo que as configurações de empresa e serviços sejam armazenadas de forma estruturada e acessível para outros serviços.

## Índice

- [Requisitos](#requisitos)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Configuração](#configuração)
- [Instalação](#instalação)
  - [Usando Docker Compose](#usando-docker-compose)
  - [Instalação Manual](#instalação-manual)
- [Uso](#uso)
  - [Endpoints da API](#endpoints-da-api)
  - [Exemplos de Requisições](#exemplos-de-requisições)
- [Solução de Problemas](#solução-de-problemas)
  - [Problemas de Conexão com o Odoo](#problemas-de-conexão-com-o-odoo)
  - [Problemas com o MongoDB](#problemas-com-o-mongodb)
- [Configuração para Produção](#configuração-para-produção)
  - [Docker Swarm](#docker-swarm)
  - [Systemd](#systemd)
  - [Segurança](#segurança)

## Requisitos

- Python 3.10+
- MongoDB 6.0+
- Docker e Docker Compose (opcional, mas recomendado)
- Módulo `company_services` instalado no Odoo

## Estrutura do Projeto

```
webhook-mongo/
├── app.py                # Aplicação FastAPI para o webhook
├── Dockerfile            # Configuração do Docker para o webhook
├── requirements.txt      # Dependências do webhook
├── .env                  # Variáveis de ambiente (criar a partir do .env.example)
└── README.md             # Esta documentação
```

## Configuração

O webhook-mongo utiliza as seguintes variáveis de ambiente:

| Variável | Descrição | Valor Padrão |
|----------|-----------|--------------|
| `MONGODB_URI` | URI de conexão com o MongoDB | `mongodb://config_user:config_password@localhost:27017/config_service` |
| `API_KEY` | Chave de API para autenticação | `development-api-key` |

Você pode configurar estas variáveis de ambiente de três maneiras:

1. Arquivo `.env` no diretório do projeto
2. Variáveis de ambiente do sistema
3. No arquivo `docker-compose.yml` (se estiver usando Docker)

## Instalação

### Usando Docker Compose

A maneira mais fácil de instalar e executar o webhook-mongo é usando Docker Compose:

1. Navegue até o diretório `mongo-config-service`:

```bash
cd mongo-config-service
```

2. Execute o script de inicialização:

```bash
./start-services.sh
```

Este script iniciará três contêineres:
- `chatwoot-mongodb`: Banco de dados MongoDB
- `chatwoot-mongo-express`: Interface web para gerenciar o MongoDB (acessível em http://localhost:8082)
- `chatwoot-webhook-mongo`: O webhook que recebe dados do módulo company_services

### Instalação Manual

Se preferir instalar manualmente:

1. Clone o repositório e navegue até o diretório `webhook-mongo`:

```bash
cd webhook-mongo
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:

```bash
export MONGODB_URI="mongodb://config_user:config_password@localhost:27017/config_service"
export API_KEY="development-api-key"
```

4. Inicie o servidor:

```bash
python app.py
# ou
uvicorn app:app --host 0.0.0.0 --port 8003 --reload
```

## Uso

### Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Verifica se o serviço está rodando |
| `/health` | GET | Verifica a saúde do serviço e a conexão com o MongoDB |
| `/company-services/{account_id}/metadata` | POST | Recebe dados do módulo company_services |

### Exemplos de Requisições

#### Verificar se o serviço está rodando

```bash
curl http://localhost:8003/
```

Resposta esperada:
```json
{"message":"MongoDB Webhook API is running"}
```

#### Verificar a saúde do serviço

```bash
curl http://localhost:8003/health
```

Resposta esperada:
```json
{"status":"healthy","mongodb":"connected"}
```

#### Enviar dados do módulo company_services

```bash
curl -X POST \
  http://localhost:8003/company-services/account_1/metadata \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: development-api-key' \
  -H 'X-Security-Token: abc123' \
  -d '{
    "yaml_content": "account_id: account_1\nsecurity_token: abc123\nname: Empresa Exemplo\n..."
  }'
```

Resposta esperada:
```json
{"success":true,"message":"Dados inseridos com sucesso"}
```

## Solução de Problemas

### Problemas de Conexão com o Odoo

Se o Odoo não conseguir se conectar ao webhook-mongo, você pode encontrar erros como:

```
HTTPConnectionPool(host='localhost', port=8003): Max retries exceeded with url: /company-services/account_1/metadata (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7218dc7d50b8>: Failed to establish a new connection: [Errno 111] Connection refused'))
```

#### Solução 1: Verificar se o webhook está rodando

Primeiro, verifique se o webhook-mongo está rodando e acessível:

```bash
curl http://localhost:8003/
```

#### Solução 2: Configurar o Odoo para usar o IP correto

No Odoo, a URL do serviço de configuração deve apontar para o IP correto onde o webhook-mongo está rodando:

1. Acesse as configurações do módulo `company_services` no Odoo
2. Defina a URL do serviço de configuração como:
   - Para desenvolvimento local: `http://host.docker.internal:8003` (Docker Desktop no Windows/Mac)
   - Para desenvolvimento local no Linux: `http://172.17.0.1:8003` (IP padrão do host Docker)
   - Para produção: `http://[IP_DO_SERVIDOR]:8003` ou `http://[NOME_DO_HOST]:8003`

#### Solução 3: Configurar a rede Docker

Se estiver usando Docker, certifique-se de que os contêineres estão na mesma rede:

1. Crie uma rede Docker:

```bash
docker network create chatwoot-network
```

2. Adicione ambos os contêineres (Odoo e webhook-mongo) a esta rede:

```yaml
# No docker-compose.yml do Odoo
networks:
  - chatwoot-network

# No docker-compose.yml do webhook-mongo
networks:
  - chatwoot-network

networks:
  chatwoot-network:
    external: true
```

3. Use o nome do serviço como hostname:

```
http://webhook-mongo:8003
```

### Problemas com o MongoDB

Se o webhook-mongo não conseguir se conectar ao MongoDB, verifique:

1. Se o MongoDB está rodando:

```bash
docker ps | grep mongodb
```

2. Se as credenciais estão corretas:

```bash
docker exec -it chatwoot-mongodb mongo -u config_user -p config_password --authenticationDatabase config_service
```

3. Se o banco de dados e a coleção existem:

```bash
docker exec -it chatwoot-mongodb mongo -u config_user -p config_password --authenticationDatabase config_service
> use config_service
> db.company_services.find()
```

## Configuração para Produção

### Docker Swarm

Para um ambiente de produção robusto, recomendamos usar Docker Swarm:

1. Crie um arquivo `docker-stack.yml`:

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0-focal
    deploy:
      replicas: 1
      restart_policy:
        condition: any
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD:-chatwoot_mongodb_password}
    volumes:
      - mongodb-data:/data/db
      - ./mongo-init:/docker-entrypoint-initdb.d
    networks:
      - mongo-network
    command: mongod --auth

  webhook-mongo:
    image: ${WEBHOOK_MONGO_IMAGE:-webhook-mongo:latest}
    deploy:
      replicas: 1
      restart_policy:
        condition: any
    environment:
      - MONGODB_URI=mongodb://config_user:config_password@mongodb:27017/config_service
      - API_KEY=${MONGO_CONFIG_API_KEY:-development-api-key}
    ports:
      - "8003:8003"
    networks:
      - mongo-network

networks:
  mongo-network:
    external: true

volumes:
  mongodb-data:
    external: true
```

2. Implante o stack:

```bash
docker stack deploy -c docker-stack.yml mongo-config
```

### Systemd

Para sistemas baseados em systemd, você pode criar um serviço:

1. Crie um arquivo `/etc/systemd/system/webhook-mongo.service`:

```ini
[Unit]
Description=Webhook MongoDB Service
After=network.target mongodb.service
Requires=mongodb.service

[Service]
Type=simple
User=webhook
WorkingDirectory=/opt/webhook-mongo
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10
Environment=MONGODB_URI=mongodb://config_user:config_password@localhost:27017/config_service
Environment=API_KEY=your-production-api-key

[Install]
WantedBy=multi-user.target
```

2. Habilite e inicie o serviço:

```bash
sudo systemctl enable webhook-mongo
sudo systemctl start webhook-mongo
```

### Configuração para VPS Separadas

Quando o Odoo e o webhook-mongo estão em VPS diferentes (cenário de produção), siga estas etapas:

1. **Configuração do Webhook-Mongo:**
   - Exponha a porta 8003 para a internet (ou use um proxy reverso)
   - Configure um domínio ou subdomínio para o webhook (ex: `webhook.seudominio.com`)
   - Configure SSL/TLS para HTTPS (recomendado para produção)
   - Defina uma API_KEY forte e segura

2. **Configuração do Firewall na VPS do Webhook:**
   - Permita conexões na porta 8003 apenas dos IPs da VPS do Odoo
   - Exemplo com UFW:
     ```bash
     sudo ufw allow from [IP_DO_ODOO] to any port 8003 proto tcp
     ```
   - Exemplo com iptables:
     ```bash
     sudo iptables -A INPUT -p tcp -s [IP_DO_ODOO] --dport 8003 -j ACCEPT
     ```

3. **Configuração no Odoo:**
   - Configure a URL do serviço para apontar para o webhook público:
     ```
     https://webhook.seudominio.com
     ```
     ou
     ```
     http://[IP_PUBLICO_DO_WEBHOOK]:8003
     ```
   - Certifique-se de que a VPS do Odoo pode acessar a internet e alcançar o webhook

4. **Teste de Conectividade:**
   - Da VPS do Odoo, teste a conexão:
     ```bash
     curl -v https://webhook.seudominio.com/
     ```
     ou
     ```bash
     curl -v http://[IP_PUBLICO_DO_WEBHOOK]:8003/
     ```

### Segurança

Para produção, recomendamos:

1. Usar HTTPS com certificados SSL/TLS
2. Alterar as senhas padrão
3. Configurar autenticação mais robusta
4. Limitar o acesso à API apenas a IPs confiáveis
5. Usar um proxy reverso como Nginx ou Traefik
6. Implementar monitoramento e alertas
7. Configurar firewalls adequadamente em ambas as VPS
hook 