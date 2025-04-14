# Referência da API Odoo

## Visão Geral

Esta documentação descreve os endpoints disponíveis na API REST para integração com o Odoo. A API segue os princípios RESTful e utiliza JSON para formatação de dados.

## Base URL

```
https://api.example.com/api/v1
```

## Autenticação

Todas as requisições à API devem incluir um token de autenticação no cabeçalho HTTP:

```
Authorization: Bearer {token}
```

## Parâmetros Comuns

Todas as requisições devem incluir o parâmetro `account_id` para identificar a conta/banco de dados:

```
?account_id=account_1
```

## Versionamento

A API é versionada através do prefixo no URL:

```
/api/v1/...
/api/v2/...
```

## Formatos de Resposta

### Sucesso

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

### Erro

```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Invalid input parameters",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

## Endpoints

### Módulo Semantic Product

#### Gerar Descrição de Produto

```
POST /products/{product_id}/description
```

Gera uma descrição semântica para um produto específico.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| product_id | integer | ID do produto no Odoo |
| account_id | string | ID da conta (query parameter) |

**Corpo da Requisição:**

```json
{
  "options": {
    "include_features": true,
    "include_use_cases": true,
    "tone": "professional"
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "product_id": 123,
    "description": "Este produto de alta qualidade...",
    "key_features": ["Durável", "Resistente à água", "Leve"],
    "use_cases": ["Ideal para uso externo", "Perfeito para viagens"]
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

#### Sincronizar Produto com Banco de Dados Vetorial

```
POST /products/{product_id}/sync
```

Sincroniza um produto com o banco de dados vetorial.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| product_id | integer | ID do produto no Odoo |
| account_id | string | ID da conta (query parameter) |

**Corpo da Requisição:**

```json
{
  "description": "Este produto de alta qualidade...",
  "skip_odoo_update": false
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "product_id": 123,
    "vector_id": "account_1_123",
    "sync_status": "completed",
    "timestamp": "2023-06-15T10:30:00Z"
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

#### Busca Semântica de Produtos

```
POST /products/search
```

Realiza uma busca semântica de produtos.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| account_id | string | ID da conta (query parameter) |

**Corpo da Requisição:**

```json
{
  "query": "produto resistente à água para uso externo",
  "limit": 10,
  "filters": {
    "category_id": 5,
    "price_range": [10.0, 50.0]
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "product_id": 123,
        "name": "Produto A",
        "description": "Este produto de alta qualidade...",
        "score": 0.92,
        "price": 29.99,
        "category_id": 5
      },
      {
        "product_id": 456,
        "name": "Produto B",
        "description": "Um produto resistente...",
        "score": 0.85,
        "price": 39.99,
        "category_id": 5
      }
    ],
    "total": 2
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

### Módulo Product Management

#### Sincronizar Múltiplos Produtos

```
POST /products/sync-batch
```

Sincroniza múltiplos produtos com o banco de dados vetorial.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| account_id | string | ID da conta (query parameter) |

**Corpo da Requisição:**

```json
{
  "product_ids": [123, 456, 789],
  "options": {
    "generate_descriptions": true,
    "skip_odoo_update": false
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "total": 3,
    "successful": 2,
    "failed": 1,
    "results": [
      {
        "product_id": 123,
        "status": "completed",
        "vector_id": "account_1_123"
      },
      {
        "product_id": 456,
        "status": "completed",
        "vector_id": "account_1_456"
      },
      {
        "product_id": 789,
        "status": "failed",
        "error": "Product not found"
      }
    ],
    "job_id": "job-123456"
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

#### Atualizar Preços em Massa

```
POST /products/update-prices
```

Atualiza preços de múltiplos produtos.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| account_id | string | ID da conta (query parameter) |

**Corpo da Requisição:**

```json
{
  "product_ids": [123, 456, 789],
  "adjustment": {
    "type": "percentage",
    "value": -10.0,
    "field": "ai_price"
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "total": 3,
    "successful": 3,
    "failed": 0,
    "results": [
      {
        "product_id": 123,
        "old_price": 29.99,
        "new_price": 26.99
      },
      {
        "product_id": 456,
        "old_price": 39.99,
        "new_price": 35.99
      },
      {
        "product_id": 789,
        "old_price": 49.99,
        "new_price": 44.99
      }
    ]
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

#### Verificar Status de Sincronização

```
GET /products/sync-status
```

Verifica o status de sincronização de produtos.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| account_id | string | ID da conta (query parameter) |
| product_ids | string | Lista de IDs de produtos separados por vírgula (opcional) |

**Resposta:**

```json
{
  "success": true,
  "data": {
    "total": 3,
    "synced": 2,
    "not_synced": 1,
    "products": [
      {
        "product_id": 123,
        "sync_status": "synced",
        "last_sync": "2023-06-15T10:30:00Z"
      },
      {
        "product_id": 456,
        "sync_status": "synced",
        "last_sync": "2023-06-15T10:30:00Z"
      },
      {
        "product_id": 789,
        "sync_status": "not_synced",
        "last_sync": null
      }
    ]
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

### Módulo Business Rules

#### Criar Regra de Negócio

```
POST /business-rules
```

Cria uma nova regra de negócio.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| account_id | string | ID da conta (query parameter) |

**Corpo da Requisição:**

```json
{
  "name": "Desconto para Clientes Premium",
  "description": "Clientes premium recebem 15% de desconto em todos os produtos",
  "rule_type": "discount",
  "priority": "1",
  "active": true
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "rule_id": 123,
    "name": "Desconto para Clientes Premium",
    "description": "Clientes premium recebem 15% de desconto em todos os produtos",
    "rule_type": "discount",
    "priority": "1",
    "active": true,
    "created_at": "2023-06-15T10:30:00Z"
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

#### Criar Regra Temporária

```
POST /business-rules/temporary
```

Cria uma nova regra temporária.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| account_id | string | ID da conta (query parameter) |

**Corpo da Requisição:**

```json
{
  "name": "Promoção de Verão",
  "description": "20% de desconto em produtos da categoria Verão",
  "rule_type": "promotion",
  "priority": "2",
  "active": true,
  "date_start": "2023-07-01T00:00:00Z",
  "date_end": "2023-08-31T23:59:59Z"
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "rule_id": 456,
    "name": "Promoção de Verão",
    "description": "20% de desconto em produtos da categoria Verão",
    "rule_type": "promotion",
    "priority": "2",
    "active": true,
    "date_start": "2023-07-01T00:00:00Z",
    "date_end": "2023-08-31T23:59:59Z",
    "created_at": "2023-06-15T10:30:00Z"
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

#### Sincronizar Regras com Sistema de IA

```
POST /business-rules/sync
```

Sincroniza todas as regras ativas com o sistema de IA.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| account_id | string | ID da conta (query parameter) |

**Resposta:**

```json
{
  "success": true,
  "data": {
    "permanent_rules": 5,
    "temporary_rules": 2,
    "sync_status": "completed",
    "timestamp": "2023-06-15T10:30:00Z"
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

#### Listar Regras Ativas

```
GET /business-rules/active
```

Lista todas as regras ativas no momento.

**Parâmetros:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| account_id | string | ID da conta (query parameter) |

**Resposta:**

```json
{
  "success": true,
  "data": {
    "permanent_rules": [
      {
        "rule_id": 123,
        "name": "Desconto para Clientes Premium",
        "description": "Clientes premium recebem 15% de desconto em todos os produtos",
        "rule_type": "discount",
        "priority": "1"
      }
    ],
    "temporary_rules": [
      {
        "rule_id": 456,
        "name": "Promoção de Verão",
        "description": "20% de desconto em produtos da categoria Verão",
        "rule_type": "promotion",
        "priority": "2",
        "date_start": "2023-07-01T00:00:00Z",
        "date_end": "2023-08-31T23:59:59Z"
      }
    ]
  },
  "meta": {
    "timestamp": "2023-06-15T10:30:00Z",
    "request_id": "req-123456"
  }
}
```

## Códigos de Status HTTP

| Código | Descrição |
|--------|-----------|
| 200 | OK - A requisição foi bem-sucedida |
| 201 | Created - Um novo recurso foi criado |
| 400 | Bad Request - A requisição contém parâmetros inválidos |
| 401 | Unauthorized - Autenticação necessária |
| 403 | Forbidden - Sem permissão para acessar o recurso |
| 404 | Not Found - Recurso não encontrado |
| 409 | Conflict - Conflito ao processar a requisição |
| 422 | Unprocessable Entity - Validação falhou |
| 429 | Too Many Requests - Limite de requisições excedido |
| 500 | Internal Server Error - Erro interno do servidor |

## Limites de Taxa

A API implementa limites de taxa para garantir a estabilidade do serviço:

- 100 requisições por minuto por cliente
- 1000 requisições por hora por cliente

Cabeçalhos de resposta incluem informações sobre o limite:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623760200
```

## Webhooks

A API suporta webhooks para notificações de eventos:

```
POST /webhooks
```

**Corpo da Requisição:**

```json
{
  "url": "https://example.com/webhook",
  "events": ["product.sync", "rule.created", "rule.expired"],
  "secret": "your-webhook-secret"
}
```

## Exemplos de Uso

### cURL

```bash
curl -X POST "https://api.example.com/api/v1/products/123/sync?account_id=account_1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Este produto de alta qualidade...", "skip_odoo_update": false}'
```

### Python

```python
import requests

url = "https://api.example.com/api/v1/products/123/sync"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}
params = {
    "account_id": "account_1"
}
data = {
    "description": "Este produto de alta qualidade...",
    "skip_odoo_update": False
}

response = requests.post(url, headers=headers, params=params, json=data)
print(response.json())
```
