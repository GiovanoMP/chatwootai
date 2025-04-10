# Integração de Busca Semântica entre Odoo e IA

![Versão](https://img.shields.io/badge/versão-1.0-blue)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

## Visão Geral

Este documento detalha a arquitetura e implementação da integração entre o Odoo ERP e sistemas de IA através de busca semântica utilizando Qdrant, OpenAI e CrewAI. O objetivo é criar uma camada de busca semântica altamente eficiente que permita aos agentes de IA acessar e compreender dados de produtos do Odoo de forma contextual e precisa.

## Arquitetura da Solução

A arquitetura proposta implementa uma abordagem híbrida de busca semântica que combina:

1. **Vetores Densos** (embeddings via OpenAI) para compreensão semântica profunda
2. **Vetores Esparsos** (BM42) para correspondência precisa de palavras-chave
3. **Metadados Estruturados** para filtragem e contexto adicional

### Diagrama de Arquitetura

```
┌─────────────┐     ┌───────────────────┐     ┌─────────────┐
│             │     │                   │     │             │
│   Odoo ERP  │◄────┤   MCP-Odoo API    │◄────┤  CrewAI    │
│             │     │                   │     │  Agents     │
└──────┬──────┘     └───────────────────┘     └──────┬──────┘
       │                                             │
       │                                             │
       ▼                                             ▼
┌──────────────┐     ┌───────────────────┐     ┌─────────────┐
│              │     │                   │     │             │
│  Odoo Module │     │  Vector Search    │     │ DataProxy   │
│  Semantic    │────►│  Service          │◄────┤ Agent       │
│  Descriptions│     │  (Qdrant + BM42)  │     │             │
└──────────────┘     └─────────┬─────────┘     └─────────────┘
                               │
                               │
                               ▼
                      ┌─────────────────┐
                      │                 │
                      │  Redis Cache    │
                      │                 │
                      └─────────────────┘
```

## Componentes Principais

### 1. Extensão do Odoo para Descrições Semânticas

Um módulo personalizado para o Odoo que adiciona campos estruturados para descrições semânticas de produtos:

- **Descrição Semântica**: Texto conciso e estruturado otimizado para busca vetorial
- **Características Principais**: Lista de atributos-chave do produto
- **Casos de Uso**: Cenários comuns de utilização do produto
- **Verificação Humana**: Fluxo de trabalho para garantir precisão das descrições

### 2. Serviço de Sincronização Vetorial

Um serviço que mantém o Qdrant sincronizado com o Odoo:

- **Extração de Metadados**: Coleta dados estruturados do Odoo via MCP-Odoo
- **Geração de Embeddings**: Cria vetores densos via OpenAI e esparsos via BM42
- **Sincronização Incremental**: Atualiza apenas produtos modificados
- **Mapeamento de IDs**: Mantém relação entre IDs do Odoo e vetores no Qdrant

### 3. Motor de Busca Híbrida com Qdrant

Implementação de busca híbrida utilizando o Qdrant com BM42:

- **Busca Vetorial Densa**: Para compreensão semântica (similaridade conceitual)
- **Busca Vetorial Esparsa**: Para correspondência de palavras-chave (precisão)
- **Filtragem por Metadados**: Para refinar resultados por categoria, tags, etc.
- **Ranking Híbrido**: Combinação ponderada de resultados densos e esparsos

### 4. Camada de Cache com Redis

Sistema de cache para otimizar performance e reduzir carga no Odoo:

- **Cache de Configurações**: Armazena configurações de domínio/account_id
- **Cache de Credenciais**: Armazena credenciais de acesso ao Odoo
- **Cache de Resultados**: Armazena resultados de buscas frequentes
- **Controle de Estado**: Gerencia estado de sincronização e timestamps

### 5. Integração com DataProxyAgent

Adaptação do DataProxyAgent para utilizar o serviço de busca semântica:

- **Interface de Consulta**: Métodos para busca semântica de produtos
- **Tradução de Consultas**: Conversão de linguagem natural para consultas estruturadas
- **Formatação de Resultados**: Apresentação consistente dos resultados para os agentes

## Fluxo de Dados

### 1. Fluxo de Sincronização

```
┌─────────────┐     ┌───────────────┐     ┌────────────────┐     ┌─────────────┐
│ Odoo:       │     │ Extrator de   │     │ Gerador de     │     │ Qdrant:     │
│ Produto     │────►│ Metadados     │────►│ Contexto       │────►│ Coleção de  │
│ Atualizado  │     │ Estruturados  │     │ Enriquecido    │     │ Vetores     │
└─────────────┘     └───────────────┘     └────────────────┘     └─────────────┘
                            │                                            ▲
                            │                                            │
                            ▼                                            │
                    ┌───────────────┐                           ┌───────────────┐
                    │ Redis:        │                           │ OpenAI:       │
                    │ Mapeamento    │                           │ Serviço de    │
                    │ de IDs        │                           │ Embeddings    │
                    └───────────────┘                           └───────────────┘
```

### 2. Fluxo de Consulta

```
┌─────────────┐     ┌───────────────┐     ┌────────────────┐     ┌─────────────┐
│ CrewAI:     │     │ DataProxy     │     │ Serviço de     │     │ Qdrant:     │
│ Agente      │────►│ Agent         │────►│ Busca          │────►│ Busca       │
│             │     │               │     │ Semântica      │     │ Híbrida     │
└─────────────┘     └───────────────┘     └────────────────┘     └──────┬──────┘
      ▲                                                                  │
      │                                                                  │
      │                                                                  ▼
┌─────┴───────┐                                                 ┌───────────────┐
│ Chatwoot:   │                                                 │ Redis:        │
│ Resposta ao │◄────────────────────────────────────────────────┤ Cache de      │
│ Cliente     │                                                 │ Resultados    │
└─────────────┘                                                 └───────────────┘
```

## Implementação Técnica

### 1. Módulo de Extensão do Odoo

O módulo `semantic_product_description` adiciona campos estruturados ao modelo de produto do Odoo:

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
    
    semantic_description_verified = fields.Boolean(
        string='Descrição Verificada',
        default=False
    )
```

### 2. Serviço de Sincronização Vetorial

O serviço `ProductSyncService` mantém o Qdrant sincronizado com o Odoo:

```python
class ProductSyncService:
    def __init__(self, redis_client, vector_store, embed_model):
        self.redis = redis_client
        self.vector_store = vector_store
        self.embed_model = embed_model
        
    def sync_product(self, account_id, product_id, force=False):
        """Sincroniza um produto específico com o Qdrant."""
        # Verificar cache e estado de sincronização
        # Extrair metadados estruturados do Odoo
        # Gerar contexto enriquecido
        # Criar embeddings e indexar no Qdrant
        # Atualizar mapeamento no Redis
        
    def sync_all_products(self, account_id, batch_size=100):
        """Sincroniza todos os produtos de um account_id com o Qdrant."""
        # Obter lista de produtos via MCP-Odoo
        # Processar em lotes para evitar sobrecarga
        # Atualizar timestamp de sincronização
```

### 3. Motor de Busca Híbrida

O serviço `ProductSearchService` implementa busca híbrida com Qdrant e BM42:

```python
class ProductSearchService:
    def __init__(self, redis_client, vector_store, embed_model):
        self.redis = redis_client
        self.vector_store = vector_store
        self.embed_model = embed_model
    
    def search_products(self, account_id, query, filters=None, top_k=5, hybrid_alpha=0.5):
        """Realiza uma busca semântica de produtos."""
        # Configurar o mecanismo de consulta híbrida
        # Executar a consulta no Qdrant
        # Processar e enriquecer os resultados
        # Armazenar em cache para consultas futuras
```

### 4. Integração com DataProxyAgent

Adaptação do `DataProxyAgent` para utilizar o serviço de busca semântica:

```python
class DataProxyAgent:
    # ... código existente ...
    
    def __init__(self, redis_host="localhost", redis_port=6379):
        # ... inicialização existente ...
        self.product_search = ProductSearchService(redis_client, vector_store, embed_model)
    
    def search_products(self, account_id, query, filters=None):
        """Busca produtos usando busca semântica."""
        return self.product_search.search_products(account_id, query, filters)
    
    # ... código existente ...
```

## Vantagens da Abordagem

### 1. Qualidade e Precisão

- **Descrições Verificadas por Humanos**: Garante precisão e relevância
- **Busca Híbrida**: Combina o melhor da compreensão semântica e correspondência exata
- **Metadados Estruturados**: Permite filtragem precisa e contextualização

### 2. Performance e Escalabilidade

- **Sincronização Incremental**: Atualiza apenas o que mudou
- **Cache em Redis**: Reduz latência e carga no Odoo
- **Processamento em Lotes**: Evita sobrecarga durante sincronizações

### 3. Manutenção e Extensibilidade

- **Arquitetura Modular**: Componentes independentes e substituíveis
- **Interface no Odoo**: Facilita manutenção das descrições semânticas
- **Logs e Monitoramento**: Facilita diagnóstico e otimização

## Casos de Uso Avançados

Esta arquitetura serve como base para diversos casos de uso avançados:

### 1. Análise de Dados e Business Intelligence

- **Análise de Tendências**: Identificar padrões nas consultas dos clientes
- **Recomendações Personalizadas**: Sugerir produtos com base no histórico e contexto
- **Segmentação de Clientes**: Agrupar clientes com interesses similares

### 2. Marketing e Vendas

- **Otimização de Catálogo**: Identificar lacunas e oportunidades no catálogo
- **Personalização de Campanhas**: Adaptar mensagens para diferentes segmentos
- **Previsão de Demanda**: Antecipar tendências com base em padrões de busca

### 3. Atendimento ao Cliente

- **Respostas Contextuais**: Fornecer informações precisas sobre produtos
- **Cross-selling Inteligente**: Sugerir produtos complementares relevantes
- **Resolução de Dúvidas**: Responder perguntas técnicas com base em dados estruturados

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

### Fase 5: Casos de Uso Avançados (Semanas 9+)

- [ ] Implementação de análise de dados
- [ ] Desenvolvimento de recursos de marketing
- [ ] Expansão para outros domínios além de produtos

## Conclusão

A integração de busca semântica entre Odoo e sistemas de IA representa um avanço significativo na capacidade de extrair valor dos dados empresariais. Esta arquitetura não apenas resolve os desafios imediatos de busca de produtos, mas estabelece uma base sólida para casos de uso avançados em análise de dados, marketing e atendimento ao cliente.

A abordagem híbrida, combinando vetores densos, esparsos e metadados estruturados, oferece o equilíbrio ideal entre compreensão semântica e precisão, enquanto a sincronização incremental e o sistema de cache garantem performance e escalabilidade.

---

## Apêndice: Configuração do Ambiente

### Requisitos

- Odoo 14.0+
- Python 3.8+
- Redis 6.0+
- Qdrant 1.0.0+
- OpenAI API (acesso à API de embeddings)

### Variáveis de Ambiente

```
# Configuração do Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Configuração do Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Configuração do OpenAI
OPENAI_API_KEY=sk-your-api-key

# Configuração do MCP-Odoo
MCP_ODOO_HOST=localhost
MCP_ODOO_PORT=8069
```

### Comandos Úteis

```bash
# Iniciar sincronização inicial para um account_id
python -m src.vector_search.cli sync-all --account-id 2

# Verificar status da sincronização
python -m src.vector_search.cli status --account-id 2

# Testar busca semântica
python -m src.vector_search.cli search --account-id 2 --query "sofá de couro confortável"
```

---

Desenvolvido com ❤️ pela Equipe ChatwootAI
