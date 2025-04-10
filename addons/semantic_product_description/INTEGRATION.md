# Guia de Integração - Módulo de Descrições Inteligentes de Produtos

Este documento fornece instruções detalhadas para integrar o módulo de Descrições Inteligentes de Produtos com o MCP (Message Control Program) e sistemas de vetorização como Qdrant.

## Visão Geral da Arquitetura

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│    Odoo     │◄───┤     MCP     │◄───┤   Qdrant    │
│             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                  ▲                  ▲
       │                  │                  │
       └──────────────────┴──────────────────┘
                  Fluxo de Dados
```

## Métodos Disponíveis para Integração

### 1. Geração de Descrições

#### `generate_semantic_description()`

Este método gera automaticamente descrições inteligentes para produtos com base em seus metadados.

**Implementação no MCP:**

```python
def generate_product_descriptions(account_id, product_ids=None):
    """
    Gera descrições para produtos específicos ou todos os produtos ativos.
    
    Args:
        account_id (str): ID da conta no MCP
        product_ids (list, optional): Lista de IDs de produtos. Se None, processa todos os produtos ativos.
    
    Returns:
        dict: Resultado da operação com contagem de produtos processados
    """
    # Configurar conexão com Odoo via MCP
    odoo_connection = get_odoo_connection(account_id)
    
    # Se product_ids não for fornecido, buscar todos os produtos ativos
    if not product_ids:
        product_ids = odoo_connection.execute(
            'product.template', 
            'search', 
            [('active', '=', True)]
        )
    
    # Chamar o método de geração de descrição
    odoo_connection.execute(
        'product.template', 
        'generate_semantic_description', 
        product_ids
    )
    
    return {
        'status': 'success',
        'products_processed': len(product_ids),
        'message': f'Descrições geradas para {len(product_ids)} produtos'
    }
```

### 2. Sincronização com Sistema de Vetorização

#### `get_products_for_sync()`

Este método retorna produtos que precisam ser sincronizados com o sistema de vetorização.

**Implementação no MCP:**

```python
def get_products_pending_sync(account_id, limit=100):
    """
    Busca produtos que precisam ser sincronizados com o sistema de vetorização.
    
    Args:
        account_id (str): ID da conta no MCP
        limit (int, optional): Número máximo de produtos a retornar. Padrão é 100.
    
    Returns:
        list: Lista de dicionários com dados dos produtos
    """
    # Configurar conexão com Odoo via MCP
    odoo_connection = get_odoo_connection(account_id)
    
    # Buscar IDs de produtos que precisam de sincronização
    product_ids = odoo_connection.execute(
        'product.template', 
        'search', 
        [('semantic_sync_status', '=', 'needs_update')],
        0, limit
    )
    
    # Buscar dados completos dos produtos
    products_data = []
    for product_id in product_ids:
        product_data = odoo_connection.execute(
            'product.template',
            'get_product_vector_data',
            product_id
        )
        products_data.append(product_data)
    
    return products_data
```

#### `get_product_vector_data(product_id)`

Este método retorna dados estruturados do produto para vetorização.

**Implementação no MCP:**

```python
def get_product_data_for_vectorization(account_id, product_id):
    """
    Obtém dados estruturados de um produto específico para vetorização.
    
    Args:
        account_id (str): ID da conta no MCP
        product_id (int): ID do produto no Odoo
    
    Returns:
        dict: Dados estruturados do produto
    """
    # Configurar conexão com Odoo via MCP
    odoo_connection = get_odoo_connection(account_id)
    
    # Obter dados do produto
    product_data = odoo_connection.execute(
        'product.template',
        'get_product_vector_data',
        product_id
    )
    
    return product_data
```

#### `update_sync_status(product_id, status, vector_id=None)`

Este método atualiza o status de sincronização de um produto.

**Implementação no MCP:**

```python
def update_product_sync_status(account_id, product_id, status, vector_id=None):
    """
    Atualiza o status de sincronização de um produto após processamento.
    
    Args:
        account_id (str): ID da conta no MCP
        product_id (int): ID do produto no Odoo
        status (str): Status de sincronização ('synced', 'not_synced', 'needs_update')
        vector_id (str, optional): ID do vetor no sistema de vetorização
    
    Returns:
        dict: Resultado da operação
    """
    # Configurar conexão com Odoo via MCP
    odoo_connection = get_odoo_connection(account_id)
    
    # Atualizar status de sincronização
    result = odoo_connection.execute(
        'product.template',
        'update_sync_status',
        product_id, status, vector_id
    )
    
    return {
        'status': 'success',
        'product_id': product_id,
        'sync_status': status,
        'vector_id': vector_id
    }
```

### 3. Fluxo Completo de Sincronização

**Implementação no MCP:**

```python
def sync_products_with_qdrant(account_id, batch_size=50):
    """
    Sincroniza produtos pendentes com o sistema de vetorização Qdrant.
    
    Args:
        account_id (str): ID da conta no MCP
        batch_size (int, optional): Tamanho do lote para processamento. Padrão é 50.
    
    Returns:
        dict: Resultado da operação com estatísticas
    """
    # Obter produtos pendentes de sincronização
    products_to_sync = get_products_pending_sync(account_id, batch_size)
    
    # Estatísticas
    stats = {
        'total': len(products_to_sync),
        'success': 0,
        'failed': 0
    }
    
    # Processar cada produto
    for product_data in products_to_sync:
        try:
            # Gerar embedding usando OpenAI
            embedding = generate_embedding_for_product(product_data)
            
            # Armazenar no Qdrant
            vector_id = store_in_qdrant(account_id, product_data['id'], embedding, product_data)
            
            # Atualizar status no Odoo
            update_product_sync_status(account_id, product_data['id'], 'synced', vector_id)
            
            stats['success'] += 1
            
        except Exception as e:
            # Registrar erro e marcar como falha
            log_error(f"Erro ao sincronizar produto {product_data['id']}: {str(e)}")
            update_product_sync_status(account_id, product_data['id'], 'not_synced')
            stats['failed'] += 1
    
    return {
        'status': 'completed',
        'statistics': stats
    }
```

## Integração com Qdrant

### Geração de Embeddings

```python
def generate_embedding_for_product(product_data):
    """
    Gera embedding para um produto usando OpenAI.
    
    Args:
        product_data (dict): Dados estruturados do produto
    
    Returns:
        list: Vetor de embedding
    """
    import openai
    
    # Preparar texto para embedding
    text_for_embedding = f"""
    Nome: {product_data['name']}
    Categoria: {product_data['category']}
    Descrição: {product_data['ai_generated_description'] or product_data['semantic_description']}
    Características: {', '.join(product_data['key_features'])}
    Casos de Uso: {', '.join(product_data['use_cases'])}
    Tags: {', '.join(product_data['tags'])}
    """
    
    # Gerar embedding usando OpenAI
    response = openai.Embedding.create(
        input=text_for_embedding,
        model="text-embedding-ada-002"
    )
    
    return response['data'][0]['embedding']
```

### Armazenamento no Qdrant

```python
def store_in_qdrant(account_id, product_id, embedding, product_data):
    """
    Armazena embedding e metadados no Qdrant.
    
    Args:
        account_id (str): ID da conta no MCP
        product_id (int): ID do produto no Odoo
        embedding (list): Vetor de embedding
        product_data (dict): Dados estruturados do produto
    
    Returns:
        str: ID do vetor no Qdrant
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import PointStruct, VectorParams, Distance
    
    # Configurar cliente Qdrant
    qdrant_client = get_qdrant_client()
    
    # Garantir que a coleção existe
    collection_name = f"products_{account_id}"
    
    # Verificar se a coleção existe, se não, criar
    collections = qdrant_client.get_collections().collections
    collection_exists = any(collection.name == collection_name for collection in collections)
    
    if not collection_exists:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
    
    # Preparar metadados
    metadata = {
        'product_id': product_id,
        'name': product_data['name'],
        'category': product_data['category'],
        'description': product_data['ai_generated_description'] or product_data['semantic_description'],
        'price': product_data.get('price', 0.0),
        'tags': product_data['tags'],
        'verified': product_data['verified'],
        'last_update': product_data['last_update']
    }
    
    # Criar ID único para o vetor
    vector_id = f"prod_{account_id}_{product_id}"
    
    # Upsert do ponto no Qdrant
    qdrant_client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=vector_id,
                vector=embedding,
                payload=metadata
            )
        ]
    )
    
    return vector_id
```

## Endpoints da API MCP

Para facilitar a integração, o MCP deve expor os seguintes endpoints:

### 1. Geração de Descrições

```
POST /api/v1/products/generate-descriptions
```

**Parâmetros:**
- `account_id` (obrigatório): ID da conta
- `product_ids` (opcional): Lista de IDs de produtos

**Resposta:**
```json
{
  "status": "success",
  "products_processed": 10,
  "message": "Descrições geradas para 10 produtos"
}
```

### 2. Sincronização com Qdrant

```
POST /api/v1/products/sync-with-qdrant
```

**Parâmetros:**
- `account_id` (obrigatório): ID da conta
- `batch_size` (opcional): Tamanho do lote para processamento

**Resposta:**
```json
{
  "status": "completed",
  "statistics": {
    "total": 50,
    "success": 48,
    "failed": 2
  }
}
```

### 3. Busca Semântica

```
POST /api/v1/products/semantic-search
```

**Parâmetros:**
- `account_id` (obrigatório): ID da conta
- `query` (obrigatório): Texto da consulta
- `limit` (opcional): Número máximo de resultados

**Resposta:**
```json
{
  "status": "success",
  "results": [
    {
      "product_id": 42,
      "name": "Cadeira Ergonômica Deluxe",
      "description": "Cadeira ergonômica de escritório com ajuste de altura...",
      "score": 0.92,
      "price": 599.99,
      "image_url": "https://example.com/images/chair.jpg"
    },
    // Mais resultados...
  ]
}
```

## Configuração do Ambiente

### Requisitos

- Odoo 14.0 ou superior
- Python 3.7 ou superior
- Qdrant (para armazenamento de vetores)
- OpenAI API (para geração de embeddings)
- Redis (para cache)

### Variáveis de Ambiente

```
# Configurações do Odoo
ODOO_HOST=localhost
ODOO_PORT=8069
ODOO_DB=odoo14
ODOO_USER=admin
ODOO_PASSWORD=admin

# Configurações do OpenAI
OPENAI_API_KEY=sk-your-api-key

# Configurações do Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Configurações do Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Exemplos de Uso

### Exemplo 1: Gerar Descrições para Todos os Produtos

```python
# Chamada via MCP
response = mcp_client.post('/api/v1/products/generate-descriptions', {
    'account_id': 'account_2'
})

print(f"Processados: {response['products_processed']} produtos")
```

### Exemplo 2: Sincronizar Produtos com Qdrant

```python
# Chamada via MCP
response = mcp_client.post('/api/v1/products/sync-with-qdrant', {
    'account_id': 'account_2',
    'batch_size': 100
})

print(f"Sincronização concluída. Sucesso: {response['statistics']['success']}, Falhas: {response['statistics']['failed']}")
```

### Exemplo 3: Busca Semântica de Produtos

```python
# Chamada via MCP
response = mcp_client.post('/api/v1/products/semantic-search', {
    'account_id': 'account_2',
    'query': 'cadeira confortável para escritório com apoio lombar',
    'limit': 5
})

# Exibir resultados
for product in response['results']:
    print(f"{product['name']} - Score: {product['score']}")
    print(f"Descrição: {product['description'][:100]}...")
    print("---")
```

## Considerações de Desempenho

- **Cache com Redis**: Utilize Redis para armazenar resultados de buscas frequentes
- **Processamento em Lote**: Processe produtos em lotes para evitar sobrecarga
- **Atualização Incremental**: Sincronize apenas produtos que foram modificados
- **Monitoramento**: Implemente monitoramento para rastrear tempos de resposta e falhas

## Solução de Problemas

### Problemas Comuns e Soluções

1. **Erro de Conexão com Odoo**:
   - Verifique as credenciais e URL do Odoo
   - Confirme se o usuário tem permissões adequadas

2. **Falha na Geração de Embeddings**:
   - Verifique a chave da API OpenAI
   - Confirme se o texto não excede o limite de tokens

3. **Erro de Sincronização com Qdrant**:
   - Verifique a conexão com o servidor Qdrant
   - Confirme se a coleção existe e tem a configuração correta

4. **Desempenho Lento**:
   - Implemente cache para consultas frequentes
   - Otimize o tamanho dos lotes de processamento
   - Considere aumentar recursos do servidor

## Próximos Passos

1. **Implementar Busca Híbrida**: Combinar busca vetorial com filtros tradicionais
2. **Adicionar Suporte a Imagens**: Incluir busca por similaridade de imagens
3. **Melhorar Geração de Descrições**: Utilizar modelos mais avançados para geração
4. **Implementar Feedback de Usuários**: Coletar feedback para melhorar resultados

## Contato e Suporte

Para dúvidas ou suporte relacionados à integração, entre em contato:

- Email: suporte@chatwootai.com
- Documentação: https://docs.chatwootai.com/integration
- GitHub: https://github.com/chatwootai/semantic_product_description
