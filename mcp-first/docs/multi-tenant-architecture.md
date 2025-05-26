# Arquitetura MCP First Multi-Tenant

## Visão Geral

Este documento detalha como a arquitetura MCP First será implementada em um ambiente multi-tenant, onde cada tenant (conta) possui seu próprio conjunto de dados e configurações, mas compartilha a mesma infraestrutura de serviços.

## Princípio Multi-Tenant

Na arquitetura ChatwootAI, o `account_id` serve como identificador universal que conecta todos os componentes do sistema:

- No **Odoo**: Representa o nome do banco de dados específico do tenant
- No **Qdrant**: Identifica o prefixo das coleções vetoriais do tenant
- No **Chatwoot**: É o identificador da conta que originou a mensagem
- No **MongoDB**: Filtra as configurações específicas do tenant

Este identificador é propagado através de todas as camadas do sistema, garantindo isolamento de dados e configurações entre diferentes tenants.

## Componentes da Arquitetura Multi-Tenant

### 1. MCP-Odoo

O MCP-Odoo já existente será adaptado para suportar múltiplos tenants:

- Cada requisição MCP incluirá o `account_id` como parâmetro obrigatório
- O MCP-Odoo usará o `account_id` para conectar ao banco de dados Odoo correspondente
- Todas as operações serão isoladas dentro do contexto do tenant específico

**Exemplo de chamada MCP multi-tenant:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_records",
    "arguments": {
      "account_id": "tenant1",
      "model": "res.partner",
      "domain": [["is_company", "=", true]],
      "fields": ["name", "email", "phone"],
      "limit": 10
    }
  }
}
```

### 2. MCP-Qdrant

O MCP-Qdrant (disponível no GitHub) será configurado para suportar múltiplos tenants:

- As coleções no Qdrant seguirão o padrão de nomenclatura `{account_id}_{collection_type}`
- Exemplo: `tenant1_products`, `tenant1_rules`, `tenant2_products`, etc.
- Cada requisição MCP incluirá o `account_id` para determinar quais coleções acessar

**Exemplo de chamada MCP multi-tenant:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search_vectors",
    "arguments": {
      "account_id": "tenant1",
      "collection_type": "products",
      "query_vector": [0.1, 0.2, 0.3, ...],
      "limit": 5
    }
  }
}
```

### 3. MCP-MongoDB

O MCP-MongoDB (disponível no GitHub) será utilizado para acessar as configurações dos agentes:

- As configurações enviadas pelo módulo Odoo são armazenadas no MongoDB
- O MCP-MongoDB permitirá que os agentes acessem essas configurações de forma padronizada
- Cada requisição incluirá o `account_id` para filtrar as configurações específicas do tenant

**Exemplo de chamada MCP multi-tenant:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_agent_config",
    "arguments": {
      "account_id": "tenant1",
      "config_type": "business_rules"
    }
  }
}
```

### 4. MCP-Chatwoot

O MCP-Chatwoot será implementado para processar mensagens de múltiplos tenants:

- O `account_id` será extraído de cada mensagem recebida do Chatwoot
- As respostas serão enviadas de volta ao canal correto com base no `account_id`
- Configurações específicas do tenant (estilo de comunicação, horários de atendimento) serão aplicadas

### 5. MCP-Orchestrator

O MCP-Orchestrator será o componente central que gerencia o fluxo de informações entre os diferentes MCPs:

- Recebe requisições dos agentes CrewAI
- Roteia as requisições para o MCP apropriado com base no tipo de operação
- Garante que o `account_id` seja propagado corretamente entre os diferentes MCPs
- Implementa cache específico por tenant para otimizar desempenho

## Fluxo de Processamento Multi-Tenant

### Fluxo de Atendimento ao Cliente

1. **Recebimento da Mensagem**:
   - Cliente envia mensagem através de um canal (ex: WhatsApp)
   - Chatwoot recebe a mensagem e a encaminha para o sistema via webhook
   - O webhook inclui o `account_id` da conta Chatwoot

2. **Processamento Inicial**:
   - MCP-Chatwoot recebe a notificação do webhook e extrai o `account_id`
   - MCP-Orchestrator identifica o canal e ativa a crew correspondente
   - O `account_id` é passado para a crew como contexto

3. **Carregamento de Configurações**:
   - A crew utiliza MCP-MongoDB para carregar configurações específicas do tenant
   - MCP-MongoDB filtra as configurações com base no `account_id`
   - Configurações incluem estilo de comunicação, horários de atendimento, etc.

4. **Análise de Intenção**:
   - A crew utiliza o Agente de Intenção para analisar o conteúdo da mensagem
   - Com base na intenção detectada, seleciona o agente especializado mais adequado

5. **Consulta de Conhecimento**:
   - O agente especializado utiliza MCP-Qdrant para consultar a coleção relevante
   - MCP-Qdrant acessa a coleção específica do tenant (`{account_id}_{collection_type}`)
   - Qdrant retorna os resultados mais relevantes com base na similaridade vetorial

6. **Verificação de Dados em Tempo Real**:
   - Se necessário, o agente utiliza MCP-Odoo para verificar informações atualizadas
   - MCP-Odoo conecta ao banco de dados Odoo específico do tenant (baseado no `account_id`)
   - Odoo processa a solicitação e retorna os dados solicitados

7. **Geração e Envio da Resposta**:
   - O agente formula uma resposta baseada nas informações obtidas
   - A resposta é formatada de acordo com o estilo de comunicação do tenant
   - MCP-Chatwoot envia a mensagem ao cliente através do canal apropriado

## Implementação do Multi-Tenant

### 1. Configuração do MCP-Odoo

O MCP-Odoo existente será adaptado para suportar múltiplos tenants:

```python
@mcp.tool("search_records")
def search_records(account_id: str, model: str, domain: List, fields: Optional[List[str]] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Busca registros em qualquer modelo Odoo para um tenant específico.
    
    Args:
        account_id: Identificador do tenant (nome do banco de dados Odoo)
        model: Nome do modelo Odoo (ex: 'res.partner')
        domain: Domínio de busca (ex: [['is_company', '=', True]])
        fields: Campos a serem retornados (opcional)
        limit: Número máximo de registros a serem retornados (opcional)
        
    Returns:
        Lista de registros encontrados
    """
    # Conectar ao banco de dados específico do tenant
    odoo_connection = get_odoo_connection(account_id)
    
    try:
        records = odoo_connection.execute_kw(
            account_id, odoo_connection.uid, odoo_connection.password,
            model, 'search_read',
            [domain],
            {'fields': fields, 'limit': limit}
        )
        return {"success": True, "records": records}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 2. Configuração do MCP-Qdrant

O MCP-Qdrant será configurado para acessar coleções específicas por tenant:

```python
@mcp.tool("search_vectors")
def search_vectors(account_id: str, collection_type: str, query_vector: List[float], limit: int = 5, filter: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Busca vetores similares em uma coleção específica do tenant.
    
    Args:
        account_id: Identificador do tenant
        collection_type: Tipo de coleção (products, rules, etc.)
        query_vector: Vetor de consulta
        limit: Número máximo de resultados
        filter: Filtro adicional (opcional)
        
    Returns:
        Resultados da busca vetorial
    """
    # Construir o nome da coleção específica do tenant
    collection_name = f"{account_id}_{collection_type}"
    
    try:
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            filter=filter
        )
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 3. Configuração do MCP-MongoDB

O MCP-MongoDB será configurado para acessar configurações específicas por tenant:

```python
@mcp.tool("get_agent_config")
def get_agent_config(account_id: str, config_type: str) -> Dict[str, Any]:
    """
    Obtém configurações de agente para um tenant específico.
    
    Args:
        account_id: Identificador do tenant
        config_type: Tipo de configuração (business_rules, company_metadata, etc.)
        
    Returns:
        Configurações do agente
    """
    try:
        # Buscar configurações específicas do tenant
        config = mongodb_client[account_id][config_type].find_one(
            {"account_id": account_id},
            {"_id": 0}  # Excluir o campo _id da resposta
        )
        
        if not config:
            return {"success": False, "error": "Configuration not found"}
        
        return {"success": True, "config": config}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 4. Configuração do CrewAI

O CrewAI será adaptado para trabalhar com o contexto multi-tenant:

```python
class WhatsAppCrew:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.mcp_client = MCPClient("http://mcp-orchestrator:8000")
        
        # Carregar configurações específicas do tenant
        config_result = self.mcp_client.call_tool("get_agent_config", {
            "account_id": self.account_id,
            "config_type": "company_metadata"
        })
        
        if not config_result.get("success"):
            raise Exception(f"Failed to load tenant configuration: {config_result.get('error')}")
        
        self.config = config_result.get("config")
        
        # Inicializar agentes com contexto do tenant
        self.agents = self._initialize_agents()
    
    def _initialize_agents(self):
        # Criar agentes com contexto do tenant
        intention_agent = Agent(
            name="Intention Agent",
            context=f"You are analyzing messages for {self.config.get('company_name')}.",
            # ... outras configurações
        )
        
        # ... inicializar outros agentes
        
        return {
            "intention": intention_agent,
            # ... outros agentes
        }
    
    def process_message(self, message: str, conversation_id: str):
        # Processar mensagem no contexto do tenant
        # Todos os agentes terão acesso ao account_id
        # Todas as chamadas MCP incluirão o account_id
        pass
```

## Gerenciamento de Configurações Multi-Tenant

### 1. Fluxo de Configuração

1. **Configuração no Odoo**:
   - Usuário configura informações da empresa, serviços, regras de negócio, etc. no Odoo
   - O módulo `company_services` prepara os dados para sincronização
   - Os dados são enviados para o webhook com o `account_id` como identificador

2. **Armazenamento no MongoDB**:
   - O webhook recebe os dados e os armazena no MongoDB
   - Os dados são organizados por `account_id` para garantir isolamento entre tenants

3. **Acesso via MCP-MongoDB**:
   - Os agentes acessam as configurações através do MCP-MongoDB
   - O `account_id` é usado para filtrar as configurações específicas do tenant

### 2. Estrutura do MongoDB

```
mongodb
├── tenant1                           # Database para o tenant1
│   ├── company_metadata              # Coleção de metadados da empresa
│   │   └── {document}                # Documento com configurações
│   ├── business_rules                # Coleção de regras de negócio
│   │   └── [{rule1}, {rule2}, ...]   # Documentos com regras
│   └── agent_config                  # Coleção de configurações de agentes
│       └── {document}                # Documento com configurações
│
├── tenant2                           # Database para o tenant2
│   ├── company_metadata              # ...
│   ├── business_rules                # ...
│   └── agent_config                  # ...
│
└── ...                               # Outros tenants
```

## Cache e Otimização

Para garantir desempenho em um ambiente multi-tenant, implementaremos estratégias de cache específicas por tenant:

1. **Cache de Configurações**:
   - Configurações frequentemente acessadas são armazenadas em cache no Redis
   - Chaves de cache incluem o `account_id` para isolamento entre tenants
   - Exemplo: `tenant1:company_metadata`, `tenant2:business_rules`

2. **Cache de Vetores**:
   - Resultados de buscas vetoriais frequentes são armazenados em cache
   - Cache é específico por tenant para evitar vazamento de dados
   - Invalidação automática quando novos vetores são adicionados

3. **Pool de Conexões**:
   - Pool de conexões Odoo separado para cada tenant
   - Conexões são reutilizadas para reduzir overhead
   - Monitoramento de uso para ajustar tamanho do pool por tenant

## Considerações de Segurança Multi-Tenant

1. **Isolamento de Dados**:
   - Verificação rigorosa do `account_id` em todas as operações
   - Validação de que o cliente tem permissão para acessar o tenant especificado
   - Prevenção de ataques de enumeração de tenants

2. **Auditoria por Tenant**:
   - Logs separados por tenant para facilitar auditoria
   - Rastreamento de todas as operações com `account_id` associado
   - Alertas específicos por tenant para atividades suspeitas

3. **Limites de Recursos**:
   - Quotas de API por tenant para evitar abuso
   - Limites de armazenamento e processamento por tenant
   - Monitoramento de uso para identificar tenants problemáticos

## Conclusão

A arquitetura MCP First Multi-Tenant permite que o sistema ChatwootAI atenda múltiplos clientes (tenants) com isolamento completo de dados e configurações, enquanto compartilha a mesma infraestrutura de serviços. O `account_id` serve como identificador universal que conecta todos os componentes do sistema, garantindo que cada tenant tenha sua própria experiência personalizada.

A implementação aproveita os componentes MCP existentes (MCP-Odoo, MCP-Qdrant, MCP-MongoDB) e os adapta para o contexto multi-tenant, garantindo escalabilidade, segurança e desempenho para todos os tenants.
