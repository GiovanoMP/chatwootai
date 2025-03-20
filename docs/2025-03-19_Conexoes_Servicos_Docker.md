# Documentação de Conexão aos Serviços Docker - ChatwootAI
**Data: 19/03/2025 - Atualizado às 22:32**

Este documento descreve a configuração atual e funcional para conexão aos serviços de dados (PostgreSQL, Redis e Qdrant) utilizando Docker no projeto ChatwootAI, bem como o status atual dos testes de integração.

## Configuração Atual Funcionando

### PostgreSQL
- **Endereço**: `localhost`
- **Porta**: `5433` (mapeada do container `5432` para `5433` no host)
- **Banco de dados**: `chatwootai`
- **Usuário/Senha**: Conforme definido nas variáveis POSTGRES_USER e POSTGRES_PASSWORD no .env

### Redis
- **Endereço interno Docker**: `172.26.0.2` (IP da rede interna Docker)
- **Porta**: `6379`
- **URL completa via IP interno**: `redis://172.26.0.2:6379/0`
- **URL alternativa via localhost**: `redis://localhost:6379/0` (recomendado quando executando fora do Docker)

### Qdrant
- **Endereço**: `localhost`
- **Porta**: `6335` (mapeada do container `6333` para `6335` no host)
- **URL completa**: `http://localhost:6335`

## Variáveis de Ambiente (.env)

As seguintes configurações estão atualmente no arquivo `.env` e funcionam corretamente:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
REDIS_URL=redis://172.26.0.2:6379/0
REDIS_HOST=172.26.0.2
REDIS_PORT=6379
QDRANT_URL=http://localhost:6335
```

Alternativamente, para conexões a partir do host (fora dos containers Docker):

```
# Usando localhost para Redis também
REDIS_URL=redis://localhost:6379/0
```

## Notas Importantes

1. **PostgreSQL e Qdrant**: Estão configurados com mapeamento de portas no `docker-compose.yml` e são acessíveis via `localhost`.

2. **Redis**: O Redis pode ser acessado de duas formas:
   - **Pelo IP interno do Docker** (recomendado para acesso entre containers): `172.26.0.2:6379`
   - **Via localhost** (recomendado para acesso a partir do host): `localhost:6379`, já que configuramos o mapeamento de porta no `docker-compose.yml`.

3. **Atenção com o IP interno do Redis**: Este IP pode mudar quando o Docker for reiniciado. Se isso ocorrer, é necessário atualizar o arquivo `.env` com o novo IP. Para evitar este problema, considere utilizar sempre a conexão via `localhost:6379` quando estiver executando fora dos containers.

4. **Quando Executar Dentro dos Containers**: Se estiver executando código dentro dos containers Docker, use os nomes dos serviços como hosts:
   - PostgreSQL: `postgres:5432`
   - Redis: `redis:6379`
   - Qdrant: `qdrant:6333`

## Verificação da Configuração

Para verificar se a configuração está funcionando corretamente, execute o script de teste:

```bash
python tests/test_forced_connections.py
```

Este script testa a conexão com todos os serviços e verifica se os serviços registrados no `DataServiceHub` estão funcionando adequadamente.

## Status Atual da Integração (Atualizado em 19/03/2025)

### Serviços Funcionando Corretamente:

- **PostgreSQL**: ✅ Conectando com sucesso
- **Redis**: ✅ Conectando com sucesso
- **Qdrant**: ✅ Conectando com sucesso
- **DataServiceHub**: ✅ Inicializando e gerenciando conexões
- **DataProxyAgent**: ✅ Inicializando com ferramentas de dados integradas

### Serviços de Dados Registrados e Funcionais:

- **ProductDataService**: ✅ Registrado com sucesso
- **CustomerDataService**: ✅ Registrado com sucesso
- **ConversationContextService**: ✅ Registrado com sucesso
- **ConversationAnalyticsService**: ✅ Registrado com sucesso
- **DomainRulesService**: ✅ Registrado com sucesso (com domínios 'cosméticos' e 'saúde')

### Componentes Verificados:

- **DataProxyAgent**: ✅ Inicialização bem sucedida (corrigido o parâmetro data_service_hub)

## Status dos Testes de Integração (Atualizado às 22:37)

### Suites de Teste:

1. **Testes de Conexão**: ✅ PASSOU
   - Verificação de conexões com PostgreSQL, Redis e Qdrant
   - Inicialização do DataServiceHub 
   - Inicialização do DataProxyAgent

2. **Testes de Integração do Hub**: ✅ PASSOU
   - **Hub Proxy Integration**: Integração entre o Hub e o DataProxyAgent
   - **Proxy Agent Tools**: Verificação das ferramentas do DataProxyAgent 
   - **Adaptable Agent Integration**: Integração entre agentes adaptáveis e o sistema

3. **Testes de Integração das Crews**: ❌ FALHOU
   - Erro ao importar o módulo `src.agents.channel_agents`
   - Este módulo provavelmente foi movido ou renomeado durante a reorganização da estrutura

### Problemas Resolvidos Hoje (19/03/2025):

1. **Importação do Plugin Manager**: Corrigida a importação do BasePlugin na classe PluginManager para apontar para o novo local (`src.plugins.base.base_plugin` em vez de `.base`).

2. **Inicialização do DataProxyAgent**: Corrigidos dois problemas importantes:
   - No `DataServiceHub.get_data_proxy_agent()`, adicionado o parâmetro obrigatório `data_service_hub=self` na criação do DataProxyAgent
   - No `HubCrew.__init__()`, corrigida a atribuição de `_data_proxy_agent` para usar a variável existente `data_proxy` em vez de uma variável inexistente

## Refatoração da Integração entre Agentes CrewAI - 20/03/2025 (00:05)

### Problemas Resolvidos:

1. **Erro com ClassVar no Pydantic**: 
   - Problema: As classes `AdaptableAgent` e `SalesAgent` utilizavam `ClassVar` para campos que não deveriam ser parte do modelo Pydantic, causando erro: "ClassVar cannot be set on an instance"
   - Solução: Substituição de `ClassVar` por `PrivateAttr`, que é a abordagem recomendada pelo Pydantic para atributos privados
   - Arquivos alterados:
     - `src/agents/base/adaptable_agent.py`
     - `src/agents/specialized/sales_agent.py`

2. **Incompatibilidade do DataProxyAgent com CrewAI**:
   - Problema: O DataProxyAgent não implementava os métodos esperados pelo CrewAI (como `.get()`) causando erro durante a execução dos testes de integração
   - Solução: Adicionados métodos delegativos no DataProxyAgent que permitem:
     - Interoperabilidade com dicionários (via `get()` e `__getitem__()`)
     - Delegação para o agente CrewAI interno (propriedades como `role`, `goal`, etc.)
     - Compatibilidade com operações de dicionário (método `keys()`)
   - Arquivo alterado: `src/core/data_proxy_agent.py`

### Status Atual dos Testes:

- ✅ `test_functional_crews_initialization`: Passou com sucesso após as correções
- ❌ `test_crew_messaging_flow`: Falha relacionada à incompatibilidade de interfaces
- ❌ `test_whatsapp_crew_initialization`: Falha no argumento `channel_type` na inicialização

### Próximos Passos:

1. ~~Corrigir a inicialização do DataProxyAgent~~ ✅ **RESOLVIDO**
2. Corrigir incompatibilidades nas interfaces entre os componentes do sistema
3. Resolver problemas na inicialização do WhatsAppChannelCrew
4. Implementar testes de integração completos para verificar o fluxo de dados
5. Testar a integração entre o Webhook do Chatwoot e o sistema refatorado
6. Documentar padrões de acesso a dados para desenvolvedores
7. Implementar testes de desempenho para avaliar a escalabilidade da solução
