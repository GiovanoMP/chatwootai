# Plano de Implementação: Configuração YAML e Sistema Multi-Tenant

**Data:** 2025-03-24  
**Autor:** Equipe de Desenvolvimento ChatwootAI  
**Versão:** 1.1

## Sumário

1. [Introdução](#introdução)
2. [Sistema Multi-Tenant](#sistema-multi-tenant)
3. [Estratégia de Persistência e Cache](#estratégia-de-persistência-e-cache)
4. [Próximos Passos de Implementação](#próximos-passos-de-implementação)
5. [Componentes a Serem Refatorados/Removidos](#componentes-a-serem-refatoradosremovidos)
6. [Estratégia de Testes](#estratégia-de-testes)
7. [Cronograma Estimado](#cronograma-estimado)

## Introdução

Este documento descreve o plano de implementação para a transição do ChatwootAI para um sistema baseado em configuração YAML e com suporte multi-tenant completo. O objetivo é permitir que o sistema sirva diferentes domínios de negócio (cosméticos, saúde, varejo, etc.) de forma dinâmica e configurável, sem necessidade de alterações no código-fonte.

A arquitetura proposta segue o princípio de "configuração como código", onde todo o comportamento dos agentes, crews e fluxos de trabalho é definido em arquivos YAML, que são carregados e interpretados em tempo de execução.

## Sistema Multi-Tenant

### Abordagem Selecionada

Implementaremos um sistema multi-tenant flexível que permita:

1. **Associação de Domínios por Conversação**:
   - Cada conversa pode ter seu próprio domínio associado
   - Isso permite atender clientes de diferentes setores simultaneamente
   - Persiste a associação entre conversas e domínios via Redis

2. **Seleção de Domínio para Testes**:
   - Via variável de ambiente `CHATWOOT_DOMAIN`
   - Via interface administrativa para alteração em tempo real

### Implementação do DomainManager

O `DomainManager` será atualizado para dar suporte a este modelo:

```python
def get_domain_for_conversation(self, conversation_id: str, refresh_cache=False):
    """Determina o domínio a ser usado para uma conversa específica."""
    # Verificar cache em memória primeiro para performance
    if not refresh_cache and conversation_id in self._domain_cache:
        return self._domain_cache[conversation_id]
    
    # Se não estiver em cache e Redis disponível, consultar Redis
    if self.redis_client:
        redis_key = f"domain:conversation:{conversation_id}"
        domain = self.redis_client.get(redis_key)
        
        if domain:
            domain_name = domain.decode()
            self._domain_cache[conversation_id] = domain_name
            return domain_name
    
    # Retorna o domínio padrão se não encontrar específico
    return self.default_domain

def set_conversation_domain(self, conversation_id: str, domain_name: str):
    """Define o domínio para uma conversação específica."""
    # Validar se o domínio existe
    if not self.loader.domain_exists(domain_name):
        raise ValueError(f"Domínio não encontrado: {domain_name}")
    
    # Atualizar cache em memória
    self._domain_cache[conversation_id] = domain_name
    
    # Persistir no Redis se disponível
    if self.redis_client:
        redis_key = f"domain:conversation:{conversation_id}"
        self.redis_client.set(redis_key, domain_name, ex=86400)  # 24 horas
    
    return True
```

### Interface de Administração

Para facilitar testes e mudanças em tempo real, será implementada uma API simples:

```python
@app.route('/api/admin/domain', methods=['POST'])
def set_domain():
    data = request.json
    conversation_id = data.get('conversation_id')
    domain_name = data.get('domain')
    
    try:
        # Se conversation_id for fornecido, define apenas para essa conversa
        if conversation_id:
            domain_manager.set_conversation_domain(conversation_id, domain_name)
            return {"success": True, "message": f"Domínio {domain_name} definido para conversa {conversation_id}"}
        
        # Caso contrário, define globalmente para testes
        else:
            domain_manager.active_domain_name = domain_name
            domain_manager.active_domain_config = domain_manager.loader.load_domain(domain_name)
            return {"success": True, "message": f"Domínio de teste global alterado para {domain_name}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}, 400
```

## Estratégia de Persistência e Cache

Um aspecto crítico do sistema multi-tenant é garantir que, uma vez carregados e instanciados, os domínios, crews e agentes sejam persistidos e reutilizados em conversas subsequentes. Isso evita o recarregamento e reinstanciação a cada nova interação, melhorando significativamente a performance e consistência.

### Infraestrutura Redis Existente

O projeto já possui uma infraestrutura Redis configurada via Docker, que será utilizada para implementar a persistência do sistema multi-tenant. Esta infraestrutura existente é ideal para nosso caso de uso, pois:

1. **Já está configurada e testada**: Conforme demonstrado em `tests/test_redis_connection.py`
2. **Suporta todas as operações necessárias**: Operações de hash, expiração de chaves, e armazenamento de estruturas complexas
3. **Alta performance**: Ideal para cache e persistência de curto/médio prazo
4. **Escalabilidade**: Capaz de lidar com múltiplos domínios e clientes simultaneamente

#### Conexão com Redis

A conexão com o Redis é feita através do cliente padrão, conforme implementado nos testes:

```python
import redis

# Configurações do Redis - priorizando variáveis de ambiente
redis_config = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', '6379')),
    'db': int(os.environ.get('REDIS_DB', '0')),
    'password': os.environ.get('REDIS_PASSWORD', None)
}

# Conectar ao Redis
redis_client = redis.Redis(
    host=redis_config['host'],
    port=redis_config['port'],
    db=redis_config['db'],
    password=redis_config['password'],
    decode_responses=True,
    socket_timeout=2.0
)
```

#### Estratégia de Chaves para Multi-Tenant

Para garantir o isolamento de dados entre diferentes domínios e clientes, adotaremos a seguinte convenção de nomenclatura de chaves:

```
domain:config:{nome_do_dominio}                 # Configuração de um domínio
domain:conversation:{conversation_id}           # Associação entre conversa e domínio
agent:state:{dominio}:{agent_id}:{conversa_id}  # Estado de um agente em uma conversa
```

Esta estrutura de chaves garante:

1. **Isolamento de dados**: Cada domínio e cliente tem seus próprios dados separados
2. **Fácil busca**: Podemos usar padrões de busca como `domain:*` para listar todas as chaves relacionadas a domínios
3. **Organização clara**: A estrutura hierárquica facilita entender o que cada chave representa

#### Políticas de Expiração

Para otimizar o uso de memória, implementaremos as seguintes políticas de TTL (Time-To-Live):

- **Configurações de domínio**: 3600 segundos (1 hora)
- **Associação conversa-domínio**: 86400 segundos (24 horas)
- **Estado de agentes**: 86400 segundos (24 horas)

Estas políticas podem ser ajustadas conforme necessário, baseado em padrões de uso e requisitos de memória.

### 1. Persistência de Configurações YAML

As configurações YAML serão carregadas apenas uma vez e persistidas:

```python
class DomainRegistry:
    """Registro centralizado de configurações de domínio."""
    
    def __init__(self, redis_client=None):
        self._configs = {}  # Cache em memória
        self.redis_client = redis_client
    
    def get_domain_config(self, domain_name):
        """Obtém configuração do domínio, usando cache quando possível."""
        # Verificar cache em memória primeiro
        if domain_name in self._configs:
            return self._configs[domain_name]
        
        # Verificar Redis
        if self.redis_client:
            redis_key = f"domain:config:{domain_name}"
            cached_config = self.redis_client.get(redis_key)
            if cached_config:
                config = json.loads(cached_config.decode())
                self._configs[domain_name] = config
                return config
        
        # Carregar do sistema de arquivos
        loader = DomainLoader()
        config = loader.load_domain(domain_name)
        
        # Persistir em Redis
        if self.redis_client and config:
            redis_key = f"domain:config:{domain_name}"
            self.redis_client.set(redis_key, json.dumps(config), ex=3600)  # 1 hora
        
        # Atualizar cache em memória
        self._configs[domain_name] = config
        
        return config
```

### 2. Cache de Instâncias de Crews

As crews e agentes serão instanciados apenas uma vez por domínio:

```python
class CrewRegistry:
    """Registro centralizado de crews instanciadas."""
    
    def __init__(self, crew_factory):
        self.crew_factory = crew_factory
        self._crews = {}  # Cache de crews instanciadas
    
    def get_crew(self, crew_id, domain_name, crew_config=None):
        """
        Obtém uma crew pelo ID, usando cache quando possível.
        
        Args:
            crew_id: Identificador da crew
            domain_name: Nome do domínio
            crew_config: Configuração opcional, se não fornecida será obtida do domínio
            
        Returns:
            Instância da crew
        """
        # Chave de cache composta
        cache_key = f"{domain_name}:{crew_id}"
        
        # Verificar cache de instâncias
        if cache_key in self._crews:
            return self._crews[cache_key]
        
        # Se não fornecida, obter configuração do domínio
        if not crew_config:
            domain_registry = DomainRegistry()
            domain_config = domain_registry.get_domain_config(domain_name)
            crew_config = domain_config.get("crews", {}).get(crew_id)
            
            if not crew_config:
                raise ValueError(f"Configuração para crew {crew_id} não encontrada no domínio {domain_name}")
        
        # Criar nova instância da crew
        crew = self.crew_factory.create_crew(crew_config, domain_name)
        
        # Armazenar em cache
        self._crews[cache_key] = crew
        
        return crew
    
    def invalidate_crew(self, crew_id, domain_name):
        """Invalida o cache de uma crew específica."""
        cache_key = f"{domain_name}:{crew_id}"
        if cache_key in self._crews:
            del self._crews[cache_key]
    
    def invalidate_domain(self, domain_name):
        """Invalida todas as crews de um domínio específico."""
        keys_to_remove = []
        for key in self._crews.keys():
            if key.startswith(f"{domain_name}:"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._crews[key]
```

### 3. Persistência de Estado do Agente

Os agentes terão estado persistente entre interações:

```python
class AgentStateManager:
    """Gerenciador de estado persistente dos agentes."""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
    
    def save_agent_state(self, agent_id, domain_name, conversation_id, state):
        """
        Salva o estado do agente para uma conversa específica.
        
        Args:
            agent_id: Identificador do agente
            domain_name: Nome do domínio
            conversation_id: ID da conversa
            state: Estado a ser persistido (dict)
        """
        if not self.redis_client:
            return False
            
        key = f"agent:state:{domain_name}:{agent_id}:{conversation_id}"
        self.redis_client.set(key, json.dumps(state), ex=86400)  # 24 horas
        return True
    
    def load_agent_state(self, agent_id, domain_name, conversation_id):
        """
        Carrega o estado persistido de um agente.
        
        Returns:
            dict: Estado do agente ou {} se não encontrado
        """
        if not self.redis_client:
            return {}
            
        key = f"agent:state:{domain_name}:{agent_id}:{conversation_id}"
        state_data = self.redis_client.get(key)
        
        if not state_data:
            return {}
            
        return json.loads(state_data.decode())
```

### 4. Sistema Integrado de Inicialização e Persistência

A integração desses componentes no sistema principal:

```python
class ChatwootAISystem:
    """Sistema principal do ChatwootAI com suporte a persistência."""
    
    def __init__(self, redis_client=None):
        # Inicializar componentes com suporte a persistência
        self.redis_client = redis_client
        self.domain_registry = DomainRegistry(redis_client)
        self.domain_manager = DomainManager(redis_client=redis_client)
        self.data_proxy_agent = DataProxyAgent()
        self.tool_registry = ToolRegistry()
        self.crew_factory = CrewFactory(self.data_proxy_agent, self.memory_system, self.tool_registry)
        self.crew_registry = CrewRegistry(self.crew_factory)
        self.agent_state_manager = AgentStateManager(redis_client)
        
        # Inicializar o HubCrew
        self.hub_crew = self._initialize_hub_crew()
        
        logger.info("Sistema ChatwootAI inicializado com suporte a persistência")
    
    def _initialize_hub_crew(self):
        """Inicializa o HubCrew com os componentes necessários."""
        # Implementação do HubCrew com suporte a persistência
        # ...
    
    def process_message(self, message, conversation_id, channel="whatsapp"):
        """
        Processa uma mensagem, utilizando componentes persistidos quando disponíveis.
        
        Args:
            message: Mensagem a ser processada
            conversation_id: ID da conversa
            channel: Canal de comunicação
            
        Returns:
            Resposta processada
        """
        # 1. Determinar o domínio da conversa
        domain_name = self.domain_manager.get_domain_for_conversation(conversation_id)
        
        # 2. Obter configuração do domínio (do cache)
        domain_config = self.domain_registry.get_domain_config(domain_name)
        
        # 3. Determinar a crew apropriada com base na mensagem
        crew_id = self.hub_crew.determine_appropriate_crew(message, domain_name)
        
        # 4. Obter a crew do registro (já instanciada se existir)
        specialized_crew = self.crew_registry.get_crew(crew_id, domain_name)
        
        # 5. Para cada agente na crew, carregar estado persistente
        for agent in specialized_crew.agents:
            state = self.agent_state_manager.load_agent_state(
                agent.id, domain_name, conversation_id
            )
            agent.restore_state(state)
        
        # 6. Processar a mensagem com a crew especializada
        result = specialized_crew.process(message, context={"conversation_id": conversation_id})
        
        # 7. Persistir o estado dos agentes após o processamento
        for agent in specialized_crew.agents:
            state = agent.get_state()
            self.agent_state_manager.save_agent_state(
                agent.id, domain_name, conversation_id, state
            )
        
        return result
```

Esta abordagem garante que:

1. As configurações YAML sejam carregadas apenas uma vez e armazenadas em cache
2. Crews e agentes sejam instanciados uma única vez por domínio
3. O estado dos agentes seja persistido entre interações da mesma conversa
4. O sistema não precise recarregar e reinstanciar componentes a cada mensagem

### 5. Estratégia de Invalidação de Cache

Para garantir que alterações em configurações sejam aplicadas, implementaremos uma estratégia de invalidação:

```python
def update_domain_configuration(domain_name, new_config=None):
    """
    Atualiza a configuração de um domínio e invalida caches.
    
    Args:
        domain_name: Nome do domínio a ser atualizado
        new_config: Nova configuração (opcional)
    """
    # 1. Se nova configuração fornecida, atualizar no DomainRegistry
    if new_config:
        domain_registry.update_domain_config(domain_name, new_config)
    
    # 2. Invalidar cache de crews deste domínio
    crew_registry.invalidate_domain(domain_name)
    
    # 3. Recarregar ferramentas conforme necessário
    tool_registry.reload_domain_tools(domain_name)
    
    # 4. Notificar componentes sobre a mudança
    # Implementação de observer pattern ou similar
    
    logger.info(f"Configuração do domínio {domain_name} atualizada e caches invalidados")
```

## Próximos Passos de Implementação

### 1. Melhorar o DomainLoader

O `DomainLoader` atual já está bem estruturado, mas precisa de algumas melhorias:

- **Validação de Configuração**:
  - Implementar validação completa de esquema YAML
  - Verificar referências cruzadas (ex: agentes referenciados em crews devem existir)
  - Aplicar validações específicas por tipo de componente

- **Suporte a Herança Múltipla**:
  - Permitir que um domínio herde de múltiplos domínios base
  - Resolver conflitos de herança com regras claras

- **Interface de Debug**:
  - Adicionar logs detalhados para rastreamento de carregamento
  - Implementar modo "dryrun" para validar configurações sem aplicá-las

### 2. Implementar o CrewFactory

Criar um `CrewFactory` responsável por instanciar dinamicamente crews e agentes a partir da configuração YAML:

```python
class CrewFactory:
    """
    Fábrica para criar crews e agentes a partir de configurações YAML.
    """
    
    def __init__(self, data_proxy_agent, memory_system, tool_registry):
        self.data_proxy_agent = data_proxy_agent
        self.memory_system = memory_system
        self.tool_registry = tool_registry
        self.agent_class_cache = {}
    
    def _load_agent_class(self, type_name):
        """Carrega dinamicamente uma classe de agente pelo nome."""
        if type_name in self.agent_class_cache:
            return self.agent_class_cache[type_name]
            
        # Mapeamento de nomes simplificados para caminhos completos
        class_mapping = {
            "SalesAgent": "src.agents.specialized.sales_agent.SalesAgent",
            "SupportAgent": "src.agents.specialized.support_agent.SupportAgent",
            "SchedulingAgent": "src.agents.specialized.scheduling_agent.SchedulingAgent"
        }
        
        # Se o tipo está no mapeamento, usar o caminho completo
        full_path = class_mapping.get(type_name, type_name)
        
        try:
            # Dividir o caminho em módulo e classe
            module_path, class_name = full_path.rsplit('.', 1)
            
            # Importar dinamicamente
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # Armazenar em cache
            self.agent_class_cache[type_name] = agent_class
            return agent_class
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Não foi possível carregar a classe de agente {type_name}: {e}")
    
    def create_agent(self, agent_id, agent_config, domain_name):
        """
        Cria um agente a partir da configuração.
        
        Args:
            agent_id: Identificador do agente
            agent_config: Configuração do agente do YAML
            domain_name: Nome do domínio ativo
        
        Returns:
            Instância do agente
        """
        agent_type = agent_config.get("type")
        agent_class = self._load_agent_class(agent_type)
        
        # Obter ferramentas atribuídas ao agente
        tool_ids = agent_config.get("tools", [])
        tools = [self.tool_registry.get_tool(tool_id) for tool_id in tool_ids]
        
        # Criar instância do agente com parâmetros obrigatórios
        agent_instance = agent_class(
            data_proxy_agent=self.data_proxy_agent,
            memory_system=self.memory_system,
            # Incluir qualquer configuração específica
            **agent_config.get("config", {})
        )
        
        # Adicionar ferramentas ao agente
        agent_instance.set_tools(tools)
        
        return agent_instance
    
    def create_crew(self, crew_config, domain_name):
        """
        Cria uma crew a partir da configuração.
        
        Args:
            crew_config: Configuração da crew do YAML
            domain_name: Nome do domínio ativo
            
        Returns:
            Instância da crew
        """
        # Obter configurações do domínio
        domain_config = self.domain_manager.get_domain_config(domain_name)
        
        # Criar os agentes definidos no YAML
        agents = {}
        for agent_id in crew_config.get("agents", []):
            agent_config = domain_config["agents"].get(agent_id)
            if not agent_config:
                raise ValueError(f"Agente {agent_id} não encontrado na configuração")
                
            agents[agent_id] = self.create_agent(agent_id, agent_config, domain_name)
        
        # Criar as tasks a partir do workflow
        tasks = self._create_tasks_from_workflow(crew_config.get("workflow", []), agents)
        
        # Criar a crew
        crew_instance = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            name=crew_config.get("name", f"{domain_name}Crew"),
            description=crew_config.get("description", ""),
            verbose=crew_config.get("verbose", True),
            process=crew_config.get("process", "sequential")
        )
        
        return crew_instance
    
    def _create_tasks_from_workflow(self, workflow, agents):
        """
        Cria tarefas a partir da definição de workflow.
        
        Args:
            workflow: Lista de passos do workflow
            agents: Dicionário de agentes instanciados
            
        Returns:
            Lista de tarefas
        """
        tasks = []
        
        for step in workflow:
            step_name = step.get("step")
            agent_id = step.get("agent")
            
            if not agent_id in agents:
                raise ValueError(f"Agente {agent_id} referenciado no passo {step_name} não encontrado")
                
            agent = agents[agent_id]
            
            # Criar a tarefa
            task = Task(
                description=step.get("description", f"Execute o passo {step_name}"),
                agent=agent,
                expected_output=step.get("expected_output", "Resultado do processamento")
            )
            
            tasks.append(task)
            
        return tasks
```

### 3. Atualizar o HubCrew

O `HubCrew` precisa ser atualizado para utilizar o `CrewFactory`, `CrewRegistry` e o `DomainManager`:

- Modificar o método `process_message` para obter o domínio correto da conversa
- Utilizar o `CrewRegistry` para obter crews já instanciadas ou criar novas quando necessário
- Implementar método `determine_appropriate_crew` para identificar qual crew deve processar uma mensagem
- Integrar com o `AgentStateManager` para persistir e restaurar o estado dos agentes

### 4. Centralizar Acesso a Ferramentas

O `DataProxyAgent` deve se tornar o único ponto de acesso a ferramentas:

- Implementar um `ToolRegistry` gerenciado pelo `DataProxyAgent`
- Garantir que todas as ferramentas sejam registradas no início do sistema
- Adicionar controle de acesso baseado em configuração YAML

## Componentes a Serem Refatorados/Removidos

Após análise da estrutura atual, os seguintes componentes serão substituídos por configuração YAML ou precisarão ser refatorados:

### 1. Agentes Especializados Codificados

Os seguintes agentes terão suas configurações movidas para YAML:

- **`src/agents/specialized/sales_agent.py`**:
  - A classe permanecerá, mas suas configurações (role, goal, backstory) serão definidas em YAML
  - O construtor será atualizado para aceitar configurações dinâmicas

- **`src/agents/specialized/support_agent.py`**:
  - Mesmo tratamento que o SalesAgent

- **`src/agents/specialized/scheduling_agent.py`**:
  - Mesmo tratamento que o SalesAgent

### 2. Definições de Crews Codificadas

As seguintes definições de crews serão substituídas por configuração YAML:

- **`src/crews/sales_crew.py`**:
  - A configuração dos agentes e workflow será movida para YAML
  - O arquivo pode ser mantido apenas como referência

- **`src/crews/support_crew.py`**:
  - Mesmo tratamento que o SalesCrew

- **`src/crews/scheduling_crew.py`**:
  - Mesmo tratamento que o SalesCrew

### 3. Tarefas Hardcoded

As seguintes tarefas serão definidas em YAML como parte do workflow:

- **`src/tasks/sales_tasks.py`**:
  - As tarefas serão definidas como parte do workflow no YAML
  - O arquivo pode ser removido após a transição

- **`src/tasks/hub_tasks.py`**:
  - As tarefas do hub serão configuradas via YAML
  - O arquivo pode ser removido após a transição

- **`src/tasks/whatsapp_tasks.py`**:
  - As tarefas específicas de canal serão definidas via YAML
  - O arquivo pode ser removido após a transição

### 4. Implementações Duplicadas

Os seguintes arquivos podem conter implementações duplicadas e devem ser revisados:

- Qualquer implementação antiga do `AgentManager` (mencionado nas memórias)
- Arquivos de teste duplicados
- Implementações que acessam diretamente a camada de dados sem passar pelo `DataProxyAgent`

## Estratégia de Testes

Para garantir a transição segura para o novo sistema, seguiremos a seguinte estratégia de testes:

1. **Testes Unitários**:
   - Para `DomainLoader`, `CrewFactory` e `DomainManager`
   - Validação de configurações YAML
   - Carregamento dinâmico de classes

2. **Testes de Integração**:
   - Simulação de fluxo completo com diferentes domínios
   - Verificação de correto roteamento de mensagens
   - Validação de resposta adaptada ao domínio

3. **Testes de Regressão**:
   - Comparação de comportamento antes e depois da refatoração
   - Garantia de compatibilidade com sistemas existentes

## Cronograma Estimado

| Tarefa | Tempo Estimado | Prioridade |
|--------|----------------|------------|
| Melhorar DomainLoader | 2 dias | Alta |
| Implementar CrewFactory | 3 dias | Alta |
| Implementar sistema de persistência e cache | 3 dias | Alta |
| Atualizar HubCrew | 2 dias | Alta |
| Centralizar acesso a ferramentas | 2 dias | Alta |
| Criar testes unitários | 3 dias | Média |
| Validação de configurações | 2 dias | Média |
| Documentação e treinamento | 1 dia | Baixa |
| **Total** | **18 dias úteis** | |

## Próximos Passos Imediatos

1. **Implementar o sistema de persistência e cache** para garantir eficiência e reutilização
2. **Refinar o DomainLoader** para garantir validação completa de configurações
3. **Implementar o CrewFactory** e **CrewRegistry** para criação e persistência de componentes
4. **Atualizar o HubCrew** para usar o sistema dinâmico e persistente
5. **Simplificar acesso a dados** via DataProxyAgent
6. **Implementar o sistema multi-tenant** conforme descrito
