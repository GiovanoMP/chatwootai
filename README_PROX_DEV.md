# Documentação para o Próximo Desenvolvedor

## Contexto e Alterações Recentes

### Visão Geral do Sistema

O sistema é uma plataforma modular de integração entre Odoo e sistemas de IA, composta por:

1. **Servidor Unificado**: Um servidor FastAPI que roda na porta 8001, unificando:
   - Webhook do Chatwoot (prefixo `/webhook`)
   - API Odoo (prefixo `/api/v1`)

2. **Módulos Odoo**: Conjunto de módulos instalados no Odoo, incluindo:
   - `business_rules`: Gerencia regras de negócio e metadados da empresa
   - `ai_credentials_manager`: Gerencia credenciais para autenticação com o sistema de IA
   e outros

3. **Serviços de Dados**: 
   - Redis para cache
   - Qdrant para busca vetorial
   - OpenAI para geração de embeddings

### Alterações Recentes (Abril 2025)

#### 1. Correção do Endpoint de Sincronização

**Problema**: O endpoint de sincronização de regras de negócio estava retornando erro 404 porque estava usando uma URL incorreta.

**Solução**: Modificamos o arquivo `sync_controller.py` para usar a URL correta:

```python
# Antes
sync_endpoint = f"{api_url}/webhook/api/v1/business-rules/sync"

# Depois
sync_endpoint = f"{api_url}/api/v1/business-rules/sync"
```

Esta alteração alinha o endpoint com a arquitetura do servidor, onde as rotas da API Odoo são registradas com o prefixo `/api/v1` e não precisam do prefixo `/webhook`.

#### 2. Reorganização da Interface do Módulo Business Rules

- Movemos a aba "Informações Básicas" para ser a primeira aba
- Colocamos a aba "Site e Redes Sociais" após a aba "Configurações de Atendimento"
- Atualizamos o botão "Ver Regras Ativas" para "Ver Regras de Negócio"
- Atualizamos o texto "Regras Temporárias Ativas" para "Promoções e Regras Temporárias Ativas"

#### 3. Correção do Wizard de Upload de Documentos

Simplificamos o formulário para remover campos que não existiam mais no modelo, corrigindo erros durante a atualização do módulo.

#### 4. Adição de Suporte a Promoções

Adicionamos suporte para configurar se promoções devem ser informadas no início da conversa, incluindo:
- Novo campo no modelo `business.rules`
- Atualização do método `sync_company_metadata`
- Atualização do método `_update_customer_service_yaml`

## Estado Atual das APIs

### Segurança e Autenticação

O sistema implementa um modelo de segurança mais robusto:

1. **Ocultação do Account ID nas APIs**:
   - As APIs não expõem mais o account_id diretamente nas URLs ou respostas
   - O account_id é obtido do token de autenticação ou do estado da requisição

2. **Verificação de Credenciais**:
   - Middleware de autenticação (`AuthMiddleware`) verifica tokens em todas as requisições
   - Tokens são validados contra o módulo `ai_credentials_manager`
   - Cada account_id tem seu próprio token único

3. **Fluxo de Autenticação**:
   ```
   1. Cliente envia requisição com token no header Authorization
   2. AuthMiddleware valida o token e extrai o account_id
   3. O account_id é armazenado no estado da requisição
   4. As rotas usam o account_id do estado, não da URL
   ```

4. **Compatibilidade com Código Legado**:
   - Para compatibilidade, ainda é possível passar o account_id na URL
   - O middleware `legacy_account_id_middleware` processa esses casos
   - Prioridade: Token de autenticação > URL parameter

### Estrutura de Rotas

O servidor unificado organiza as rotas da seguinte forma:

1. **Rotas do Webhook** (prefixo `/webhook`):
   - Processam webhooks do Chatwoot
   - Gerenciam eventos de sincronização de credenciais

2. **Rotas da API Odoo** (prefixo `/api/v1`):
   - `/api/v1/business-rules/*`: Gerenciamento de regras de negócio
   - `/api/v1/credentials/*`: Gerenciamento de credenciais
   - `/api/v1/semantic-product/*`: Busca semântica de produtos
   - `/api/v1/product-management/*`: Gerenciamento de produtos

3. **Rotas Específicas**:
   - `/api/v1/business-rules/sync`: Sincroniza regras de negócio com o sistema de IA
   - `/api/v1/business-rules/sync-company-metadata`: Sincroniza metadados da empresa

## Problemas Conhecidos e Pendências

### 1. Erros de Coroutine

Nos logs, observamos erros relacionados a coroutines já aguardadas:

```
Failed to sync company metadata: cannot reuse already awaited coroutine
Failed to get business area for account account_1: cannot reuse already awaited coroutine
```

Estes erros indicam problemas no código assíncrono, onde uma coroutine está sendo reutilizada. Embora não impeçam a sincronização geral, devem ser corrigidos.

### 2. Conexão com PostgreSQL

Há erros de conexão com o PostgreSQL nos logs:

```
Erro ao conectar ao PostgreSQL: connection to server at "localhost" (127.0.0.1), port 5433 failed: Connection refused
```

O sistema continua funcionando usando Redis, mas a conexão com PostgreSQL deve ser configurada corretamente ou removida se não for necessária.

### 3. Configuração de URLs

A configuração de URLs para comunicação entre o módulo Odoo e o servidor da API pode ser confusa:
- O módulo Odoo se comunica com o servidor através da rede local
- A URL base deve apontar para o endereço correto (geralmente `http://localhost:8001`)
- Em produção, isso pode precisar ser ajustado para o endereço do VPS

## Recomendações para o Próximo Desenvolvedor

### 1. Corrigir Erros de Coroutine

Investigue os erros de coroutine nos métodos:
- `sync_company_metadata`
- Método que obtém o business area para uma conta

Possível solução: Evite reutilizar coroutines já aguardadas. Crie novas instâncias quando necessário.

### 2. Melhorar Tratamento de Erros

Adicione tratamento de erros mais robusto, especialmente para:
- Falhas de conexão com serviços externos (Redis, Qdrant, OpenAI)
- Erros durante a sincronização de metadados
- Problemas de autenticação

### 3. Padronizar Configuração de URLs

Crie um sistema centralizado para gerenciar URLs de serviços:
- Defina claramente quais endpoints precisam do prefixo `/webhook`
- Documente a estrutura de rotas
- Considere usar variáveis de ambiente para configuração em diferentes ambientes

### 4. Melhorar Documentação de APIs

Documente todas as APIs disponíveis, incluindo:
- Endpoints
- Parâmetros
- Formato de resposta
- Requisitos de autenticação

### 5. Testes Automatizados

Desenvolva testes automatizados para:
- Verificar a sincronização de regras de negócio
- Testar a autenticação
- Validar o comportamento do sistema com diferentes configurações

## Arquitetura do Sistema

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Odoo (8069)    │<─────│  Servidor (8001)│<─────│  Chatwoot       │
│  - business_rules    │      │  - FastAPI      │      │                 │
│  - ai_credentials   │      │  - Webhook      │      │                 │
│                 │      │  - API Odoo     │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                               │   │
                               │   │
                 ┌─────────────┘   └─────────────┐
                 │                               │
        ┌────────▼─────────┐             ┌───────▼──────────┐
        │                  │             │                  │
        │  Redis (6379)    │             │  Qdrant (6333)   │
        │  - Cache         │             │  - Vector Search │
        │                  │             │                  │
        └──────────────────┘             └──────────────────┘
```

## Fluxo de Sincronização

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Odoo           │────>│  API            │────>│  OpenAI         │
│  (Regras)       │     │  (Processamento)│     │  (Embeddings)   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               │
                               ▼
                        ┌─────────────────┐
                        │                 │
                        │  Qdrant         │
                        │  (Armazenamento)│
                        │                 │
                        └─────────────────┘
```

## Conclusão

O sistema está funcionando corretamente após as alterações recentes. A sincronização de regras de negócio está operacional, e a interface do módulo foi melhorada. Existem alguns problemas menores a serem resolvidos, principalmente relacionados ao código assíncrono e à configuração de conexões.

A arquitetura do sistema é sólida, com uma clara separação de responsabilidades entre os diferentes componentes. O próximo desenvolvedor deve focar em resolver os problemas pendentes e melhorar a documentação e os testes.
