# Qdrant Installation

Este diretório contém a configuração do Qdrant, o banco de dados vetorial usado pelo sistema.

## Sobre o Qdrant

Qdrant é um banco de dados vetorial de código aberto focado em busca por similaridade e filtragem por metadados. É usado para armazenar embeddings e realizar buscas semânticas.

## Configuração

O Qdrant está configurado para:

- Executar na porta 6333 (API REST)
- Executar na porta 6334 (gRPC)
- Armazenar dados no volume Docker `qdrant_data`
- Conectar-se à rede `chatwootai_network_public` para comunicação com outros serviços

## Uso

Para iniciar o Qdrant:

```bash
cd qdrant-installation
docker-compose up -d
```

Para parar o Qdrant:

```bash
cd qdrant-installation
docker-compose down
```

## Conexão com Outros Serviços

Outros serviços podem se conectar ao Qdrant usando:

- **Host**: `qdrant` (dentro da rede Docker)
- **Porta**: `6333` (API REST)
- **URL**: `http://qdrant:6333`

Não há autenticação configurada, então os serviços na mesma rede Docker podem se conectar diretamente.

## Persistência de Dados

Os dados do Qdrant são armazenados no volume Docker `qdrant_data`, garantindo que os dados persistam mesmo se o contêiner for reiniciado ou removido.

## Documentação

Para mais informações sobre o Qdrant, consulte a [documentação oficial](https://qdrant.tech/documentation/).
