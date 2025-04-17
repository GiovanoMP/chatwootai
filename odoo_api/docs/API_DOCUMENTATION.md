# API Odoo - Documentação

## Visão Geral

A API Odoo é um serviço RESTful que fornece uma interface para integração entre o Odoo ERP e o sistema de IA. Esta API permite que módulos Odoo se comuniquem com o sistema de IA para realizar operações como sincronização de credenciais, gerenciamento de regras de negócio, busca semântica de produtos e muito mais.

## Arquitetura

A API Odoo é construída usando o framework FastAPI e segue uma arquitetura modular:

```
odoo/
├── api/                   # Implementação da API REST
│   ├── __init__.py
│   ├── main.py            # Ponto de entrada da API
│   ├── core/              # Componentes centrais
│   │   ├── __init__.py
│   │   ├── auth.py        # Autenticação e autorização
│   │   ├── exceptions.py  # Exceções personalizadas
│   │   └── middleware.py  # Middlewares da aplicação
│   ├── modules/           # Módulos específicos da API
│   │   ├── __init__.py
│   │   ├── business_rules/# Módulo de regras de negócio
│   │   ├── credentials/   # Módulo de gerenciamento de credenciais
│   │   └── products/      # Módulo de gerenciamento de produtos
│   └── services/          # Serviços compartilhados
│       ├── __init__.py
│       ├── cache.py       # Serviço de cache
│       └── vector.py      # Serviço de vetorização
├── connectors/            # Conectores para Odoo e outros sistemas
│   ├── __init__.py
│   ├── odoo_connector.py  # Conector para Odoo
│   └── qdrant_connector.py# Conector para Qdrant
├── models/                # Modelos de dados
│   ├── __init__.py
│   ├── business_rule.py   # Modelo de regra de negócio
│   └── product.py         # Modelo de produto
├── utils/                 # Utilitários
│   ├── __init__.py
│   ├── logging.py         # Configuração de logging
│   └── helpers.py         # Funções auxiliares
└── docs/                  # Documentação
    ├── inicializacao_rapida_servidor_unificado.md  # Guia de inicialização rápida
    └── API_REFERENCE.md   # Referência da API
```

## Tecnologias Utilizadas

- **FastAPI**: Framework web para construção de APIs
- **Pydantic**: Validação de dados e serialização
- **Redis**: Cache para melhorar o desempenho
- **Qdrant**: Banco de dados vetorial para busca semântica
- **OpenAI**: Geração de embeddings para busca semântica
- **XMLRPC**: Comunicação com o Odoo

## Módulos Disponíveis

### 1. Business Rules

Gerencia regras de negócio que podem ser usadas pelo sistema de IA para tomar decisões.

**Endpoints principais:**
- `GET /api/v1/business-rules`: Lista regras de negócio
- `POST /api/v1/business-rules`: Cria uma nova regra de negócio
- `GET /api/v1/business-rules/{rule_id}`: Obtém uma regra específica
- `PUT /api/v1/business-rules/{rule_id}`: Atualiza uma regra existente
- `DELETE /api/v1/business-rules/{rule_id}`: Remove uma regra
- `GET /api/v1/business-rules/semantic-search`: Busca semântica de regras
- `POST /api/v1/business-rules/sync`: Sincroniza regras com o sistema de IA

### 2. Credentials

Gerencia credenciais para acesso ao sistema de IA.

**Endpoints principais:**
- `POST /api/v1/credentials/sync`: Sincroniza credenciais com o sistema de IA
- `GET /api/v1/credentials/verify`: Verifica se as credenciais são válidas

### 3. Products

Gerencia produtos no Odoo.

**Endpoints principais:**
- `GET /api/v1/products`: Lista produtos
- `POST /api/v1/products`: Cria um novo produto
- `GET /api/v1/products/{product_id}`: Obtém um produto específico
- `PUT /api/v1/products/{product_id}`: Atualiza um produto existente
- `GET /api/v1/products/search`: Busca semântica de produtos
- `POST /api/v1/products/sync`: Sincroniza produtos com o sistema de IA

## Como Adicionar um Novo Módulo

Para adicionar um novo módulo à API Odoo, siga os passos abaixo:

### 1. Criar a Estrutura de Diretórios

Crie um novo diretório dentro de `odoo/api/modules/` com o nome do seu módulo:

```bash
mkdir -p odoo/api/modules/seu_modulo
touch odoo/api/modules/seu_modulo/__init__.py
```

### 2. Criar os Arquivos Básicos

Crie os seguintes arquivos dentro do diretório do seu módulo:

- `schemas.py`: Define os modelos de dados usando Pydantic
- `routes.py`: Define os endpoints da API
- `services.py`: Implementa a lógica de negócio

### 3. Definir Schemas (schemas.py)

```python
# -*- coding: utf-8 -*-

"""
Schemas para o módulo seu_modulo.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Modelo de resposta padrão da API
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None

# Modelo de requisição
class SeuModeloRequest(BaseModel):
    name: str = Field(..., description="Nome do item")
    description: str = Field(..., description="Descrição do item")
    # Adicione outros campos conforme necessário

# Modelo de resposta
class SeuModeloResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    # Adicione outros campos conforme necessário
```

### 4. Implementar Serviços (services.py)

```python
# -*- coding: utf-8 -*-

"""
Serviços para o módulo seu_modulo.
"""

import logging
from typing import Dict, List, Optional, Any

from odoo.api.core.exceptions import ValidationError, NotFoundError, OdooOperationError
from odoo.connectors.odoo_connector import OdooConnectorFactory
from odoo.api.services.cache import get_cache_service
from odoo.api.modules.seu_modulo.schemas import SeuModeloResponse, SeuModeloRequest

logger = logging.getLogger(__name__)

class SeuModuloService:
    """Serviço para o módulo seu_modulo."""

    async def get_item(self, account_id: str, item_id: int) -> SeuModeloResponse:
        """
        Obtém um item pelo ID.
        """
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Implementar lógica para obter o item
            # ...
            
            return SeuModeloResponse(...)
            
        except Exception as e:
            logger.error(f"Failed to get item: {e}")
            raise ValidationError(f"Failed to get item: {e}")
    
    # Implementar outros métodos conforme necessário

# Singleton para o serviço
_service_instance = None

async def get_seu_modulo_service() -> SeuModuloService:
    """
    Obtém uma instância do serviço.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = SeuModuloService()
    return _service_instance
```

### 5. Definir Rotas (routes.py)

```python
# -*- coding: utf-8 -*-

"""
Rotas para o módulo seu_modulo.
"""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Request

from odoo.api.core.exceptions import OdooAPIError, NotFoundError, ValidationError
from odoo.api.modules.seu_modulo.schemas import SeuModeloRequest, SeuModeloResponse, APIResponse
from odoo.api.modules.seu_modulo.services import get_seu_modulo_service

logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(
    prefix="/seu-modulo",
    tags=["seu-modulo"],
)

# Função para construir resposta padrão
def build_response(
    success: bool,
    data: Any = None,
    error: Dict[str, Any] = None,
    meta: Dict[str, Any] = None,
) -> APIResponse:
    """
    Constrói uma resposta padrão da API.
    """
    if meta is None:
        meta = {}
    
    meta["timestamp"] = time.time()
    
    return APIResponse(
        success=success,
        data=data,
        error=error,
        meta=meta,
    )

# Rota para obter um item
@router.get(
    "/{item_id}",
    response_model=APIResponse,
    summary="Obtém um item",
    description="Obtém um item pelo ID.",
)
async def get_item(
    request: Request,
    item_id: int = Path(..., description="ID do item"),
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Obtém um item pelo ID.
    """
    try:
        service = await get_seu_modulo_service()
        
        # Obter item
        result = await service.get_item(
            account_id=account_id,
            item_id=item_id,
        )
        
        # Construir resposta
        return build_response(
            success=True,
            data=result,
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )
        
    except NotFoundError as e:
        logger.warning(f"Item not found: {e}")
        raise HTTPException(
            status_code=404,
            detail={"code": getattr(e, "code", "NOT_FOUND"), "message": str(e)},
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e)},
        )
        
    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e)},
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Implementar outras rotas conforme necessário
```

### 6. Registrar o Módulo no Arquivo Principal (main.py)

Edite o arquivo `odoo/api/main.py` para incluir o seu módulo:

```python
# Importar e incluir rotas dos módulos
from odoo.api.modules.seu_modulo.routes import router as seu_modulo_router

# Incluir rotas
app.include_router(seu_modulo_router, prefix="/api/v1")
```

### 7. Atualizar o Arquivo __init__.py

Atualize o arquivo `odoo/api/modules/seu_modulo/__init__.py`:

```python
# -*- coding: utf-8 -*-

"""
Módulo seu_modulo.
"""

from odoo.api.modules.seu_modulo import routes, schemas, services
```

## Comunicação com o Módulo Odoo

Para que seu módulo Odoo se comunique com a API, você precisa implementar a lógica de comunicação no módulo Odoo. Aqui está um exemplo de como fazer isso:

```python
# No módulo Odoo
import requests
import json

def call_api(self, endpoint, method="GET", data=None, params=None):
    """
    Chama a API Odoo.
    
    Args:
        endpoint: Endpoint da API (ex: "/api/v1/seu-modulo")
        method: Método HTTP (GET, POST, PUT, DELETE)
        data: Dados para enviar no corpo da requisição
        params: Parâmetros de consulta
        
    Returns:
        Resposta da API
    """
    # Obter configurações
    base_url = self.env['ai.credentials'].get_api_url()
    token = self.env['ai.credentials'].get_api_token()
    account_id = self.env['ai.credentials'].get_account_id()
    
    # Adicionar account_id aos parâmetros
    if params is None:
        params = {}
    params['account_id'] = account_id
    
    # Construir URL
    url = f"{base_url}{endpoint}"
    
    # Configurar headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    
    # Fazer requisição
    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, params=params, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, params=params, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, params=params, headers=headers)
        else:
            raise ValueError(f"Método HTTP não suportado: {method}")
        
        # Verificar status code
        response.raise_for_status()
        
        # Retornar resposta
        return response.json()
        
    except requests.exceptions.RequestException as e:
        # Tratar erro
        raise Exception(f"Erro ao chamar API: {e}")
```

## Exemplos de Uso

### Exemplo 1: Busca Semântica de Produtos

```python
# No módulo Odoo
def search_products(self, query, limit=5, score_threshold=0.7):
    """
    Busca produtos semanticamente similares a uma consulta.
    
    Args:
        query: Consulta para busca semântica
        limit: Número máximo de resultados
        score_threshold: Limiar de similaridade (0.0 a 1.0)
        
    Returns:
        Lista de produtos
    """
    # Chamar API
    response = self.call_api(
        endpoint="/api/v1/products/search",
        method="GET",
        params={
            "query": query,
            "limit": limit,
            "score_threshold": score_threshold,
        },
    )
    
    # Verificar sucesso
    if not response.get("success"):
        error = response.get("error", {})
        raise Exception(f"Erro na busca semântica: {error.get('message')}")
    
    # Retornar dados
    return response.get("data", [])
```

### Exemplo 2: Sincronização de Credenciais

```python
# No módulo Odoo
def sync_credentials(self):
    """
    Sincroniza credenciais com o sistema de IA.
    
    Returns:
        True se a sincronização foi bem-sucedida
    """
    # Obter dados das credenciais
    credentials_data = {
        "api_key": self.api_key,
        "api_secret": self.api_secret,
        "domain": self.domain,
        "business_area": self.business_area,
        "company_name": self.company_name,
        # Adicionar outros campos conforme necessário
    }
    
    # Chamar API
    response = self.call_api(
        endpoint="/api/v1/credentials/sync",
        method="POST",
        data=credentials_data,
    )
    
    # Verificar sucesso
    if not response.get("success"):
        error = response.get("error", {})
        raise Exception(f"Erro na sincronização de credenciais: {error.get('message')}")
    
    # Retornar sucesso
    return True
```

## Boas Práticas para Desenvolvimento de Módulos

1. **Separação de Responsabilidades**:
   - `schemas.py`: Define os modelos de dados
   - `routes.py`: Define os endpoints da API
   - `services.py`: Implementa a lógica de negócio

2. **Tratamento de Erros**:
   - Use exceções específicas (`ValidationError`, `NotFoundError`, etc.)
   - Registre erros com o logger
   - Retorne respostas de erro padronizadas

3. **Documentação**:
   - Documente todas as funções e classes
   - Use docstrings para descrever parâmetros e retornos
   - Adicione descrições aos endpoints da API

4. **Validação de Dados**:
   - Use Pydantic para validar dados de entrada e saída
   - Defina restrições e validações nos modelos

5. **Cache**:
   - Use o serviço de cache para operações frequentes
   - Defina TTLs apropriados para os dados em cache

6. **Segurança**:
   - Verifique sempre o `account_id` nas requisições
   - Valide permissões de acesso quando necessário

## Documentação

A documentação completa está disponível na pasta `docs/`:

- [Inicialização Rápida do Servidor Unificado](docs/inicializacao_rapida_servidor_unificado.md): Guia passo a passo para inicializar o servidor unificado
- [Referência da API](docs/API_REFERENCE.md): Documentação detalhada dos endpoints da API

## Solução de Problemas

### Problema: Erro de Conexão com a API

Verifique se:
1. O servidor da API está rodando
2. A URL da API está correta
3. O token de autenticação é válido
4. O account_id está sendo passado corretamente

### Problema: Erro de Validação de Dados

Verifique se:
1. Os dados enviados estão no formato correto
2. Todos os campos obrigatórios estão presentes
3. Os valores dos campos estão dentro dos limites esperados

### Problema: Erro no Odoo

Verifique se:
1. O conector Odoo está configurado corretamente
2. As credenciais do Odoo são válidas
3. O modelo Odoo existe e tem os campos esperados

## Recursos Adicionais

- [Documentação do FastAPI](https://fastapi.tiangolo.com/)
- [Documentação do Pydantic](https://pydantic-docs.helpmanual.io/)
- [Documentação do Odoo XML-RPC](https://www.odoo.com/documentation/14.0/developer/reference/external_api.html)
- [Documentação do Qdrant](https://qdrant.tech/documentation/)
