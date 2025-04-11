# Serviço de Vetorização para Produtos

Este serviço permite a geração de embeddings para descrições de produtos e a busca semântica usando linguagem natural.

## Visão Geral

O serviço de vetorização é responsável por:

1. Gerar embeddings para descrições de produtos
2. Armazenar embeddings no Qdrant
3. Realizar buscas semânticas usando linguagem natural

## Arquitetura

```
┌─────────────┐     ┌───────────────────┐     ┌─────────────────┐     ┌─────────────┐
│             │     │                   │     │                 │     │             │
│   Odoo UI   │◄────┤   Módulo Odoo     │◄────┤   MCP-Odoo      │◄────┤  Agente de  │
│ (Usuário)   │     │   (Metadados)     │     │   (Roteamento)  │     │  Descrição  │
└──────┬──────┘     └───────────────────┘     └────────┬────────┘     └─────────────┘
       │                                                │                     ▲
       │                                                │                     │
       │                                                ▼                     │
       │                                      ┌─────────────────┐             │
       │                                      │                 │             │
       └─────────────────────────────────────►│ Vector Service │─────────────┘
                                              │                 │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │                 │
                                              │     Qdrant      │
                                              │                 │
                                              └─────────────────┘
```

## Componentes

### 1. Agente de Descrição de Produtos

Localizado em `src/agents/product_description_agent.py`, este agente usa OpenAI para gerar descrições comerciais concisas a partir de metadados de produtos.

### 2. Serviço de Vetorização

Localizado em `src/vector_service/`, este serviço fornece:

- API REST para geração de embeddings e busca semântica
- Integração com OpenAI para geração de embeddings
- Integração com Qdrant para armazenamento e busca de vetores
- Cache com Redis para melhorar o desempenho

### 3. Integração com MCP-Odoo

Localizado em `src/mcp_odoo/server.py`, esta integração fornece:

- Endpoint para geração de descrições de produtos
- Endpoint para sincronização de produtos com o banco de dados vetorial
- Endpoint para busca semântica de produtos

### 4. Módulo Odoo

Localizado em `addons/semantic_product_description/`, este módulo fornece:

- Interface para edição de descrições de produtos
- Integração com MCP-Odoo para geração de descrições e sincronização
- Campos para armazenamento de metadados e status de sincronização

## Configuração

### Requisitos

- Python 3.8+
- OpenAI API Key
- Qdrant (local ou remoto)
- Redis (opcional, para cache)
- Odoo 14+

### Variáveis de Ambiente

Crie um arquivo `.env.vector-service` com as seguintes variáveis:

```
# Configurações do Serviço de Vetorização
VECTOR_SERVICE_HOST=0.0.0.0
VECTOR_SERVICE_PORT=8001
VECTOR_SERVICE_RELOAD=false

# Configurações do OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Configurações do Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=
QDRANT_HTTPS=false

# Configurações do Redis
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## Uso

### Iniciar o Serviço de Vetorização

```bash
./start_vector_service.sh
```

### Testar a Integração

```bash
# Copiar o arquivo de exemplo
cp .env.test.example .env.test

# Editar o arquivo com suas configurações
nano .env.test

# Executar o script de teste
./test_integration.py
```

## Fluxo de Trabalho

### 1. Geração de Descrição

1. Usuário clica em "Gerar Descrição com IA" no módulo Odoo
2. Módulo Odoo envia metadados para MCP-Odoo
3. MCP-Odoo chama o Agente de Descrição
4. Descrição gerada é retornada ao usuário para edição

### 2. Sincronização com Qdrant

1. Usuário clica em "Sincronizar com Sistema de IA" após revisar/editar a descrição
2. Módulo Odoo envia descrição para MCP-Odoo
3. MCP-Odoo chama o Serviço de Vetorização
4. Serviço de Vetorização gera embedding e armazena no Qdrant
5. Status de sincronização é atualizado no Odoo

### 3. Busca Semântica

1. Aplicação cliente envia consulta em linguagem natural para MCP-Odoo
2. MCP-Odoo chama o Serviço de Vetorização para busca
3. Serviço de Vetorização consulta Qdrant e retorna resultados
4. MCP-Odoo enriquece resultados com dados do Odoo e retorna ao cliente

## API do Serviço de Vetorização

### Criar/Atualizar Vetor

```
POST /api/v1/vectors
```

**Corpo da Requisição:**
```json
{
  "account_id": "account_2",
  "product_id": "1",
  "text": "Descrição do produto...",
  "metadata": {
    "name": "Nome do Produto",
    "category": "Categoria",
    "verified": true
  }
}
```

### Busca Semântica

```
POST /api/v1/search
```

**Corpo da Requisição:**
```json
{
  "account_id": "account_2",
  "query": "produto de alta qualidade",
  "limit": 5,
  "filter": {
    "category": "Móveis"
  }
}
```

## Testes

### Testes Unitários

```bash
# Executar testes unitários
pytest src/tests/
```

### Testes de Integração

```bash
# Executar testes de integração
./test_integration.py
```

## Solução de Problemas

### Erro de Conexão com Qdrant

Verifique se o Qdrant está em execução e acessível:

```bash
curl http://localhost:6333/collections
```

### Erro de Geração de Embeddings

Verifique se a chave da API OpenAI está configurada corretamente:

```bash
echo $OPENAI_API_KEY
```

### Erro de Conexão com MCP-Odoo

Verifique se o MCP-Odoo está em execução e acessível:

```bash
curl http://localhost:8000/health
```

## Próximos Passos

1. Implementar busca híbrida (vetorial + filtros)
2. Adicionar suporte para busca por similaridade de imagens
3. Implementar análise de feedback para melhorar as descrições
4. Adicionar suporte para outros ERPs além do Odoo
