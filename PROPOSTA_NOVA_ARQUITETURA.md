# Proposta de Nova Arquitetura: Sistema Modular com Microsserviços

## 1. Visão Geral

Esta proposta apresenta uma evolução arquitetural do sistema ChatwootAI para uma abordagem baseada em microsserviços, visando maior escalabilidade, manutenibilidade e desempenho. A arquitetura proposta mantém a flexibilidade necessária para um desenvolvedor solo enquanto prepara o terreno para crescimento futuro.

## 2. Arquitetura Proposta

### 2.1. Diagrama de Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Sistema de IA  │◄───►│  Config Service │◄───►│  Config Viewer  │
│  (ChatwootAI)   │     │  (Microserviço) │     │  (Microserviço) │
│                 │     │                 │     │                 │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  MCP-Odoo       │◄───►│  Odoo ERP       │     │  Odoo API       │
│  (Microserviço) │     │  (Módulos AI)   │◄───►│  (Microserviço) │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  Qdrant         │
                                                │  (Vector DB)    │
                                                │                 │
                                                └─────────────────┘
```

### 2.2. Componentes Principais

1. **Sistema de IA (ChatwootAI)**: Sistema principal que processa mensagens do Chatwoot e coordena as crews especializadas.

2. **Config Service**: Microsserviço responsável pelo armazenamento e gerenciamento de configurações e mapeamentos.

3. **Config Viewer**: Interface web para visualização e gerenciamento de configurações.

4. **MCP-Odoo**: Microsserviço que encapsula a lógica de comunicação com o Odoo através do protocolo MCP.

5. **Odoo API**: Microsserviço responsável pela vetorização de dados do Odoo para o Qdrant.

6. **Odoo ERP**: Sistema ERP com módulos AI para configuração e gerenciamento.

7. **Qdrant**: Banco de dados vetorial para armazenamento e busca de embeddings.

## 3. Fluxo de Processamento de Mensagens

### 3.1. Fluxo Completo

```
[Chatwoot] → [Webhook Handler] → [Config Cache] → [Hub] → [Crew Factory] → [Canal-Specific Crew]
                                                                              ├─→ [Intent Agent]
                                                                              ├─→ [Business Rules Agent]
                                                                              ├─→ [Support Docs Agent]
                                                                              ├─→ [Product Info Agent]
                                                                              ├─→ [MCP Agent]
                                                                              └─→ [Response Agent]
```

### 3.2. Detalhamento do Fluxo

1. **Recebimento do Webhook**: O Webhook Handler recebe a mensagem do Chatwoot.

2. **Identificação do Tenant**: O handler consulta o Config Cache para identificar o tenant com base no account_id e inbox_id.

3. **Obtenção de Configurações**: O Config Cache fornece as configurações e credenciais do tenant.

4. **Direcionamento para o Hub**: O Hub determina qual crew deve processar a mensagem com base no canal.

5. **Criação da Crew**: A Crew Factory cria a crew apropriada com os agentes necessários.

6. **Processamento pela Crew**: A crew processa a mensagem usando seus agentes especializados.

7. **Resposta ao Cliente**: A resposta é enviada de volta ao Chatwoot.

## 4. Implementação do Config Cache

### 4.1. Estrutura do Cache

O Config Cache é um componente crítico que mantém em memória:
- Mapeamento de contas Chatwoot para tenants
- Configurações de cada tenant
- Credenciais de cada tenant

### 4.2. Mecanismo de Invalidação por Evento

Quando uma configuração é alterada no Config Service, o cache é invalidado e atualizado imediatamente:

1. Config Service envia notificação de alteração
2. Sistema principal recebe a notificação
3. Cache específico é invalidado
4. Nova versão é buscada imediatamente

### 4.3. Fallback para Arquivos Locais

Em caso de falha na comunicação com o Config Service, o sistema usa fallback para arquivos locais:

1. Tenta obter do cache em memória
2. Se não encontrar, tenta obter do Config Service
3. Se falhar, usa arquivos locais como fallback

## 5. Crews Especializadas

### 5.1. Estrutura das Crews

Cada crew é especializada em um canal específico (WhatsApp, Instagram, etc.) e contém agentes especializados:

- **Intention Agent**: Identifica a intenção do cliente
- **Business Rules Agent**: Consulta regras de negócio
- **Support Documents Agent**: Busca documentos de suporte
- **Product Info Agent**: Consulta informações de produtos
- **MCP Agent**: Executa ações no Odoo
- **Response Agent**: Gera a resposta final

### 5.2. Criação Dinâmica de Agentes

Os agentes são criados dinamicamente com base nas coleções habilitadas para o tenant:

```python
def _initialize_agents(self):
    agents = {}
    
    # Agente de intenção (sempre presente)
    agents["intention"] = create_intention_agent(self.config)
    
    # Agentes de coleções vetoriais (criados apenas se a coleção estiver habilitada)
    if "business_rules" in self.enabled_collections:
        agents["business_rules"] = create_business_rules_agent(
            self.config,
            tools=[self.tools["business_rules"], self.tools["redis_cache"]]
        )
    
    # ... outros agentes
    
    return agents
```

### 5.3. Processamento Paralelo

As tarefas são executadas em paralelo para reduzir o tempo total de processamento:

```python
async def process_tasks(self, inputs):
    # Criar tarefas assíncronas
    tasks = []
    for task_name in self.parallel_tasks:
        tasks.append(self.execute_task_with_timeout(task_name, inputs))
    
    # Executar tarefas em paralelo
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Processar resultados
    processed_results = {}
    for task_name, result in zip(self.parallel_tasks, results):
        if isinstance(result, Exception):
            processed_results[task_name] = self._task_fallback(task_name, inputs)
        else:
            processed_results[task_name] = result
    
    return processed_results
```

## 6. Microsserviços Propostos

### 6.1. Config Service

**Responsabilidades**:
- Armazenar configurações e mapeamentos em PostgreSQL
- Fornecer API REST para acesso às configurações
- Gerenciar versionamento de configurações
- Notificar alterações para invalidação de cache

**Endpoints Principais**:
- `/configs/{tenant_id}/{domain}/{config_type}`: Obter/atualizar configuração
- `/mapping`: Obter/atualizar mapeamento de contas
- `/odoo-webhook`: Receber atualizações do Odoo

### 6.2. MCP-Odoo

**Responsabilidades**:
- Encapsular a comunicação com o Odoo via XML-RPC
- Fornecer API REST para operações no Odoo
- Gerenciar pool de conexões com o Odoo
- Implementar cache para operações frequentes

**Endpoints Principais**:
- `/products`: Operações relacionadas a produtos
- `/orders`: Operações relacionadas a pedidos
- `/customers`: Operações relacionadas a clientes

### 6.3. Odoo API (Vetorização)

**Responsabilidades**:
- Receber dados dos módulos do Odoo
- Vetorizar dados para o Qdrant
- Gerenciar coleções no Qdrant
- Fornecer API para busca vetorial

**Endpoints Principais**:
- `/vectorize`: Vetorizar dados para o Qdrant
- `/search`: Buscar dados vetorizados
- `/collections`: Gerenciar coleções

## 7. Vantagens da Nova Arquitetura

### 7.1. Desempenho Significativamente Melhorado

- **Cache em Memória**: Acesso quase instantâneo às configurações (100.000x mais rápido que disco)
- **Processamento Paralelo**: Execução simultânea de agentes especializados
- **Consultas Otimizadas**: Indexação para acesso direto O(1) em vez de busca linear O(n)
- **Redução de Parsing**: Parsing de YAML/JSON apenas uma vez durante atualização do cache
- **Pré-processamento de Dados**: Transformação de dados uma única vez
- **Redução de I/O**: Minimização de operações de leitura/escrita em disco
- **Melhor Localidade de Referência**: Dados relacionados agrupados em estruturas contíguas

### 7.2. Escalabilidade e Manutenibilidade

- **Separação de Responsabilidades**: Cada componente tem uma função clara e específica
- **Escalabilidade Independente**: Cada microsserviço pode escalar conforme necessário
- **Evolução Tecnológica**: Cada componente pode evoluir independentemente
- **Testabilidade**: Componentes isolados são mais fáceis de testar
- **Resiliência**: Falhas em um componente não afetam todo o sistema

### 7.3. Preparação para o Futuro

- **Arquitetura Extensível**: Facilidade para adicionar novos microsserviços
- **Suporte a Equipes**: Preparado para crescimento da equipe de desenvolvimento
- **Containerização**: Pronto para implantação em Docker e Kubernetes
- **Observabilidade**: Estrutura preparada para monitoramento avançado
- **Integração Contínua**: Facilita a implementação de CI/CD

## 8. Implementação para Desenvolvedor Solo

### 8.1. Abordagem Incremental

1. **Fase 1**: Implementar Config Service e Config Viewer
2. **Fase 2**: Implementar cache com invalidação no sistema principal
3. **Fase 3**: Extrair MCP-Odoo como microsserviço
4. **Fase 4**: Implementar Odoo API para vetorização
5. **Fase 5**: Migrar para containerização com Docker Compose

### 8.2. Controle de Complexidade

- **Cache Robusto**: Implementação simples mas eficaz de cache com invalidação
- **Fallback Local**: Garantia de funcionamento mesmo sem microsserviços
- **Documentação Clara**: Cada componente bem documentado
- **Scripts de Automação**: Simplificação de tarefas repetitivas
- **Monitoramento Básico**: Logs estruturados e métricas essenciais

## 9. Próximos Passos

1. Implementar o webhook do Odoo no Config Service
2. Desenvolver o mecanismo de cache com invalidação
3. Refatorar o webhook handler para usar o cache
4. Implementar o MCP-Odoo como microsserviço interno
5. Desenvolver o Odoo API para vetorização

## 10. Conclusão

A arquitetura proposta equilibra a necessidade de escalabilidade futura com a realidade de um desenvolvedor solo, oferecendo ganhos significativos de desempenho e manutenibilidade sem adicionar complexidade excessiva. A abordagem incremental permite evolução gradual do sistema, preparando o terreno para crescimento futuro.
