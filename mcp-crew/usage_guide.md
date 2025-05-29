# Guia de Uso do MCP-Crew

## Introdução

O MCP-Crew é um protocolo central de contexto para modelos (Model Context Protocol) projetado para gerenciar múltiplas crews de agentes de IA. Este guia explica como configurar, inicializar e utilizar o MCP-Crew em seus projetos.

## Instalação

### Requisitos

- Python 3.8+
- Redis 6.0+ (opcional, mas recomendado para produção)

### Passos para Instalação

1. Clone o repositório:
```bash
git clone https://github.com/sprintia/mcp-crew.git
cd mcp-crew
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o ambiente:
```bash
cp config/default_config.yaml config/config.yaml
# Edite config/config.yaml conforme necessário
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
# Redis (opcional)
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mcp_crew.log

# Servidor API
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# Credenciais do Mercado Livre (para o conector específico)
ML_CLIENT_ID=seu_client_id
ML_CLIENT_SECRET=sua_client_secret
ML_ENDPOINT=https://api.mercadolivre.com
```

### Arquivo de Configuração

Alternativamente, você pode usar um arquivo YAML para configuração:

```yaml
redis:
  enabled: true
  host: localhost
  port: 6379
  db: 0
  password: null

logging:
  level: INFO
  file: logs/mcp_crew.log

server:
  host: 0.0.0.0
  port: 5000

mcps:
  mercado_livre:
    client_id: seu_client_id
    client_secret: sua_client_secret
    endpoint: https://api.mercadolivre.com
```

## Uso Básico

### Inicialização do MCP-Crew

```python
from mcp_crew import MCPCrew

# Inicializa o MCP-Crew
mcp_crew = MCPCrew(config_path="config/config.yaml")

# Registra um MCP do Mercado Livre
mcp_crew.register_mercadolivre_mcp(
    mcp_id="mercado_livre_1",
    endpoint="https://api.mercadolivre.com",
    client_id="seu_client_id",
    client_secret="sua_client_secret"
)

# Inicia o MCP-Crew
import asyncio
asyncio.run(mcp_crew.start())
```

### Executando o Servidor API

```python
from mcp_crew import MCPCrew

# Inicializa o MCP-Crew
mcp_crew = MCPCrew(config_path="config/config.yaml")

# Executa o servidor API
mcp_crew.run_api_server(host="0.0.0.0", port=5000)
```

Alternativamente, você pode executar o servidor diretamente:

```bash
python -m mcp_crew.main
```

## Gerenciamento de Agentes

### Criação de Agentes

```python
from mcp_crew.core.agent_manager import Agent

# Cria um agente
agent = Agent(
    name="Analista de Preços",
    role="analyst",
    capabilities=["price_analysis", "market_research"]
)

# Registra o agente no gerenciador
agent_id = mcp_crew.agent_manager.register_agent(agent)
```

### Agrupamento de Agentes

```python
# Cria um grupo de agentes
mcp_crew.agent_manager.create_group("mercado_livre_team", [agent_id])

# Adiciona outro agente ao grupo
mcp_crew.agent_manager.add_agent_to_group("mercado_livre_team", another_agent_id)
```

## Autorização e Permissões

### Criação de Políticas de Autorização

```python
from mcp_crew.core.auth_manager import AuthorizationPolicy, PermissionLevel, ActionType

# Cria uma política de autorização
policy = AuthorizationPolicy(
    name="Política Padrão",
    description="Política com permissões básicas"
)

# Define regras
policy.add_rule("analyst", ActionType.QUERY, PermissionLevel.EXECUTE)
policy.add_rule("analyst", ActionType.DATA_MODIFICATION, PermissionLevel.READ)

# Define requisitos de aprovação
policy.set_approval_requirement("analyst", ActionType.AUTONOMOUS, True)

# Registra a política
policy_id = mcp_crew.auth_manager.register_policy(policy)

# Define como política ativa
mcp_crew.auth_manager.set_active_policy(policy_id)
```

### Verificação de Permissões

```python
# Verifica se um agente tem permissão para uma ação
has_permission = mcp_crew.auth_manager.check_permission(
    agent_id="agent_123",
    role="analyst",
    action_type=ActionType.QUERY,
    required_level=PermissionLevel.EXECUTE
)

# Verifica se uma ação requer aprovação
requires_approval = mcp_crew.auth_manager.requires_approval(
    role="analyst",
    action_type=ActionType.AUTONOMOUS
)
```

## Comunicação entre Agentes

### Envio de Mensagens

```python
from mcp_crew.core.communication import Message, MessageType

# Cria uma mensagem
message = mcp_crew.communication_protocol.create_message(
    sender_id="agent_123",
    message_type=MessageType.COMMAND,
    content={"action": "analyze_prices", "product_id": "123"},
    recipient_id="agent_456"
)

# Envia a mensagem
import asyncio
response = asyncio.run(mcp_crew.communication_protocol.send_message(message))
```

### Processamento de Mensagens

```python
from mcp_crew.core.communication import MessageHandler, Message

# Cria um manipulador de mensagens
class MyMessageHandler(MessageHandler):
    async def handle_message(self, message: Message):
        print(f"Mensagem recebida: {message.content}")
        return message.create_response({"status": "success"})

# Registra o manipulador
mcp_crew.communication_protocol.register_handler("agent_456", MyMessageHandler())

# Processa mensagens (em um loop)
async def process_messages():
    while True:
        await mcp_crew.communication_protocol.process_messages("agent_456")
        await asyncio.sleep(0.1)
```

## Gerenciamento de Contexto

### Criação e Atualização de Contexto

```python
from mcp_crew.core.context_manager import ContextType

# Cria um contexto
context = mcp_crew.context_manager.create_context(
    context_type=ContextType.CONVERSATION,
    owner_id="agent_123",
    data={"conversation_history": []},
    ttl=3600  # 1 hora
)

# Atualiza o contexto
mcp_crew.context_manager.update_context(
    context_id=context.id,
    data={"conversation_history": ["Olá, como posso ajudar?"]},
    merge=True
)
```

### Recuperação de Contexto

```python
# Obtém um contexto pelo ID
context = mcp_crew.context_manager.get_context(context_id)

# Obtém todos os contextos de um proprietário
contexts = mcp_crew.context_manager.get_contexts_by_owner(
    owner_id="agent_123",
    context_type=ContextType.CONVERSATION
)
```

## Integração com MCPs Específicos

### Mercado Livre

```python
# Obtém o conector do Mercado Livre
ml_connector = mcp_crew.mcp_registry.get_connector("mercado_livre_1")

# Executa uma operação
import asyncio
result = asyncio.run(ml_connector.execute_operation(
    operation="list_products",
    params={"limit": 10}
))

# Obtém detalhes de um produto
product = asyncio.run(ml_connector.execute_operation(
    operation="get_product",
    params={"product_id": "MLB123456"}
))
```

## Considerações para Produção

### Uso de Redis

Para ambientes de produção, recomenda-se fortemente o uso do Redis para:

1. **Caching**: Melhora significativamente o desempenho
2. **Persistência de Estado**: Garante que o estado seja preservado entre reinicializações
3. **Comunicação Distribuída**: Permite escalar horizontalmente

### Segurança

1. **Armazenamento Seguro de Credenciais**: Nunca armazene credenciais no código-fonte
2. **HTTPS**: Use HTTPS para todas as comunicações externas
3. **Controle de Acesso**: Implemente autenticação e autorização para a API

### Monitoramento

1. **Logging**: Configure adequadamente o nível de logging
2. **Métricas**: Monitore o desempenho e uso de recursos
3. **Alertas**: Configure alertas para condições críticas

## Solução de Problemas

### Problemas Comuns

1. **Erro de Conexão com Redis**: Verifique se o Redis está em execução e acessível
2. **Falha na Autenticação com MCPs**: Verifique as credenciais e a validade dos tokens
3. **Mensagens Não Entregues**: Verifique se os manipuladores estão registrados corretamente

### Logs

Os logs são uma ferramenta valiosa para diagnóstico. Configure o nível de logging adequado:

```
LOG_LEVEL=DEBUG  # Para desenvolvimento
LOG_LEVEL=INFO   # Para produção
```

## Próximos Passos

1. **Implementação de Crews Adicionais**: Expanda para outras plataformas
2. **Interface de Usuário**: Desenvolva uma interface para monitoramento e controle
3. **Análise de Dados**: Implemente recursos avançados de análise
4. **Integração com Modelos de IA**: Conecte com modelos de linguagem avançados
