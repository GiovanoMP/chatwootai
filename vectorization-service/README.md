# Serviço de Vetorização

Este é um microsserviço para vetorização de regras de negócio, regras de agendamento e documentos de suporte, utilizando embeddings para busca semântica e enriquecimento de conteúdo.

## Visão Geral

O serviço de vetorização é responsável por:

1. Receber regras de negócio, regras de agendamento e documentos de suporte do módulo Odoo
2. Enriquecer automaticamente o conteúdo para melhorar a qualidade da recuperação
3. Processar documentos longos dividindo-os em chunks com sobreposição
4. Gerar embeddings para esses dados usando o modelo OpenAI text-embedding-3-small
5. Armazenar os embeddings no Qdrant para busca semântica
6. Fornecer endpoints para busca semântica de regras e documentos
7. Garantir sincronização bidirecional entre o Odoo e o Qdrant
8. Implementar controle de consumo de tokens e cache para otimização de custos

## Tecnologias Utilizadas

- **FastAPI**: Framework web para APIs
- **Qdrant**: Banco de dados vetorial para armazenamento e busca de embeddings
- **Redis**: Cache, controle de taxa e armazenamento de metadados
- **OpenAI**: Geração de embeddings (text-embedding-3-small) e enriquecimento de conteúdo (GPT-4o-mini)
- **Docker**: Containerização e integração com a rede existente
- **Logging**: Sistema de logging estruturado com rotação de arquivos

## Estrutura do Projeto

```
vectorization-service/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── business_rules.py
│   │   ├── scheduling_rules.py
│   │   └── support_documents.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── business_rule.py
│   │   ├── scheduling_rule.py
│   │   └── support_document.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache_service.py
│   │   ├── document_processor.py
│   │   ├── embedding_service.py
│   │   ├── enrichment_service.py
│   │   ├── redis_service.py
│   │   └── vector_service.py
│   ├── utils/
│   │   └── __init__.py
│   └── main.py
├── logs/
│   ├── vectorization_service_YYYYMMDD.log
│   ├── critical.log
│   ├── sync_operations.log
│   └── embedding_operations.log
├── tests/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── test_service.py
└── README.md
```

## Instalação e Execução

### Pré-requisitos

- Docker e Docker Compose
- Qdrant e Redis já instalados e funcionando na rede `odoo14_default`
- Chave de API da OpenAI para embeddings e enriquecimento

### Configuração

1. Clone o repositório
2. Copie o arquivo `.env.example` para `.env` e configure as variáveis de ambiente:

```bash
cp .env.example .env
```

3. Edite o arquivo `.env` com suas configurações, especialmente:
   - `OPENAI_API_KEY`: Sua chave de API da OpenAI
   - `API_KEY`: Chave de API para autenticação (deve ser a mesma usada pelo módulo Odoo)
   - `QDRANT_HOST`: Nome do contêiner Qdrant na rede Docker (geralmente `qdrant`)
   - `REDIS_HOST`: Nome do contêiner Redis na rede Docker (geralmente `odoo_api-redis-1`)
   - `LOG_LEVEL`: Nível de logging (INFO, DEBUG, etc.)
   - `ENABLE_DOCUMENT_CHUNKING`: Habilitar ou desabilitar o chunking de documentos

### Execução

Para iniciar o serviço:

```bash
cd vectorization-service
docker-compose up -d
```

O serviço estará disponível em `http://localhost:8004`.

### Testando o Serviço

O projeto inclui um script de teste para verificar se o serviço está funcionando corretamente:

```bash
# Testar todos os endpoints
python test_service.py --url http://localhost:8004 --api-key development-api-key

# Testar apenas a verificação de saúde
python test_service.py --test health

# Testar apenas a sincronização de regras de negócio
python test_service.py --test business-rules
```

## Endpoints da API

### Verificação de Saúde

- `GET /health`: Verifica se o serviço está funcionando corretamente

### Regras de Negócio

- `POST /api/v1/business-rules/sync`: Sincroniza regras de negócio com enriquecimento automático
- `POST /api/v1/business-rules/search`: Busca regras de negócio semanticamente

### Regras de Agendamento

- `POST /api/v1/scheduling-rules/sync`: Sincroniza regras de agendamento

### Documentos de Suporte

- `POST /api/v1/support-documents/sync`: Sincroniza documentos de suporte com chunking e enriquecimento

> **Nota**: O endpoint de metadados da empresa foi removido. Os dados da empresa agora são gerenciados pelo MongoDB via outro módulo.

## Sistema de Enriquecimento

O serviço implementa um sistema de enriquecimento automático para melhorar a qualidade da recuperação:

1. **Enriquecimento de Regras de Negócio**:
   - Regras com descrições curtas são automaticamente enriquecidas
   - O modelo GPT-4o-mini adiciona contexto e detalhes relevantes
   - Limite de 10 enriquecimentos por hora por conta

2. **Enriquecimento de Documentos**:
   - Documentos pequenos ou de tipos específicos (FAQ, políticas) são enriquecidos
   - O enriquecimento adiciona termos relacionados e explicações adicionais
   - Limite de 20 enriquecimentos por hora por conta

3. **Controle de Consumo**:
   - Cache para evitar enriquecimentos repetidos
   - Limites de tokens na resposta (150 para regras, 300 para documentos)
   - Verificação de necessidade baseada no tamanho e tipo do conteúdo

## Sistema de Chunking para RAG

Para documentos longos, o serviço implementa um sistema de chunking inteligente:

1. **Divisão em Chunks**:
   - Documentos longos são divididos em chunks menores (800 caracteres por padrão)
   - Sobreposição entre chunks (150 caracteres por padrão) para preservar contexto
   - Quebras inteligentes em finais de parágrafos ou frases

2. **Metadados Enriquecidos**:
   - Cada chunk mantém metadados do documento original
   - Informações adicionais como posição no documento (chunk_index, total_chunks)
   - Identificadores únicos para rastreabilidade

3. **Formatação para Embedding**:
   - Cada chunk é formatado com contexto adicional
   - Inclui nome do documento, tipo e posição relativa
   - Melhora a qualidade da recuperação

## Uso do Redis

O Redis é utilizado para:

1. **Cache de Dados**: Armazenar resultados de consultas frequentes
2. **Controle de Rate Limiting**: Limitar o número de chamadas à API OpenAI
3. **Invalidação de Cache**: Garantir que os dados estejam sempre atualizados
4. **Metadados de Sincronização**: Armazenar informações sobre sincronizações
5. **Cache de Enriquecimento**: Evitar enriquecimentos repetidos do mesmo conteúdo

## Sincronização Bidirecional

O serviço implementa sincronização bidirecional entre o Odoo e o Qdrant:

1. Quando regras ou documentos são adicionados ou atualizados no Odoo, eles são sincronizados com o Qdrant
2. Quando regras ou documentos são removidos do Odoo, eles também são removidos do Qdrant
3. O cache no Redis é invalidado automaticamente quando os dados mudam
4. Logs detalhados são gerados para rastrear todas as operações de sincronização

## Sistema de Logging

O serviço implementa um sistema de logging estruturado:

1. **Logs Gerais**: Armazenados em `logs/vectorization_service_YYYYMMDD.log`
2. **Logs Críticos**: Eventos críticos em `logs/critical.log`
3. **Logs de Sincronização**: Operações de sincronização em `logs/sync_operations.log`
4. **Logs de Embedding**: Operações de embedding em `logs/embedding_operations.log`
5. **Rotação de Logs**: Rotação automática de logs para evitar arquivos muito grandes

## Limitação de Tokens

Para controlar o consumo de tokens da OpenAI:

1. Os textos são limitados a um número máximo de tokens antes de gerar embeddings (8192 tokens)
2. O enriquecimento é limitado por conta e por período (10-20 por hora)
3. O cache é utilizado para evitar chamadas desnecessárias à API
4. Verificação de necessidade para evitar enriquecimentos desnecessários

## Documentação da API

A documentação da API está disponível em:

- Swagger UI: `http://localhost:8004/docs`
- ReDoc: `http://localhost:8004/redoc`

## Diretrizes para Serviços Futuros

Para estender o sistema com novos serviços especializados, recomendamos:

### 1. Microsserviços Especializados

Para funcionalidades específicas como otimização de produtos para marketplaces ou conteúdo para redes sociais, recomendamos criar microsserviços separados:

- **Separação de Responsabilidades**: Cada serviço com um domínio específico
- **Escalabilidade Independente**: Escalar cada serviço conforme necessário
- **Evolução Independente**: Cada serviço pode evoluir no seu próprio ritmo

### 2. Estrutura Recomendada

```
/services
  /vectorization-service     # Serviço atual
  /product-optimization      # Novo serviço para produtos
    /app
      /api
        marketplace_ml.py    # Endpoint para Mercado Livre
        marketplace_shopee.py # Endpoint para Shopee
      /services
        optimization_service.py # Serviço de otimização
      main.py
    Dockerfile
    docker-compose.yml
  /social-media-service      # Serviço para redes sociais
    /app
      /api
        instagram.py         # Endpoint para Instagram
        facebook.py          # Endpoint para Facebook
      /services
        content_service.py   # Serviço de conteúdo
      main.py
    Dockerfile
    docker-compose.yml
```

### 3. Compartilhamento de Infraestrutura

- Todos os serviços devem usar a mesma rede Docker (`odoo14_default`)
- Compartilhar Redis para cache e controle de taxa
- Usar o mesmo sistema de autenticação (API Key)

### 4. Adicionando Novos Endpoints

Para adicionar novos endpoints ao serviço atual:

1. Criar um novo arquivo na pasta `app/api/`
2. Implementar um novo router com os endpoints necessários
3. Registrar o router em `app/main.py`
4. Implementar os serviços necessários em `app/services/`
5. Atualizar a documentação
