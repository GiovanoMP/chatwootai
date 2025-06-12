# Redis para ChatwootAI

Este diretório contém a configuração do Redis e Redis Commander para o projeto ChatwootAI, fornecendo armazenamento em memória para cache, filas e mensagens.

## Informações de Acesso

### Redis
- **Host**: localhost
- **Porta**: 6379
- **Senha**: redis_password

### Redis Commander (Interface Web)
- **URL de acesso**: http://localhost:8083
- **Usuário**: admin
- **Senha**: admin_password

## Inicialização

### Inicialização com Docker Compose

```bash
# Navegue até o diretório do Redis
cd /home/giovano/Projetos/ai_stack/ai-stack/redis

# Verifique se a rede ai-stack existe
cd ..
./network.sh
cd redis

# Inicie o Redis e Redis Commander
docker-compose up -d
```

## Parando o serviço

Para parar os serviços Redis e Redis Commander:

```bash
# Navegue até o diretório do Redis
cd /home/giovano/Projetos/ai_stack/ai-stack/redis

# Pare os serviços
docker-compose down
```

## Reiniciando o serviço

Para reiniciar os serviços Redis e Redis Commander:

```bash
# Navegue até o diretório do Redis
cd /home/giovano/Projetos/ai_stack/ai-stack/redis

# Pare e inicie os serviços
docker-compose down
docker-compose up -d
```

## Uso do Redis

O Redis é utilizado para:

1. **Cache**: Armazenamento temporário de dados frequentemente acessados
2. **Filas de Mensagens**: Comunicação assíncrona entre serviços
3. **Pub/Sub**: Sistema de publicação/assinatura para eventos em tempo real
4. **Sessões**: Armazenamento de dados de sessão de usuários

## Integração com MCP-Redis

Este Redis é projetado para trabalhar com o serviço MCP-Redis, que fornece uma interface MCP (Model Context Protocol) para acesso aos dados. O MCP-Redis deve ser configurado separadamente.

## Segurança

- Autenticação habilitada com senha
- Dados persistidos em volume Docker dedicado
- Acesso restrito à rede ai-stack
