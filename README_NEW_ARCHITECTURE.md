# Nova Arquitetura Chatwoot V4

Este documento explica as mudanças implementadas na nova arquitetura do Chatwoot V4, focando no `DomainLoader`, `DomainManager`, `ToolRegistry` e `DataProxyAgent`. Também fornece instruções para migração e testes.

## Visão Geral da Nova Arquitetura

A nova arquitetura foi projetada para resolver problemas identificados na versão anterior, principalmente relacionados a:

1. **Acesso inconsistente a dados** - Alguns agentes acessavam serviços diretamente em vez de usar o DataProxyAgent
2. **Duplicação de código** - Cada agente gerenciava suas próprias ferramentas
3. **Configurações espalhadas** - Não havia um local centralizado para configurações de domínio
4. **Tratamento de erros inconsistente** - Diferentes abordagens em diferentes componentes

### Principais Componentes Refatorados

#### 1. DomainLoader (src/core/domain/domain_loader_new.py)

Responsável por carregar configurações de domínio a partir de arquivos YAML:

- Suporte completo para herança de configurações entre domínios
- Validação rigorosa de configurações carregadas
- Cache eficiente para melhor performance

#### 2. DomainManager (src/core/domain/domain_manager_new.py)

Gerencia os domínios ativos e fornece acesso às configurações:

- Interface unificada para acessar configurações de domínio
- Gerenciamento do domínio ativo do sistema
- Acesso simplificado a configurações específicas via dotted notation

#### 3. ToolRegistry (src/core/tools/tool_registry.py)

Centraliza o gerenciamento de todas as ferramentas do sistema:

- Registro, instanciação e gerenciamento de ferramentas
- Carregamento dinâmico de classes de ferramentas
- Compartilhamento de instâncias para economia de recursos

#### 4. DataProxyAgent (src/core/data_proxy_agent_new.py)

O ponto central de acesso a dados no sistema:

- Único ponto de acesso para consultas de dados
- Usa o ToolRegistry para acessar ferramentas necessárias
- Adapta consultas com base no domínio ativo
- Fornece estatísticas e monitoramento de acessos a dados

## Benefícios da Nova Arquitetura

1. **Simplificação dos Agentes**
   - Agentes mais enxutos e focados apenas na sua especialidade
   - Redução de código duplicado
   - Melhor testabilidade

2. **Configurações Centralizadas**
   - Toda configuração de domínio em um único local (arquivos YAML)
   - Herança para evitar duplicação entre domínios relacionados
   - Validação automatizada de configurações

3. **Melhor Gerenciamento de Ferramentas**
   - Carregamento dinâmico de ferramentas conforme necessário
   - Compartilhamento de instâncias para economia de recursos
   - Ferramentas específicas por domínio

4. **Acesso a Dados Consistente**
   - Todas as consultas passam pelo DataProxyAgent
   - Tratamento de erros padronizado
   - Estatísticas e monitoramento centralizados

## Como Usar os Novos Componentes

### DomainManager

```python
from src.core.domain.domain_manager_new import DomainManager

# Inicializa o gerenciador
domain_manager = DomainManager()

# Define o domínio ativo
domain_manager.set_active_domain("cosmetics")

# Obtém uma configuração específica
max_products = domain_manager.get_active_domain_setting("settings.product_list.max_items", default=10)
```

### ToolRegistry

```python
from src.core.tools.tool_registry import ToolRegistry

# Inicializa o registro
tool_registry = ToolRegistry()

# Registra uma ferramenta
tool_registry.register_tool("product_search", {
    "type": "search",
    "class": "src.tools.search.ProductSearchTool",
    "config": {
        "name": "product_search",
        "description": "Busca produtos no catálogo"
    }
})

# Obtém uma instância da ferramenta
product_search_tool = tool_registry.get_tool_instance("product_search")

# Obtém todas as ferramentas de um determinado tipo
all_search_tools = tool_registry.get_tool_instances_by_type("search")
```

### DataProxyAgent

```python
from src.core.data_proxy_agent_new import DataProxyAgent
from src.core.tools.tool_registry import ToolRegistry
from src.core.domain.domain_manager_new import DomainManager

# Inicializa os componentes necessários
tool_registry = ToolRegistry()
domain_manager = DomainManager()

# Inicializa o DataProxyAgent
data_proxy = DataProxyAgent(
    tool_registry=tool_registry,
    domain_manager=domain_manager
)

# Consulta dados de produtos
products = data_proxy.query_product_data(
    query_text="produtos para pele seca",
    filters={"category": "skincare"},
    domain="cosmetics"  # Opcional, usa o domínio ativo se não fornecido
)

# Obtém ferramentas para um agente específico
agent_tools = data_proxy.get_tools_for_agent("sales")
```

## Adaptando Agentes Existentes

A nova arquitetura exige que os agentes acessem dados exclusivamente através do DataProxyAgent. Para facilitar a transição, criamos um script de migração que adapta agentes existentes.

### Script de Migração

O script `scripts/migrate_to_new_architecture.py` fornece várias ferramentas para migração:

1. **Migrar Configurações de Domínio**
   ```bash
   python scripts/migrate_to_new_architecture.py --migrate-domain cosmetics
   ```

2. **Verificar Compatibilidade de Ferramentas**
   ```bash
   python scripts/migrate_to_new_architecture.py --check-compatibility
   ```

3. **Adaptar um Agente**
   ```bash
   python scripts/migrate_to_new_architecture.py --adapt-agent sales
   ```

O script cria backups automáticos antes de fazer qualquer modificação, garantindo que você possa reverter se necessário.

## Testando os Novos Componentes

Implementamos testes unitários abrangentes para todos os componentes:

- `tests/unit/core/domain/test_domain_loader.py`
- `tests/unit/core/domain/test_domain_manager.py`
- `tests/unit/core/tools/test_tool_registry.py`
- `tests/unit/core/test_data_proxy_agent.py`

Execute os testes com:

```bash
python -m pytest tests/unit/core/
```

## Próximos Passos

1. **Refatorar Agentes Restantes**
   - Adaptar todos os agentes para usar exclusivamente o DataProxyAgent

2. **Migrar Configurações**
   - Converter todas as configurações de domínio para o novo formato

3. **Testes de Integração**
   - Verificar se todos os componentes funcionam juntos corretamente

4. **Atualizar Documentação**
   - Documentar completamente a nova arquitetura e padrões de uso

## Conclusão

A nova arquitetura representa uma melhoria significativa na organização, manutenção e extensibilidade do Chatwoot V4. Ao centralizar o acesso a dados através do DataProxyAgent e gerenciar melhor as configurações de domínio e ferramentas, criamos um sistema mais robusto e adaptável a diferentes contextos de negócio.
