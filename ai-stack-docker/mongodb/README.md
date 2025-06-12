# MongoDB para ChatwootAI

Este diretório contém a configuração do MongoDB e Mongo Express para o projeto ChatwootAI, fornecendo armazenamento de dados para configurações de tenants e serviços.

## Informações de Acesso

### MongoDB
- **Host**: localhost
- **Porta**: 27017
- **Usuário Root**: admin
- **Senha Root**: admin_password
- **Banco de Dados**: config_service
- **Usuário do Banco**: config_user
- **Senha do Banco**: config_password

### Mongo Express (Interface Web)
- **URL de acesso**: http://localhost:8082
- **Usuário**: admin
- **Senha**: express_password

## Inicialização

### Inicialização com Docker Compose

```bash
# Navegue até o diretório do MongoDB
cd /home/giovano/Projetos/ai_stack/ai-stack/mongodb

# Verifique se a rede ai-stack existe
cd ..
./network.sh
cd mongodb

# Inicie o MongoDB e Mongo Express
docker-compose up -d
```

## Parando o serviço

Para parar os serviços MongoDB e Mongo Express:

```bash
# Navegue até o diretório do MongoDB
cd /home/giovano/Projetos/ai_stack/ai-stack/mongodb

# Pare os serviços
docker-compose down
```

## Reiniciando o serviço

Para reiniciar os serviços MongoDB e Mongo Express:

```bash
# Navegue até o diretório do MongoDB
cd /home/giovano/Projetos/ai_stack/ai-stack/mongodb

# Pare e inicie os serviços
docker-compose down
docker-compose up -d
```

## Estrutura de Dados

O MongoDB é inicializado com as seguintes coleções:

- **company_services**: Armazena configurações de serviços da empresa por tenant
- **tenants**: Armazena informações sobre os tenants do sistema
- **configurations**: Armazena configurações gerais do sistema

## Integração com MCP-MongoDB

Este MongoDB é projetado para trabalhar com o serviço MCP-MongoDB, que fornece uma interface MCP (Model Context Protocol) para acesso aos dados. O MCP-MongoDB deve ser configurado separadamente.

## Segurança

- Autenticação habilitada para todos os acessos
- Dados persistidos em volume Docker dedicado
- Acesso restrito à rede ai-stack
