# Integração MCP com CrewAI - Relatório Técnico

## Resumo Executivo

Este documento resume o trabalho de integração entre o CrewAI e servidores MCP (Model Context Protocol) no projeto ai-stack, especificamente com MCP-Redis e MCP-MongoDB. Detalhamos os desafios encontrados, soluções implementadas e próximos passos recomendados.

## Objetivos do Projeto

1. Integrar o CrewAI com servidores MCP para disponibilizar ferramentas externas aos agentes
2. Testar e validar a conexão com MCP-Redis e MCP-MongoDB
3. Resolver problemas de compatibilidade entre os diferentes transportes MCP

## Resultados Principais

### MCP-Redis

✅ **SUCESSO**: Integração com MCP-Redis funcionando corretamente.

- O MCP-Redis implementa o transporte SSE (Server-Sent Events) no endpoint `/sse`
- O MCPServerAdapter do CrewAI conecta-se perfeitamente ao MCP-Redis
- Os agentes conseguem descobrir e utilizar as ferramentas expostas pelo MCP-Redis

**Configuração de Teste Bem-Sucedida:**

```python
# URL do MCP-Redis com transporte SSE
redis_url = "http://localhost:8002/sse"
print_info(f"Tentando conectar ao MCP-Redis em: {redis_url}")

# Tenta conectar ao MCP-Redis
with MCPServerAdapter({"url": redis_url}) as redis_tools:
    tool_count = len(redis_tools)
    print_success(f"Conexão estabelecida com MCP-Redis!")
    print_success(f"Ferramentas descobertas: {tool_count}")
```

**Resultado:** Conexão bem-sucedida com 42 ferramentas descobertas, incluindo operações Redis como `get`, `set`, `hget`, `hset`, `lpush`, `rpush`, `sadd`, `publish`, entre outras.

### MCP-MongoDB

❌ **DESAFIO**: Integração com MCP-MongoDB apresentou incompatibilidades.

- O MCP-MongoDB implementa apenas endpoints REST, sem suporte nativo a SSE
- O MCPServerAdapter do CrewAI espera um servidor MCP com suporte a SSE ou streamable-http
- Tentativas de configuração com diferentes transportes (`http`, `sse`, `streamable-http`, `rest`) não foram bem-sucedidas

**Tentativas de Configuração Testadas:**

1. **Configuração com URL Base:**
```python
{"url": "http://localhost:8001"}
```

2. **Configuração com Transporte HTTP:**
```python
{"url": "http://localhost:8001", "transport": "http"}
```
**Erro:** `ValueError: Invalid transport, expected sse or streamable-http found 'http'`

3. **Configuração com Transporte Streamable-HTTP:**
```python
{"url": "http://localhost:8001", "transport": "streamable-http"}
```
**Erro:** `mcp.shared.exceptions.McpError: Session terminated`

4. **Configuração com Transporte REST:**
```python
{"url": "http://localhost:8001", "transport": "rest"}
```
**Erro:** `ValueError: Invalid transport, expected sse or streamable-http found 'rest'`

**Nota:** Apesar das falhas com o MCPServerAdapter, a conexão direta via HTTP com os endpoints REST do MCP-MongoDB funciona perfeitamente:

```python
# Verificar endpoint de saúde
health_response = requests.get("http://localhost:8001/health")
health_data = health_response.json()
# Resultado: {'status': 'healthy', 'mongodb': 'connected', 'multi_tenant': True, 'default_tenant': 'account_1'}

# Verificar endpoint de ferramentas
tools_response = requests.get("http://localhost:8001/tools")
tools_data = tools_response.json()
# Resultado: 3 ferramentas disponíveis (query, aggregate, getCompanyConfig)
```

## Análise Técnica

### Arquitetura MCP

O protocolo MCP (Model Context   Protocol) permite que servidores exponham ferramentas para serem utilizadas por agentes de IA. Existem diferentes tipos de transporte no protocolo MCP:

1. **SSE (Server-Sent Events)**: Implementado pelo MCP-Redis, permite streaming de eventos do servidor para o cliente
2. **HTTP/REST**: Implementado pelo MCP-MongoDB, baseado em requisições HTTP padrão
3. **streamable-http**: Uma variante do HTTP que suporta streaming, esperada pelo MCPServerAdapter
4. **STDIO**: Para comunicação local via entrada/saída padrão

### Testes Realizados

1. **Conexão direta com endpoints REST do MCP-MongoDB**:
   - Endpoint `/health`: Retorna status "healthy"
   - Endpoint `/tools`: Lista 3 ferramentas disponíveis (query, aggregate, getCompanyConfig)

2. **Tentativas com MCPServerAdapter**:
   - Configuração com transporte `http`: Erro "Invalid transport, expected sse or streamable-http"
   - Configuração com transporte `streamable-http`: Erro "Session terminated"
   - Configuração com transporte `rest`: Erro "Invalid transport"

3. **Verificação de compatibilidade**:
   - O MCPServerAdapter do CrewAI aceita apenas os transportes "sse" ou "streamable-http"
   - O MCP-MongoDB atual implementa apenas endpoints REST padrão

## Solução Proposta: Adaptador Personalizado

Para resolver a incompatibilidade entre o MCPServerAdapter e o MCP-MongoDB, iniciamos o desenvolvimento de um adaptador personalizado que:

1. Conecta-se diretamente aos endpoints REST do MCP-MongoDB
2. Descobre automaticamente as ferramentas disponíveis
3. Converte essas ferramentas em objetos `Tool` compatíveis com o CrewAI
4. Permite que os agentes utilizem essas ferramentas de forma transparente

### Implementação do Adaptador

```python
class MongoDBAdapter:
    """Adaptador personalizado para conectar o MCP-MongoDB ao CrewAI."""
    
    def __init__(self, base_url: str = "http://localhost:8001", tenant_id: str = "account_1"):
        """Inicializa o adaptador para o MCP-MongoDB."""
        self.base_url = base_url
        self.tenant_id = tenant_id
        self._tools = None
    
    def _fetch_tools(self):
        """Busca a lista de ferramentas disponíveis no MCP-MongoDB."""
        response = requests.get(f"{self.base_url}/tools")
        response.raise_for_status()
        return response.json()["tools"]
    
    def _create_tool_function(self, tool_name: str):
        """Cria uma função que executa a ferramenta via API REST."""
        def execute_tool(**kwargs):
            if "tenant_id" not in kwargs:
                kwargs["tenant_id"] = self.tenant_id
            response = requests.post(
                f"{self.base_url}/tools/{tool_name}", 
                json=kwargs
            )
            response.raise_for_status()
            return response.json()
        return execute_tool
    
    @property
    def tools(self):
        """Obtém as ferramentas como objetos Tool do CrewAI."""
        if self._tools is None:
            raw_tools = self._fetch_tools()
            self._tools = [
                Tool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    func=self._create_tool_function(tool_data["name"])
                )
                for tool_data in raw_tools
            ]
        return self._tools
```

### Exemplo de Uso com CrewAI

```python
from mongodb_adapter import MongoDBAdapter
from crewai import Agent, Task, Crew

# Criar adaptador e obter ferramentas
adapter = MongoDBAdapter(base_url="http://localhost:8001")
mongodb_tools = adapter.tools

# Criar agente com as ferramentas do MCP-MongoDB
agent = Agent(
    role="Analista de Dados",
    goal="Analisar dados da empresa",
    backstory="Especialista em consultas MongoDB",
    tools=mongodb_tools
)

# Criar tarefa
task = Task(
    description="Consultar configurações da empresa na coleção 'company_services'",
    agent=agent
)

# Executar crew
crew = Crew(agents=[agent], tasks=[task])
resultado = crew.kickoff()
```

### Vantagens do Adaptador Personalizado

- Não requer modificações no código do MCP-MongoDB
- Mantém a experiência de uso consistente com o padrão CrewAI
- Permite descoberta dinâmica de ferramentas
- Não exige definição manual de cada ferramenta nos agentes

## Próximos Passos

### 1. Plano de Desenvolvimento do MongoDB Adapter

O desenvolvimento do MongoDB Adapter é necessário devido à incompatibilidade fundamental entre o MCPServerAdapter padrão do CrewAI (que espera transportes SSE ou streamable-http) e o MCP-MongoDB (que implementa apenas endpoints REST). Nossa estratégia de implementação inclui:

#### 1.1. Justificativa para o Adaptador Personalizado

- **Incompatibilidade de Transporte**: O MCPServerAdapter do CrewAI foi projetado para trabalhar com transportes de streaming (SSE ou streamable-http), enquanto o MCP-MongoDB implementa apenas endpoints REST síncronos.
- **Preservação da Arquitetura Existente**: Não queremos modificar o código do MCP-MongoDB, que é um componente estável e testado.
- **Experiência Consistente**: Precisamos manter a mesma experiência de uso para os agentes CrewAI, independentemente do backend MCP utilizado.
- **Suporte Multi-tenant**: O adaptador precisa suportar a arquitetura multi-tenant do ChatwootAI, onde cada tenant é identificado por um account_id único.

#### 1.2. Arquitetura do MongoDB Adapter

O MongoDB Adapter será implementado como uma classe Python que:

1. **Descoberta Dinâmica de Ferramentas**:
   - Conecta-se ao endpoint `/tools` do MCP-MongoDB via REST
   - Analisa o schema das ferramentas disponíveis
   - Cria objetos `Tool` compatíveis com CrewAI dinamicamente

2. **Execução Transparente**:
   - Intercepta chamadas de ferramentas dos agentes
   - Traduz essas chamadas para requisições REST ao endpoint `/tools/{tool_name}`
   - Gerencia parâmetros, incluindo o tenant_id automaticamente
   - Formata e retorna os resultados de forma consistente

3. **Gerenciamento de Estado**:
   - Implementa interface de context manager (`__enter__`/`__exit__`)
   - Gerencia conexões e recursos de forma adequada
   - Suporta caching de ferramentas para melhor performance

#### 1.3. Componentes Principais do Adaptador

```
MongoDBAdapter
├── __init__(base_url, tenant_id, timeout, headers)
├── connect() -> bool
├── disconnect() -> None
├── tools -> List[BaseTool]
├── refresh_tools() -> List[BaseTool]
├── check_health() -> Dict
└── MongoDBTool (classe interna)
    ├── __init__(name, description, func, parameters)
    ├── _run(**kwargs) -> str
    └── arun(**kwargs) -> str (para suporte assíncrono)
```

#### 1.4. Tarefas de Implementação

- [x] Implementação básica do adaptador (mongodb_adapter.py)
- [x] Implementação avançada com tratamento de erros (mongodb_adapter_final.py)
- [ ] Testes de integração com diferentes configurações do MCP-MongoDB
- [ ] Implementação de caching e otimizações de performance
- [ ] Documentação completa e exemplos de uso
- [ ] Testes de carga e estabilidade

### 2. Integração com o Fluxo de Trabalho do CrewAI

#### 2.1. Criação de Exemplos de Uso

Desenvolveremos exemplos completos que demonstram:

- Conexão ao MCP-MongoDB via adaptador personalizado
- Criação de agentes com ferramentas MongoDB
- Execução de tarefas que utilizam essas ferramentas
- Tratamento de erros e casos de borda

#### 2.2. Documentação do Processo de Integração

- Guia passo a passo para integração
- Exemplos de configuração para diferentes cenários
- Troubleshooting de problemas comuns
- Melhores práticas para uso em produção

#### 2.3. Testes de Compatibilidade

- Verificação de compatibilidade com diferentes versões do CrewAI
- Testes com diferentes configurações do MCP-MongoDB
- Validação em ambientes multi-tenant

### 3. Considerações de Longo Prazo

#### 3.1. Evolução do MCP-MongoDB

- Avaliar a possibilidade de adicionar suporte a SSE no MCP-MongoDB
- Implementar o transporte streamable-http no MCP-MongoDB
- Manter compatibilidade com a implementação REST atual

#### 3.2. Contribuições para o Ecossistema CrewAI

- Propor melhorias para o MCPServerAdapter para suportar mais tipos de transporte
- Compartilhar a implementação do adaptador com a comunidade
- Documentar as lições aprendidas para outros implementadores de MCP

#### 3.3. Monitoramento e Manutenção

- Implementar logging detalhado para diagnóstico
- Adicionar métricas de performance e uso
- Estabelecer processo de atualização para acompanhar mudanças no CrewAI e MCP-MongoDB

## Conclusão

A integração do CrewAI com servidores MCP é uma adição valiosa ao projeto ai-stack, permitindo que agentes utilizem ferramentas externas de forma dinâmica. Embora o MCP-Redis funcione perfeitamente com o MCPServerAdapter padrão, o MCP-MongoDB requer uma abordagem personalizada devido às diferenças no protocolo de transporte.

O desenvolvimento de um adaptador personalizado para o MCP-MongoDB permitirá que os agentes do CrewAI utilizem as ferramentas MongoDB sem exigir modificações no servidor MCP ou definições manuais de ferramentas, mantendo a experiência de uso consistente e simplificada.
