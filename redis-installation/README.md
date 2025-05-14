# Redis Installation

Este diretório contém a configuração do Redis, o banco de dados em memória usado pelo sistema para cache e filas.

## Sobre o Redis

Redis é um armazenamento de estrutura de dados em memória, usado como banco de dados, cache e message broker. No nosso sistema, é usado para:

- Cache de dados frequentemente acessados
- Controle de rate limiting
- Armazenamento de metadados de sincronização
- Filas de processamento assíncrono

## Configuração

O Redis está configurado para:

- Executar na porta 6379
- Armazenar dados no volume Docker `redis_data`
- Usar o modo AOF (Append Only File) para persistência
- Conectar-se à rede `chatwootai_network_public` para comunicação com outros serviços

## Uso

Para iniciar o Redis:

```bash
cd redis-installation
docker-compose up -d
```

Para parar o Redis:

```bash
cd redis-installation
docker-compose down
```

## Conexão com Outros Serviços

Outros serviços podem se conectar ao Redis usando:

- **Host**: `redis` (dentro da rede Docker)
- **Porta**: `6379`
- **URL**: `redis://redis:6379`

Não há autenticação configurada, então os serviços na mesma rede Docker podem se conectar diretamente.

## Persistência de Dados

Os dados do Redis são armazenados no volume Docker `redis_data` e o modo AOF garante que as operações sejam registradas em um arquivo de log, permitindo a recuperação dos dados em caso de reinicialização.

## Documentação

Para mais informações sobre o Redis, consulte a [documentação oficial](https://redis.io/documentation).
