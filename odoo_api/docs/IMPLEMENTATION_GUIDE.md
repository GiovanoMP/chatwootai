# Guia de Implementação para Novos Módulos

Este guia descreve como implementar novos módulos na API para integração com módulos Odoo.

## Visão Geral

Para implementar um novo módulo na API, você precisa seguir estes passos:

1. Criar um agente de embedding específico para o módulo
2. Implementar os serviços do módulo
3. Implementar as rotas da API
4. Implementar os esquemas de dados
5. Implementar os testes

## 1. Criar Agente de Embedding

O agente de embedding é responsável por processar dados brutos antes da geração de embeddings, melhorando a qualidade dos vetores gerados.

### Estrutura do Arquivo

Crie um novo arquivo em `odoo_api/embedding_agents/` com o nome do módulo, por exemplo, `product_description_agent.py`:

```python
"""
Agente de embedding para descrições de produtos.

Este módulo implementa um agente para processamento de descrições de produtos
antes da geração de embeddings.
"""

import json
import logging
from typing import Dict, Any, Optional

from odoo_api.core.interfaces.embedding_agent import EmbeddingAgent
from odoo_api.core.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

class ProductDescriptionEmbeddingAgent(EmbeddingAgent):
    """
    Agente para processamento de descrições de produtos para embeddings.
    
    Este agente utiliza um LLM para estruturar e enriquecer os dados brutos
    de produtos antes de enviá-los para o serviço de embeddings,
    melhorando a qualidade dos vetores gerados.
    """
    
    async def process_data(
        self, 
        data: Dict[str, Any], 
        business_area: Optional[str] = None
    ) -> str:
        """
        Processa dados de produto para vetorização.
        
        Args:
            data: Dados brutos do produto
            business_area: Área de negócio da empresa (opcional)
            
        Returns:
            Texto enriquecido pronto para vetorização
        """
        # Implementar lógica específica para o módulo
        # ...

# Singleton para o agente
_product_description_agent_instance = None

async def get_product_description_agent() -> ProductDescriptionEmbeddingAgent:
    """
    Obtém uma instância do agente de embeddings para descrições de produtos.
    
    Returns:
        Instância do agente de embeddings
    """
    global _product_description_agent_instance
    
    if _product_description_agent_instance is None:
        _product_description_agent_instance = ProductDescriptionEmbeddingAgent()
    
    return _product_description_agent_instance
```

### Implementação do Método `process_data`

O método `process_data` é o coração do agente de embedding. Ele recebe dados brutos e retorna um texto rico para vetorização.

```python
async def process_data(
    self, 
    data: Dict[str, Any], 
    business_area: Optional[str] = None
) -> str:
    """
    Processa dados para vetorização.
    
    Args:
        data: Dados brutos
        business_area: Área de negócio da empresa (opcional)
        
    Returns:
        Texto enriquecido pronto para vetorização
    """
    # Construir o prompt para o agente
    system_prompt = """
    Você é um especialista em processamento de dados para sistemas de IA.
    Sua tarefa é transformar os dados brutos em um texto rico e contextualizado
    para vetorização, seguindo estas diretrizes:
    
    1. [Diretrizes específicas do módulo]
    2. [...]
    
    Formate o texto final de forma que capture a essência dos dados.
    """
    
    # Adicionar contexto da área de negócio, se disponível
    if business_area:
        system_prompt += f"\nEstes dados pertencem à área de negócio: {business_area}. Considere o contexto desta indústria."
    
    # Preparar os dados em formato legível
    formatted_data = self._format_data(data)
    
    # Chamar o LLM para processar os dados
    user_prompt = f"Processe os seguintes dados para vetorização:\n\n{formatted_data}"
    
    openai_service = await get_openai_service()
    response = await openai_service.generate_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1000,
        temperature=0.2  # Baixa temperatura para respostas mais determinísticas
    )
    
    return response.strip()
```

## 2. Implementar Serviços do Módulo

Os serviços do módulo implementam a lógica de negócio específica do módulo.

### Estrutura do Diretório

Crie um novo diretório em `odoo_api/modules/` com o nome do módulo, por exemplo, `product_description/`:

```
odoo_api/modules/product_description/
  ├── __init__.py
  ├── services.py
  ├── routes.py
  └── schemas.py
```

### Implementação do Serviço

Crie um arquivo `services.py` com a implementação do serviço:

```python
"""
Serviços para o módulo Product Description.

Este módulo implementa os serviços para o módulo Product Description,
incluindo geração e sincronização de descrições de produtos.
"""

import logging
from typing import Dict, List, Optional, Any

from odoo_api.core.domain.exceptions import ValidationError, NotFoundError
from odoo_api.core.domain.odoo_connector import OdooConnectorFactory
from odoo_api.core.services.cache_service import get_cache_service
from odoo_api.core.services.vector_service import get_vector_service
from odoo_api.embedding_agents.product_description_agent import get_product_description_agent
from odoo_api.modules.product_description.schemas import (
    ProductRequest,
    ProductResponse,
    ProductListResponse,
    ProductSyncResponse,
)

logger = logging.getLogger(__name__)

class ProductDescriptionService:
    """Serviço para o módulo Product Description."""
    
    async def generate_description(
        self,
        account_id: str,
        product_id: int,
    ) -> ProductResponse:
        """
        Gera uma descrição rica para um produto.
        
        Args:
            account_id: ID da conta
            product_id: ID do produto
            
        Returns:
            Produto com descrição gerada
        """
        # Implementar lógica específica para o módulo
        # ...
```

## 3. Implementar Rotas da API

As rotas da API definem os endpoints para interação com o módulo.

### Implementação das Rotas

Crie um arquivo `routes.py` com a implementação das rotas:

```python
"""
Rotas da API para o módulo Product Description.

Este módulo implementa as rotas da API para o módulo Product Description,
incluindo geração e sincronização de descrições de produtos.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from odoo_api.modules.product_description.services import ProductDescriptionService
from odoo_api.modules.product_description.schemas import (
    ProductRequest,
    ProductResponse,
    ProductListResponse,
    ProductSyncResponse,
)

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/{account_id}/generate_description/{product_id}")
async def generate_description(
    account_id: str,
    product_id: int,
):
    """
    Gera uma descrição rica para um produto.
    
    Args:
        account_id: ID da conta
        product_id: ID do produto
        
    Returns:
        Produto com descrição gerada
    """
    service = ProductDescriptionService()
    
    try:
        result = await service.generate_description(account_id, product_id)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 4. Implementar Esquemas de Dados

Os esquemas de dados definem a estrutura dos dados do módulo.

### Implementação dos Esquemas

Crie um arquivo `schemas.py` com a implementação dos esquemas:

```python
"""
Esquemas de dados para o módulo Product Description.

Este módulo define os esquemas de dados para o módulo Product Description,
incluindo requisições e respostas.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class ProductRequest(BaseModel):
    """Requisição para criação/atualização de produto."""
    
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    list_price: Optional[float] = None
    # Outros campos específicos do módulo
    
class ProductResponse(BaseModel):
    """Resposta para produto."""
    
    id: int
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    list_price: Optional[float] = None
    ai_description: Optional[str] = None
    # Outros campos específicos do módulo
    
class ProductListResponse(BaseModel):
    """Resposta para lista de produtos."""
    
    total: int
    limit: int
    offset: int
    products: List[ProductResponse]
    
class ProductSyncResponse(BaseModel):
    """Resposta para sincronização de produtos."""
    
    sync_status: str
    products_count: int
    vectorized_products: int
    timestamp: str
    error: Optional[str] = None
```

## 5. Implementar Testes

Os testes garantem que o módulo funcione corretamente.

### Testes Unitários

Crie um arquivo `test_product_description_agent.py` em `odoo_api/tests/unit/`:

```python
"""
Testes unitários para o agente de embedding de descrições de produtos.

Este módulo contém testes para verificar o funcionamento do agente de embedding
de descrições de produtos.
"""

import asyncio
import os
import sys
import unittest
from typing import Dict, Any

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from odoo_api.embedding_agents.product_description_agent import get_product_description_agent

class TestProductDescriptionAgent(unittest.TestCase):
    """Testes para o agente de embedding de descrições de produtos."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.loop = asyncio.get_event_loop()
        
        # Dados de teste
        self.product = {
            "id": 1,
            "name": "Smartphone XYZ",
            "description": "Smartphone com tela de 6.5 polegadas, 128GB de armazenamento e 8GB de RAM.",
            "category_id": 1,
            "list_price": 1999.99,
            # Outros campos específicos do módulo
        }
    
    def test_process_data(self):
        """Testar processamento de dados do produto."""
        async def _test():
            # Obter agente
            agent = await get_product_description_agent()
            
            # Testar processamento sem área de negócio
            processed_text = await agent.process_data(self.product)
            
            # Verificar se contém informações importantes
            self.assertIn("Smartphone XYZ", processed_text)
            self.assertIn("6.5 polegadas", processed_text)
            self.assertIn("128GB", processed_text)
            self.assertIn("8GB", processed_text)
            
            # Testar processamento com área de negócio
            business_area = "loja de eletrônicos"
            processed_text_with_area = await agent.process_data(
                self.product,
                business_area
            )
            
            # Verificar se contém informações importantes
            self.assertIn("Smartphone XYZ", processed_text_with_area)
            self.assertIn("6.5 polegadas", processed_text_with_area)
            self.assertIn("128GB", processed_text_with_area)
            self.assertIn("8GB", processed_text_with_area)
            
            # Verificar se o contexto da área de negócio foi considerado
            self.assertIn("eletrônicos", processed_text_with_area.lower())
        
        self.loop.run_until_complete(_test())
```

### Testes de Integração

Crie um arquivo `test_product_description_service.py` em `odoo_api/tests/integration/`:

```python
"""
Testes de integração para o serviço de Product Description.

Este módulo contém testes para verificar o funcionamento do serviço de Product Description,
incluindo a integração com o agente de embedding e os serviços de vetorização e cache.
"""

import asyncio
import os
import sys
import unittest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from odoo_api.modules.product_description.services import ProductDescriptionService
from odoo_api.modules.product_description.schemas import ProductResponse
from odoo_api.core.services.vector_service import get_vector_service
from odoo_api.core.services.cache_service import get_cache_service
from odoo_api.embedding_agents.product_description_agent import get_product_description_agent

class TestProductDescriptionService(unittest.TestCase):
    """Testes para o serviço de Product Description."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.loop = asyncio.get_event_loop()
        self.account_id = "account_test"
        
        # Criar serviço
        self.service = ProductDescriptionService()
        
        # Dados de teste
        self.test_products = [
            ProductResponse(
                id=1,
                name="Smartphone XYZ",
                description="Smartphone com tela de 6.5 polegadas, 128GB de armazenamento e 8GB de RAM.",
                category_id=1,
                list_price=1999.99,
                # Outros campos específicos do módulo
            ),
            # Outros produtos de teste
        ]
    
    # Implementar testes específicos para o módulo
    # ...
```

## 6. Registrar Rotas

Para que as rotas do módulo sejam acessíveis, você precisa registrá-las no roteador principal da API.

### Atualizar o Arquivo `main.py`

Atualize o arquivo `odoo_api/main.py` para incluir as rotas do novo módulo:

```python
from fastapi import FastAPI
from odoo_api.modules.business_rules.routes import router as business_rules_router
from odoo_api.modules.product_description.routes import router as product_description_router

app = FastAPI(title="Odoo API", version="1.0.0")

app.include_router(business_rules_router, prefix="/api/v1")
app.include_router(product_description_router, prefix="/api/v1")
```

## Conclusão

Seguindo este guia, você pode implementar novos módulos na API para integração com módulos Odoo. Lembre-se de:

1. Seguir a estrutura de diretórios e arquivos
2. Implementar a interface `EmbeddingAgent` para o agente de embedding
3. Criar serviços, rotas e esquemas específicos para o módulo
4. Implementar testes unitários e de integração
5. Registrar as rotas no roteador principal da API

Isso garantirá que o novo módulo seja consistente com a arquitetura do sistema e funcione corretamente.
