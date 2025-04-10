# Integração de Busca Semântica para Odoo e IA

![Versão](https://img.shields.io/badge/versão-1.0-blue)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

## Visão Geral

Este documento detalha a arquitetura e implementação da integração de busca semântica entre o Odoo ERP e sistemas de IA, utilizando Qdrant para busca vetorial, OpenAI para embeddings, e Redis para cache. A solução é composta por dois componentes principais:

1. **Módulo Odoo `semantic_product_description`**: Extensão para o Odoo que adiciona campos estruturados para descrições semânticas de produtos
2. **Módulo Python `vector_search`**: Implementação da lógica de busca semântica, integrada ao MCP-Odoo existente

Esta arquitetura permite que agentes de IA (via CrewAI) realizem buscas semânticas precisas em produtos do Odoo, combinando a compreensão de linguagem natural com a estrutura de dados do ERP.

## Parte 1: Módulo Odoo `semantic_product_description`

### Propósito

O módulo `semantic_product_description` estende o modelo de produto do Odoo para incluir campos estruturados que enriquecem a busca semântica:

- **Descrição Semântica**: Texto conciso e estruturado otimizado para busca vetorial
- **Características Principais**: Lista de atributos-chave do produto
- **Casos de Uso**: Cenários comuns de utilização do produto
- **Verificação Humana**: Fluxo de trabalho para garantir precisão das descrições

### Arquitetura do Módulo Odoo

```
semantic_product_description/
├── __init__.py                  # Inicialização do módulo
├── __manifest__.py              # Metadados e dependências
├── models/
│   ├── __init__.py              # Inicialização dos modelos
│   └── product_template.py      # Extensão do modelo product.template
└── views/
    └── product_template_views.xml  # Interface do usuário
```

### Integração com Módulos Odoo Existentes

O módulo depende de:
- **`product`**: Módulo base que define o modelo `product.template`
- **`sale`**: Módulo de vendas que contém campos como `description_sale`

### Campos Adicionados ao Modelo de Produto

```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    semantic_description = fields.Text(
        string='Descrição Semântica',
        help='Descrição concisa e estruturada do produto para busca semântica'
    )
    
    key_features = fields.Text(
        string='Características Principais',
        help='Lista de características principais do produto, uma por linha'
    )
    
    use_cases = fields.Text(
        string='Casos de Uso',
        help='Cenários de uso comuns para este produto, um por linha'
    )
    
    semantic_description_last_update = fields.Datetime(
        string='Última Atualização da Descrição Semântica',
        readonly=True
    )
    
    semantic_description_verified = fields.Boolean(
        string='Descrição Verificada',
        default=False,
        help='Indica se a descrição semântica foi verificada por um humano'
    )
```

### Interface do Usuário

O módulo adiciona uma nova aba "Descrição Semântica" na tela de produto com:

- Campo de texto para descrição semântica
- Campo de texto para características principais (uma por linha)
- Campo de texto para casos de uso (um por linha)
- Indicador de verificação humana
- Botões para gerar descrição automaticamente e marcar como verificado

### Funcionalidades Principais

1. **Geração Automática de Descrições**:
   ```python
   @api.model
   def generate_semantic_description(self):
       """Gera automaticamente uma descrição semântica baseada nos metadados do produto."""
       for product in self:
           # Coletar metadados
           name = product.name
           category = product.categ_id.name if product.categ_id else ""
           attributes = []
           for attr_line in product.attribute_line_ids:
               attr_name = attr_line.attribute_id.name
               attr_values = ", ".join([v.name for v in attr_line.value_ids])
               attributes.append(f"{attr_name}: {attr_values}")
           
           # Gerar descrição estruturada
           description = f"{name} é um produto da categoria {category}. "
           
           if product.description_sale:
               description += product.description_sale + " "
           
           if attributes:
               description += "Disponível com as seguintes características: " + "; ".join(attributes) + "."
           
           # Atualizar o produto
           product.write({
               'semantic_description': description,
               'semantic_description_last_update': fields.Datetime.now(),
               'semantic_description_verified': False  # Requer verificação humana
           })
   ```

2. **Verificação Humana**:
   ```python
   def verify_semantic_description(self):
       """Marca a descrição semântica como verificada."""
       self.ensure_one()
       self.write({
           'semantic_description_verified': True
       })
   ```

## Parte 2: Módulo Python `vector_search`

### Propósito

O módulo `vector_search` implementa a lógica de busca semântica, integrando-se ao MCP-Odoo existente para:

1. Extrair metadados estruturados do Odoo
2. Gerar embeddings via OpenAI
3. Indexar produtos no Qdrant
4. Realizar buscas híbridas (dense + sparse vectors)
5. Cachear resultados no Redis

### Arquitetura do Módulo

```
src/vector_search/
├── __init__.py
├── config.py                # Configurações do módulo
├── models/
│   ├── __init__.py
│   ├── product_metadata.py  # Modelos para metadados de produtos
│   └── vector_mapping.py    # Mapeamento entre IDs de produtos e vetores
├── services/
│   ├── __init__.py
│   ├── embedding_service.py # Serviço de embeddings via OpenAI
│   ├── metadata_service.py  # Serviço de extração de metadados
│   ├── sync_service.py      # Serviço de sincronização
│   └── search_service.py    # Serviço de busca
├── utils/
│   ├── __init__.py
│   ├── redis_client.py      # Cliente Redis
│   └── qdrant_client.py     # Cliente Qdrant
└── cli/
    ├── __init__.py
    └── commands.py          # Comandos CLI para sincronização e busca
```

### Componentes Principais

#### 1. Serviço de Embeddings

```python
class EmbeddingService:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Inicializa o serviço de embeddings.
        
        Args:
            api_key: Chave da API OpenAI
            model: Modelo de embedding a ser usado
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Gera um embedding para o texto fornecido.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            List[float]: Vetor de embedding
        """
        try:
            response = openai.Embedding.create(
                input=text,
                model=self.model
            )
            return response["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {str(e)}")
            raise
    
    def generate_product_embedding(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera embedding para um produto com base em seus dados semânticos.
        
        Args:
            product_data: Dados do produto obtidos do MCP-Odoo
            
        Returns:
            Dict: Dados do produto com embedding adicionado
        """
        # Construir texto para embedding
        text_parts = []
        
        # Nome e categoria são fundamentais
        text_parts.append(f"Produto: {product_data['name']}")
        text_parts.append(f"Categoria: {product_data['category_name']}")
        
        # Descrição semântica verificada tem prioridade
        if product_data.get('semantic_description') and product_data.get('verified'):
            text_parts.append(f"Descrição: {product_data['semantic_description']}")
        # Caso contrário, usar descrição de venda
        elif product_data.get('description_sale'):
            text_parts.append(f"Descrição: {product_data['description_sale']}")
        
        # Adicionar características principais
        if product_data.get('key_features'):
            features = product_data['key_features'].split('\n')
            features = [f.strip() for f in features if f.strip()]
            if features:
                text_parts.append("Características principais:")
                text_parts.extend(features)
        
        # Adicionar casos de uso
        if product_data.get('use_cases'):
            use_cases = product_data['use_cases'].split('\n')
            use_cases = [u.strip() for u in use_cases if u.strip()]
            if use_cases:
                text_parts.append("Casos de uso:")
                text_parts.extend(use_cases)
        
        # Adicionar atributos e variantes
        if product_data.get('attributes'):
            text_parts.append("Atributos e variantes:")
            for attr in product_data['attributes']:
                values = ", ".join([v['value_name'] for v in attr['values']])
                text_parts.append(f"{attr['attribute_name']}: {values}")
        
        # Adicionar tags
        if product_data.get('tags'):
            tags = [tag['tag_name'] for tag in product_data['tags']]
            text_parts.append(f"Tags: {', '.join(tags)}")
        
        # Juntar tudo em um texto
        full_text = "\n".join(text_parts)
        
        # Gerar embedding
        try:
            embedding = self.generate_embedding(full_text)
            
            # Adicionar embedding e texto usado aos dados do produto
            result = product_data.copy()
            result['embedding'] = embedding
            result['embedding_text'] = full_text
            result['embedding_model'] = self.model
            
            return result
        except Exception as e:
            logger.error(f"Erro ao gerar embedding para produto {product_data['id']}: {str(e)}")
            # Retornar dados originais sem embedding em caso de erro
            return product_data
```

#### 2. Serviço de Sincronização

```python
class ProductSyncService:
    def __init__(self, redis_client, vector_store, embed_model, mcp_client):
        self.redis = redis_client
        self.vector_store = vector_store
        self.embed_model = embed_model
        self.mcp_client = mcp_client
        self.metadata_service = MetadataService(mcp_client)
        
    def sync_product(self, account_id, product_id, force=False):
        """Sincroniza um produto específico com o Qdrant."""
        # Verificar cache e estado de sincronização
        vector_id = self._get_product_vector_id(account_id, product_id)
        
        if not force and vector_id:
            # Verificar se o produto foi modificado desde a última sincronização
            last_sync = self._get_last_sync_timestamp(account_id, product_id)
            product_data = self.mcp_client.get_product_semantic_data(account_id, product_id)
            
            if product_data.get('write_date'):
                write_timestamp = datetime.fromisoformat(product_data['write_date']).timestamp()
                if write_timestamp <= last_sync:
                    logger.info(f"Produto {product_id} não foi modificado desde a última sincronização.")
                    return vector_id
        
        # Extrair metadados estruturados
        product_data = self.mcp_client.get_product_semantic_data(account_id, product_id)
        metadata = self.metadata_service.extract_product_metadata(product_data)
        
        # Gerar contexto enriquecido
        enhanced_context = self.metadata_service.generate_enhanced_context(product_data)
        
        # Gerar embedding
        product_with_embedding = self.embed_model.generate_product_embedding(product_data)
        
        # Indexar no Qdrant
        vector_id = self._index_product(account_id, product_id, product_with_embedding, enhanced_context, metadata)
        
        # Atualizar cache
        self._set_product_vector_id(account_id, product_id, vector_id)
        self._set_last_sync_timestamp(account_id, product_id)
        
        return vector_id
        
    def sync_all_products(self, account_id, batch_size=100):
        """Sincroniza todos os produtos de um account_id com o Qdrant."""
        # Obter lista de produtos via MCP-Odoo
        product_ids = self.mcp_client.get_all_product_ids(account_id)
        
        total = len(product_ids)
        logger.info(f"Sincronizando {total} produtos para account_id {account_id}")
        
        # Processar em lotes para evitar sobrecarga
        synced_count = 0
        for i in range(0, total, batch_size):
            batch = product_ids[i:i+batch_size]
            for product_id in batch:
                try:
                    self.sync_product(account_id, product_id)
                    synced_count += 1
                    logger.info(f"Sincronizado produto {product_id} ({i+batch.index(product_id)+1}/{total})")
                except Exception as e:
                    logger.error(f"Erro ao sincronizar produto {product_id}: {str(e)}")
        
        # Atualizar timestamp de sincronização global
        self._set_last_sync_timestamp(account_id)
        logger.info(f"Sincronização concluída para account_id {account_id}: {synced_count} produtos sincronizados")
        
        return synced_count
```

#### 3. Serviço de Busca

```python
class ProductSearchService:
    def __init__(self, redis_client, vector_store, embed_model, mcp_client):
        self.redis = redis_client
        self.vector_store = vector_store
        self.embed_model = embed_model
        self.mcp_client = mcp_client
    
    def search_products(self, account_id, query, filters=None, top_k=5, hybrid_alpha=0.5):
        """
        Realiza uma busca semântica de produtos.
        
        Args:
            account_id: ID da conta no Chatwoot
            query: Consulta em linguagem natural
            filters: Dicionário com filtros (categorias, tags, etc.)
            top_k: Número de resultados a retornar
            hybrid_alpha: Peso da busca híbrida (0 = apenas sparse, 1 = apenas dense)
            
        Returns:
            Lista de produtos encontrados com suas informações
        """
        # Verificar cache primeiro
        cache_key = f"search:{account_id}:{query}:{json.dumps(filters or {})}:{top_k}:{hybrid_alpha}"
        cached_results = self.redis.get(cache_key)
        
        if cached_results:
            return json.loads(cached_results)
        
        # Gerar embedding para a consulta
        query_embedding = self.embed_model.generate_embedding(query)
        
        # Preparar filtros
        qdrant_filters = self._prepare_filters(account_id, filters)
        
        # Executar busca híbrida no Qdrant
        search_results = self.vector_store.search(
            query_vector=query_embedding,
            query_filter=qdrant_filters,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
            hybrid_alpha=hybrid_alpha
        )
        
        # Processar resultados
        processed_results = []
        for result in search_results:
            product_id = result.payload.get("product_id")
            if product_id:
                # Obter dados completos do produto via MCP-Odoo
                product_data = self.mcp_client.get_product_details(account_id, product_id)
                
                # Adicionar score de relevância
                product_data["relevance_score"] = result.score
                
                # Adicionar contexto enriquecido
                product_data["enhanced_context"] = result.payload.get("enhanced_context", "")
                
                processed_results.append(product_data)
        
        # Armazenar em cache por 1 hora
        self.redis.setex(cache_key, 3600, json.dumps(processed_results))
        
        return processed_results
```

## Parte 3: Integração com MCP-Odoo

### Abordagem Híbrida

A integração com o MCP-Odoo existente segue uma abordagem híbrida:

1. **Extensão do MCP-Odoo**: Adicionamos ferramentas (tools) específicas para busca semântica
2. **Módulo Separado**: Mantemos a lógica complexa de embeddings e interação com Qdrant em um módulo separado

### Extensão do MCP-Odoo

```python
# Em src/mcp_odoo/server.py (adicionar novas ferramentas)

# Importar o serviço de busca semântica
from src.vector_search.services.search_service import ProductSearchService

# Inicializar o serviço de busca semântica no contexto da aplicação
@asynccontextmanager
async def app_lifespan(_: FastMCP) -> AsyncIterator[AppContext]:
    """Application lifespan for initialization and cleanup"""
    # Initialize Odoo client on startup
    odoo_client = get_odoo_client()
    
    # Initialize semantic search service
    search_service = ProductSearchService()
    
    try:
        yield AppContext(odoo=odoo_client, search_service=search_service)
    finally:
        # Cleanup if needed
        pass

# Adicionar ferramenta para busca semântica de produtos
@mcp.tool(
    "search_products_semantic",
    description="Search products using semantic search with natural language queries",
)
def search_products_semantic(
    ctx: Context, request: SemanticSearchRequest
) -> Dict[str, Any]:
    """
    Search products using semantic search with natural language queries
    
    This tool uses a hybrid search approach combining dense vectors (embeddings)
    and sparse vectors (BM42) for optimal results.
    """
    try:
        # Get the search service from context
        search_service = ctx.app.search_service
        
        # Perform semantic search
        results = search_service.search_products(
            account_id=request.account_id,
            query=request.query,
            filters=request.filters,
            top_k=request.limit,
            hybrid_alpha=request.hybrid_alpha
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Adicionar ferramenta para sincronização de produtos
@mcp.tool(
    "sync_products_to_vector_db",
    description="Synchronize products from Odoo to vector database for semantic search",
)
def sync_products_to_vector_db(
    ctx: Context, request: SyncProductsRequest
) -> Dict[str, Any]:
    """
    Synchronize products from Odoo to vector database for semantic search
    """
    try:
        # Get the search service from context
        search_service = ctx.app.search_service
        
        # Perform synchronization
        if request.product_ids:
            # Sync specific products
            results = []
            for product_id in request.product_ids:
                result = search_service.sync_product(
                    account_id=request.account_id,
                    product_id=product_id,
                    force=request.force
                )
                results.append({"product_id": product_id, "success": result is not None})
            
            return {
                "success": True,
                "message": f"Synchronized {len(results)} products",
                "results": results
            }
        else:
            # Sync all products
            count = search_service.sync_all_products(
                account_id=request.account_id,
                force=request.force
            )
            
            return {
                "success": True,
                "message": f"Synchronized {count} products"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### Integração com DataProxyAgent

```python
# Em src/core/agents/data_proxy_agent.py

def search_products_semantic(self, query, account_id, domain, filters=None):
    """
    Busca produtos usando busca semântica com consultas em linguagem natural.
    
    Args:
        query: Consulta em linguagem natural
        account_id: ID da conta
        domain: Nome do domínio
        filters: Filtros opcionais (categoria, tags, etc.)
        
    Returns:
        Lista de produtos encontrados
    """
    try:
        # Preparar a requisição para o MCP
        request = {
            "query": query,
            "account_id": account_id,
            "domain": domain,
            "filters": filters or {},
            "limit": 10,
            "hybrid_alpha": 0.5  # Balanceamento entre vetores densos e esparsos
        }
        
        # Chamar a ferramenta do MCP
        response = self.mcp_client.call_tool("search_products_semantic", request)
        
        if response.get("success"):
            return response.get("results", [])
        else:
            self.logger.error(f"Error in semantic search: {response.get('error')}")
            return []
    except Exception as e:
        self.logger.error(f"Exception in semantic search: {str(e)}")
        return []
```

## Fluxo de Dados na Arquitetura Proposta

```
┌─────────────┐     ┌───────────────────┐     ┌─────────────┐
│             │     │                   │     │             │
│   Odoo ERP  │◄────┤   MCP-Odoo API    │◄────┤  CrewAI    │
│             │     │   (Estendido)     │     │  Agents     │
└──────┬──────┘     └─────────┬─────────┘     └──────┬──────┘
       │                      │                      │
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐     ┌───────────────────┐     ┌─────────────┐
│              │     │                   │     │             │
│  Odoo Module │     │  Vector Search    │     │ DataProxy   │
│  Semantic    │────►│  Module           │◄────┤ Agent       │
│  Descriptions│     │  (Independente)   │     │ (Adaptado)  │
└──────────────┘     └─────────┬─────────┘     └─────────────┘
                               │
                               │
                               ▼
                      ┌─────────────────┐
                      │                 │
                      │  Redis + Qdrant │
                      │                 │
                      └─────────────────┘
```

## Vantagens da Abordagem Híbrida

1. **Modularidade**: Mantém a lógica complexa de embeddings e busca vetorial em um módulo separado
2. **Integração Consistente**: Utiliza o MCP-Odoo como ponto de entrada para todas as operações de dados
3. **Reutilização**: Aproveita a infraestrutura existente de autenticação e configuração
4. **Escalabilidade**: Permite escalar o serviço de busca vetorial independentemente
5. **Manutenção**: Facilita a manutenção e evolução de cada componente
6. **Performance**: Minimiza o impacto no servidor MCP principal

## Considerações de Implementação

### 1. Configuração Multi-Tenant

A solução suporta a arquitetura multi-tenant existente:

- Cada **domínio** representa um modelo de negócio (furniture, cosmetics, etc.)
- Cada **account_id** representa um cliente específico dentro daquele domínio
- As configurações são carregadas de `@config/<domínio>/<account_id>.yaml`

### 2. Gestão de Dependências

O módulo `vector_search` depende de:

- **llama-index**: Para integração com Qdrant e processamento de embeddings
- **qdrant-client**: Para comunicação com o Qdrant
- **redis**: Para cache e controle de estado
- **openai**: Para geração de embeddings

### 3. Considerações de Performance

- **Processamento em Lotes**: Sincronização em lotes para evitar sobrecarga
- **Cache em Redis**: Redução de chamadas repetitivas à API OpenAI e ao Odoo
- **Busca Híbrida**: Balanceamento entre precisão semântica e performance
- **Sincronização Incremental**: Atualização apenas de produtos modificados

## Roadmap de Implementação

### Fase 1: Fundação (Semanas 1-2)

- [x] Desenvolvimento do módulo de extensão do Odoo
- [ ] Implementação da estrutura básica do serviço de sincronização
- [ ] Configuração do Qdrant com suporte a BM42

### Fase 2: Sincronização (Semanas 3-4)

- [ ] Implementação completa do serviço de sincronização
- [ ] Integração com Redis para cache e controle de estado
- [ ] Testes de sincronização com dados reais

### Fase 3: Busca Semântica (Semanas 5-6)

- [ ] Implementação do serviço de busca híbrida
- [ ] Integração com o DataProxyAgent
- [ ] Testes de performance e precisão

### Fase 4: Otimização e Monitoramento (Semanas 7-8)

- [ ] Implementação de dashboard de monitoramento
- [ ] Otimização de performance
- [ ] Documentação completa

## Conclusão

A arquitetura proposta oferece uma solução robusta e escalável para integrar busca semântica ao Odoo ERP, permitindo que agentes de IA realizem consultas em linguagem natural e obtenham resultados precisos e contextualizados.

A abordagem híbrida, combinando um módulo Odoo para enriquecimento de dados com um módulo Python para busca vetorial, e integrando ambos através do MCP-Odoo existente, oferece o melhor equilíbrio entre integração e separação de responsabilidades.

---

## Apêndice: Comandos Úteis

```bash
# Instalar o módulo Odoo
cd /path/to/odoo/addons
git clone https://github.com/your-repo/semantic_product_description.git
# Atualizar lista de módulos no Odoo e instalar

# Iniciar sincronização inicial para um account_id
python -m src.vector_search.cli sync-all --account-id 2

# Verificar status da sincronização
python -m src.vector_search.cli status --account-id 2

# Testar busca semântica
python -m src.vector_search.cli search --account-id 2 --query "sofá de couro confortável"
```

---

Desenvolvido com ❤️ pela Equipe ChatwootAI
