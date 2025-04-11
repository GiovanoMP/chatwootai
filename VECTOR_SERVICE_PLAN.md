# Plano de Implementação: Serviço de Vetorização para Produtos

Este documento descreve o plano de implementação para o serviço de vetorização de produtos, que integrará o módulo Odoo de Descrições Inteligentes de Produtos com o sistema de busca vetorial Qdrant.

## Visão Geral da Arquitetura

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

## Componentes Principais

### 1. Agente de Descrição de Produtos
- **Função**: Gerar descrições comerciais concisas a partir de metadados de produtos
- **Implementação**: Agente único especializado usando OpenAI
- **Localização**: `src/agents/product_description_agent.py`

### 2. Serviço de Vetorização
- **Função**: Gerar embeddings e gerenciar armazenamento no Qdrant
- **Implementação**: Serviço independente com API REST
- **Localização**: `src/vector_service/`

### 3. Integração com MCP-Odoo
- **Função**: Conectar o módulo Odoo com o agente de descrição e o serviço de vetorização
- **Implementação**: Endpoints adicionais no MCP-Odoo existente
- **Localização**: `src/mcp_odoo/server.py`

## Fluxo de Trabalho

1. **Geração de Descrição**:
   - Usuário clica em "Gerar Descrição com IA" no módulo Odoo
   - Módulo Odoo envia metadados para MCP-Odoo
   - MCP-Odoo chama o Agente de Descrição
   - Descrição gerada é retornada ao usuário para edição

2. **Sincronização com Qdrant**:
   - Usuário clica em "Sincronizar com Sistema de IA" após revisar/editar a descrição
   - Módulo Odoo envia descrição para MCP-Odoo
   - MCP-Odoo chama o Serviço de Vetorização
   - Serviço de Vetorização gera embedding e armazena no Qdrant
   - Status de sincronização é atualizado no Odoo

3. **Busca Semântica**:
   - Aplicação cliente envia consulta em linguagem natural para MCP-Odoo
   - MCP-Odoo chama o Serviço de Vetorização para busca
   - Serviço de Vetorização consulta Qdrant e retorna resultados
   - MCP-Odoo enriquece resultados com dados do Odoo e retorna ao cliente

## Plano de Implementação

### Fase 1: Agente de Descrição de Produtos (Semana 1)

1. **Implementar o Agente de Descrição**
   - Criar classe `ProductDescriptionAgent` usando OpenAI
   - Implementar método para gerar descrições concisas (50-100 palavras)
   - Testar com diferentes tipos de produtos

2. **Integrar com MCP-Odoo**
   - Adicionar endpoint `generate_product_description` no MCP-Odoo
   - Configurar para receber metadados e retornar descrições
   - Testar integração com o módulo Odoo

### Fase 2: Serviço de Vetorização (Semana 2)

1. **Implementar o Serviço de Vetorização Básico**
   - Criar API REST com FastAPI
   - Implementar endpoint para geração de embeddings
   - Implementar endpoint para armazenamento no Qdrant
   - Implementar endpoint para busca semântica

2. **Integrar com Qdrant**
   - Configurar cliente Qdrant
   - Implementar gerenciamento de coleções por tenant/account_id
   - Implementar operações CRUD para vetores
   - Implementar busca semântica

### Fase 3: Integração Completa (Semana 3)

1. **Integrar MCP-Odoo com Serviço de Vetorização**
   - Adicionar endpoint `sync_product_to_vector_db` no MCP-Odoo
   - Adicionar endpoint `semantic_search` no MCP-Odoo
   - Testar fluxo completo desde o Odoo até o Qdrant

2. **Otimizações**
   - Implementar cache com Redis
   - Otimizar geração de embeddings
   - Implementar busca híbrida (vetorial + filtros)

### Fase 4: Testes e Documentação (Semana 4)

1. **Testes Abrangentes**
   - Testar com diferentes tipos de produtos
   - Testar com diferentes tenants/account_ids
   - Testar performance e escalabilidade

2. **Documentação**
   - Atualizar documentação do módulo Odoo
   - Documentar endpoints do MCP-Odoo
   - Documentar Serviço de Vetorização
   - Criar guia de uso para usuários finais

## Detalhes de Implementação

### Agente de Descrição de Produtos

```python
# Em src/agents/product_description_agent.py

import openai
from typing import Dict, Any
import os

class ProductDescriptionAgent:
    """
    Agente especializado em gerar descrições comerciais concisas para produtos.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        openai.api_key = self.api_key
    
    def generate_description(self, product_metadata: Dict[str, Any]) -> str:
        """
        Gera uma descrição comercial concisa a partir dos metadados do produto.
        
        Args:
            product_metadata: Dicionário com metadados do produto
            
        Returns:
            str: Descrição gerada
        """
        # Construir prompt para o OpenAI
        prompt = self._build_prompt(product_metadata)
        
        # Gerar descrição usando OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um especialista em marketing e vendas, especializado em criar descrições concisas e persuasivas para produtos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        # Extrair e retornar a resposta
        return response.choices[0].message.content.strip()
    
    def _build_prompt(self, product_metadata):
        """Constrói o prompt para o LLM com base nos metadados do produto."""
        prompt = f"""
        Crie uma descrição comercial concisa e atraente para o seguinte produto:
        
        Nome do Produto: {product_metadata.get('name', 'N/A')}
        Categoria: {product_metadata.get('category', 'N/A')}
        """
        
        # Adicionar atributos se disponíveis
        if 'attributes' in product_metadata and product_metadata['attributes']:
            prompt += "Atributos:\n"
            for attr in product_metadata['attributes']:
                attr_name = attr.get('name', 'N/A')
                attr_values = ", ".join(attr.get('values', []))
                prompt += f"- {attr_name}: {attr_values}\n"
        
        # Adicionar características principais se disponíveis
        if 'key_features' in product_metadata and product_metadata['key_features']:
            prompt += "\nCaracterísticas Principais:\n"
            for feature in product_metadata['key_features']:
                prompt += f"- {feature}\n"
        
        # Adicionar casos de uso se disponíveis
        if 'use_cases' in product_metadata and product_metadata['use_cases']:
            prompt += "\nCasos de Uso:\n"
            for use_case in product_metadata['use_cases']:
                prompt += f"- {use_case}\n"
        
        # Adicionar tags se disponíveis
        if 'tags' in product_metadata and product_metadata['tags']:
            prompt += f"\nTags: {', '.join(product_metadata['tags'])}\n"
        
        # Adicionar instruções específicas
        prompt += """
        A descrição deve:
        1. Ser atraente e persuasiva
        2. Destacar apenas os principais benefícios e características
        3. Ter entre 50 e 100 palavras (muito importante)
        4. Usar linguagem comercial e direta
        
        Forneça apenas a descrição, sem introduções ou comentários adicionais.
        """
        
        return prompt
```

### Serviço de Vetorização

```python
# Em src/vector_service/api/app.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

from ..services.embedding import EmbeddingService
from ..services.search import SearchService
from ..utils.qdrant_client import get_qdrant_client
from ..utils.redis_client import get_redis_client

app = FastAPI(title="Vector Service API", description="API for product vectorization and semantic search")

# Modelos de dados
class ProductData(BaseModel):
    account_id: str
    product_id: str
    text: str
    metadata: Dict[str, Any]

class SearchQuery(BaseModel):
    account_id: str
    query: str
    limit: int = 10
    filter: Optional[Dict[str, Any]] = None

# Dependências
def get_embedding_service():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    qdrant_client = get_qdrant_client()
    redis_client = get_redis_client()
    return EmbeddingService(openai_api_key, qdrant_client, redis_client)

def get_search_service():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    qdrant_client = get_qdrant_client()
    redis_client = get_redis_client()
    return SearchService(openai_api_key, qdrant_client, redis_client)

# Rotas
@app.post("/api/v1/vectors", status_code=201)
async def create_vector(
    product_data: ProductData,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Create or update a vector for a product.
    """
    try:
        vector_id = embedding_service.generate_and_store_embedding(
            account_id=product_data.account_id,
            product_id=product_data.product_id,
            text=product_data.text,
            metadata=product_data.metadata
        )
        return {"success": True, "vector_id": vector_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/search")
async def search(
    search_query: SearchQuery,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Perform semantic search.
    """
    try:
        results = search_service.search(
            account_id=search_query.account_id,
            query=search_query.query,
            limit=search_query.limit,
            filter=search_query.filter
        )
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Integração com MCP-Odoo

```python
# Em src/mcp_odoo/server.py (adicionar novos endpoints)

@mcp.tool(
    "generate_product_description",
    description="Generate a rich commercial description for a product based on its metadata",
)
def generate_product_description(
    ctx: Context, request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a rich commercial description for a product based on its metadata
    
    This tool uses an LLM to create compelling product descriptions that can be
    reviewed and edited by users before being used for semantic search.
    """
    try:
        # Validate request
        account_id = request.get("account_id")
        product_id = request.get("product_id")
        
        if not account_id or not product_id:
            return {
                "success": False,
                "error": "Missing required parameters: account_id and product_id"
            }
        
        # Get product metadata from Odoo
        product_metadata = ctx.app.odoo.get_product_metadata(
            account_id=account_id,
            product_id=product_id
        )
        
        # Initialize the description agent
        from agents.product_description_agent import ProductDescriptionAgent
        description_agent = ProductDescriptionAgent()
        
        # Generate description
        description = description_agent.generate_description(product_metadata)
        
        return {
            "success": True,
            "description": description,
            "product_id": product_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool(
    "sync_product_to_vector_db",
    description="Synchronize a product to the vector database",
)
def sync_product_to_vector_db(
    ctx: Context, request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Synchronize a product to the vector database for semantic search
    
    This tool generates embeddings and stores them in Qdrant for semantic search.
    """
    try:
        # Validate request
        account_id = request.get("account_id")
        product_id = request.get("product_id")
        description = request.get("description")
        
        if not account_id or not product_id:
            return {
                "success": False,
                "error": "Missing required parameters: account_id and product_id"
            }
        
        # Get product data from Odoo if description not provided
        product_data = {}
        if not description:
            product_data = ctx.app.odoo.get_product_data(
                account_id=account_id,
                product_id=product_id
            )
            description = product_data.get("ai_generated_description") or product_data.get("semantic_description")
        
        if not description:
            return {
                "success": False,
                "error": "No description available for vectorization"
            }
        
        # Prepare metadata
        metadata = {
            "product_id": product_id,
            "name": product_data.get("name", ""),
            "category": product_data.get("category_name", ""),
            "verified": True
        }
        
        # Call Vector Service API
        import requests
        vector_service_url = os.environ.get("VECTOR_SERVICE_URL", "http://localhost:8001")
        
        response = requests.post(
            f"{vector_service_url}/api/v1/vectors",
            json={
                "account_id": account_id,
                "product_id": product_id,
                "text": description,
                "metadata": metadata
            }
        )
        
        if response.status_code != 201:
            return {
                "success": False,
                "error": f"Vector Service error: {response.text}"
            }
        
        result = response.json()
        
        # Update product in Odoo with vector ID and sync status
        ctx.app.odoo.update_product_sync_status(
            account_id=account_id,
            product_id=product_id,
            vector_id=result.get("vector_id"),
            sync_status="synced"
        )
        
        return {
            "success": True,
            "vector_id": result.get("vector_id"),
            "message": "Product successfully synchronized with vector database"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool(
    "semantic_search",
    description="Perform semantic search for products",
)
def semantic_search(
    ctx: Context, request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform semantic search for products
    
    This tool searches for products using natural language queries.
    """
    try:
        # Validate request
        account_id = request.get("account_id")
        query = request.get("query")
        limit = request.get("limit", 10)
        
        if not account_id or not query:
            return {
                "success": False,
                "error": "Missing required parameters: account_id and query"
            }
        
        # Call Vector Service API
        import requests
        vector_service_url = os.environ.get("VECTOR_SERVICE_URL", "http://localhost:8001")
        
        response = requests.post(
            f"{vector_service_url}/api/v1/search",
            json={
                "account_id": account_id,
                "query": query,
                "limit": limit
            }
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Vector Service error: {response.text}"
            }
        
        result = response.json()
        
        # Enrich results with Odoo data if needed
        enriched_results = []
        for item in result.get("results", []):
            product_id = item.get("metadata", {}).get("product_id")
            if product_id:
                product_data = ctx.app.odoo.get_product_data(
                    account_id=account_id,
                    product_id=product_id,
                    fields=["name", "list_price", "image_url"]
                )
                
                item["product_data"] = product_data
            
            enriched_results.append(item)
        
        return {
            "success": True,
            "results": enriched_results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## Próximos Passos

1. Implementar o Agente de Descrição de Produtos
2. Testar a geração de descrições com diferentes tipos de produtos
3. Implementar o Serviço de Vetorização básico
4. Integrar com MCP-Odoo
5. Testar o fluxo completo

## Considerações Futuras

1. **Suporte a Múltiplos ERPs**: Preparar o Serviço de Vetorização para receber dados de diferentes MCPs
2. **Busca Híbrida**: Implementar busca que combine vetores e filtros tradicionais
3. **Análise de Feedback**: Coletar feedback dos usuários para melhorar as descrições geradas
4. **Suporte a Imagens**: Adicionar suporte para busca por similaridade de imagens
