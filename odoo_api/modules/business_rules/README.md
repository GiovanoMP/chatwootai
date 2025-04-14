# Módulo Business Rules

Este módulo implementa a API para gerenciamento de regras de negócio para o sistema de IA.

## Visão Geral

O módulo Business Rules permite:

- Criar, atualizar, listar e remover regras de negócio
- Gerenciar regras temporárias com datas de início e fim
- Fazer upload de documentos (PDF e DOCX) para extração de regras
- Sincronizar regras ativas com o sistema de IA

## Tipos de Regras

O módulo suporta os seguintes tipos de regras:

- **Greeting**: Regras de saudação para atendimento ao cliente
- **Business Hours**: Horários de funcionamento
- **Delivery**: Regras de entrega (prazos, frete grátis, etc.)
- **Pricing**: Regras de precificação (descontos, margens, etc.)
- **Promotion**: Promoções específicas
- **Customer Service**: Regras de atendimento ao cliente
- **Product**: Regras relacionadas a produtos
- **Custom**: Regras personalizadas

## Regras Temporárias

Regras temporárias são regras que têm uma data de início e fim definidas. Elas são automaticamente ativadas e desativadas com base nessas datas. Isso é útil para promoções sazonais, horários especiais de funcionamento, etc.

## Upload de Documentos

O módulo permite fazer upload de documentos PDF e DOCX para extração de regras de negócio. O texto extraído dos documentos é armazenado e pode ser usado para referência ou para alimentar um sistema de IA para extração automática de regras.

## Sincronização com o Sistema de IA

O módulo fornece um endpoint para sincronizar todas as regras ativas com o sistema de IA. As regras são armazenadas tanto no Redis (para acesso rápido) quanto no Qdrant (para busca semântica).

### Busca Semântica de Regras

O módulo implementa busca semântica de regras de negócio, permitindo encontrar regras relevantes para uma consulta em linguagem natural. Por exemplo, se um cliente perguntar "vocês embalam para presente?", o sistema pode encontrar a regra sobre embalagem de presentes, mesmo que a pergunta não contenha exatamente as mesmas palavras da regra.

A busca semântica é implementada usando o Qdrant, que armazena embeddings vetoriais das regras e permite busca por similaridade. Isso proporciona uma experiência muito mais natural e flexível para o sistema de IA, que pode encontrar regras relevantes mesmo quando a consulta usa sinônimos ou expressões diferentes.

## Endpoints da API

### Regras de Negócio

- `POST /api/v1/business-rules`: Cria uma nova regra de negócio
- `POST /api/v1/business-rules/temporary`: Cria uma nova regra temporária
- `PUT /api/v1/business-rules/{rule_id}`: Atualiza uma regra existente
- `DELETE /api/v1/business-rules/{rule_id}`: Remove uma regra
- `GET /api/v1/business-rules/{rule_id}`: Obtém uma regra pelo ID
- `GET /api/v1/business-rules`: Lista regras com paginação e filtros
- `GET /api/v1/business-rules/active`: Lista regras ativas no momento
- `POST /api/v1/business-rules/sync`: Sincroniza regras com o sistema de IA
- `GET /api/v1/business-rules/search`: Busca semântica de regras

### Documentos

- `POST /api/v1/business-rules/documents`: Faz upload de um documento
- `GET /api/v1/business-rules/documents`: Lista documentos

## Exemplos de Uso

### Criar uma Regra de Negócio

```python
import requests

url = "https://api.example.com/api/v1/business-rules"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}
params = {
    "account_id": "account_1"
}
data = {
    "name": "Desconto para Clientes Premium",
    "description": "Clientes premium recebem 15% de desconto em todos os produtos",
    "type": "pricing",
    "priority": 3,
    "active": True,
    "rule_data": {
        "discount_percentage": 15.0,
        "product_categories": [1, 2, 3]
    }
}

response = requests.post(url, headers=headers, params=params, json=data)
print(response.json())
```

### Criar uma Regra Temporária

```python
import requests
from datetime import date

url = "https://api.example.com/api/v1/business-rules/temporary"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}
params = {
    "account_id": "account_1"
}
data = {
    "name": "Promoção de Verão",
    "description": "Desconto de 20% em produtos de verão",
    "type": "promotion",
    "priority": 4,
    "active": True,
    "rule_data": {
        "name": "Promoção de Verão",
        "description": "Desconto de 20% em produtos de verão",
        "discount_type": "percentage",
        "discount_value": 20.0,
        "product_categories": [5, 6]
    },
    "start_date": str(date.today()),
    "end_date": str(date(2023, 12, 31))
}

response = requests.post(url, headers=headers, params=params, json=data)
print(response.json())
```

### Listar Regras Ativas

```python
import requests

url = "https://api.example.com/api/v1/business-rules/active"
headers = {
    "Authorization": "Bearer YOUR_TOKEN"
}
params = {
    "account_id": "account_1"
}

response = requests.get(url, headers=headers, params=params)
print(response.json())
```

### Sincronizar Regras com o Sistema de IA

```python
import requests

url = "https://api.example.com/api/v1/business-rules/sync"
headers = {
    "Authorization": "Bearer YOUR_TOKEN"
}
params = {
    "account_id": "account_1"
}

response = requests.post(url, headers=headers, params=params)
print(response.json())
```

### Busca Semântica de Regras

```python
import requests

url = "https://api.example.com/api/v1/business-rules/search"
headers = {
    "Authorization": "Bearer YOUR_TOKEN"
}
params = {
    "account_id": "account_1",
    "query": "Vocês embalam para presente?",
    "limit": 3,
    "score_threshold": 0.7
}

response = requests.get(url, headers=headers, params=params)
print(response.json())
```

### Fazer Upload de um Documento

```python
import requests
import base64

url = "https://api.example.com/api/v1/business-rules/documents"
headers = {
    "Authorization": "Bearer YOUR_TOKEN"
}
params = {
    "account_id": "account_1",
    "name": "Política de Entregas",
    "description": "Documento com as políticas de entrega da empresa",
    "document_type": "pdf"
}

with open("politica_entregas.pdf", "rb") as file:
    files = {"file": file}
    response = requests.post(url, headers=headers, params=params, files=files)
    print(response.json())
```

## Considerações de Implementação

- As regras são armazenadas no Odoo e sincronizadas com o Redis para acesso rápido pelo sistema de IA
- Regras temporárias são verificadas automaticamente com base nas datas de início e fim
- O processamento de documentos é feito de forma assíncrona para não bloquear a API
- O módulo utiliza cache para otimizar o desempenho de consultas frequentes
