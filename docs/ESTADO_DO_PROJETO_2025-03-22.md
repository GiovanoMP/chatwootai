# Estado do Projeto ChatwootAI - 2025-03-22

## Visão Geral do Projeto

O ChatwootAI é um sistema avançado de atendimento ao cliente que integra o Chatwoot como hub central de comunicação com uma arquitetura de agentes inteligentes baseada em CrewAI. O sistema foi projetado para fornecer respostas adaptadas a diferentes domínios de negócio (cosméticos, saúde, varejo, etc.) através de configurações YAML, agentes especializados e um sistema de plugins.

### Componentes Principais

1. **Hub Central (hub.py)**
   - `HubCrew`: Orquestração principal do fluxo de mensagens
   - `OrchestratorAgent`: Roteamento inteligente de mensagens
   - `ContextManagerAgent`: Gestão de contexto das conversas
   - `IntegrationAgent`: Integrações com sistemas externos
   - `DataProxyAgent`: Ponto único de acesso a dados para todos os agentes

2. **Crews Especializadas**
   - `SalesCrew`: Processamento de consultas relacionadas a vendas e produtos
   - `SupportCrew`: Atendimento de suporte ao cliente
   - `MarketingCrew`: Gestão de campanhas e promoções

3. **Camada de Dados**
   - `DataServiceHub`: Coordenação central de todos os serviços de dados
   - `ProductDataService`: Acesso a dados de produtos
   - `CustomerDataService`: Acesso a dados de clientes
   - `ConversationContextService`: Gestão do contexto das conversas
   - `ConversationAnalyticsService`: Análise de conversas
   - `DomainRulesService`: Regras de negócio específicas por domínio

4. **Domínios de Negócio**
   - Configurações YAML por domínio em `/config/domains/{domínio}/`
   - Adaptação dinâmica via `DomainManager`

5. **Infraestrutura**
   - Redis: Cache e armazenamento temporário
   - PostgreSQL: Banco de dados relacional
   - Qdrant: Banco de dados vetorial para busca semântica (em Docker)
   - Chatwoot: Interface de comunicação com clientes

## Arquitetura do Sistema

O ChatwootAI segue uma arquitetura hub-and-spoke, onde o `HubCrew` atua como o hub central que coordena o fluxo de mensagens entre os diferentes componentes do sistema.

### Fluxo de Processamento de Mensagens

1. **Entrada da Mensagem**
   - Cliente envia mensagem via WhatsApp/Telegram/etc.
   - Chatwoot recebe a mensagem e a encaminha via webhook para o sistema

2. **Processamento pelo Hub Central**
   - `ChatwootWebhookHandler` recebe a mensagem e a encaminha para o `HubCrew`
   - `HubCrew` normaliza a mensagem e consulta o domínio ativo
   - `OrchestratorAgent` analisa a intenção da mensagem
   - `ContextManagerAgent` atualiza o contexto da conversa
   - `HubCrew` determina a crew especializada apropriada

3. **Processamento pela Crew Especializada**
   - A crew especializada (ex: `SalesCrew`) recebe a mensagem
   - O agente principal da crew (ex: `SalesAgent`) formula consultas adaptadas ao domínio
   - Todo acesso a dados é feito EXCLUSIVAMENTE via `DataProxyAgent`
   - `DataProxyAgent` encaminha consultas para o `DataServiceHub`
   - `DataServiceHub` coordena os serviços específicos (ex: `ProductDataService`)

4. **Retorno da Resposta**
   - A crew especializada formata a resposta conforme o domínio ativo
   - A resposta retorna para o `HubCrew`
   - `HubCrew` encaminha a resposta para o Chatwoot
   - Cliente recebe a resposta personalizada

### Princípios Arquiteturais Fundamentais

1. **Centralização do Acesso a Dados**
   - Todo acesso a dados DEVE ser feito via `DataProxyAgent` → `DataServiceHub`
   - Nenhum agente ou componente deve acessar diretamente os serviços de dados

2. **Adaptação Dinâmica por Domínio**
   - Configurações YAML determinam o comportamento por domínio
   - Agentes são configurados dinamicamente conforme o domínio ativo

3. **Memória Persistente**
   - Contexto das conversas e configurações são mantidos em memória persistente
   - Redis é utilizado para cache e armazenamento temporário

4. **Arquitetura Modular**
   - Componentes são desacoplados e se comunicam através de interfaces bem definidas
   - Plugins podem estender a funcionalidade do sistema

## Estado Atual do Desenvolvimento

### Funcionalidades Implementadas

1. **Estrutura Base do Sistema**
   - Arquitetura hub-and-spoke com `HubCrew` como orquestrador central
   - Integração com Chatwoot via webhook
   - Sistema de configuração por domínio via YAML

2. **Componentes Principais**
   - `HubCrew` com atributo `_role` para roteamento de mensagens
   - `DataProxyAgent` com método `fetch_data` para acesso centralizado a dados
   - `SalesAgent` adaptado para usar o `DataProxyAgent` corretamente
   - `DataServiceHub` com serviços básicos registrados

3. **Domínios de Negócio**
   - Domínio "cosmetics" configurado e funcional
   - Validação de configurações via Pydantic

4. **Infraestrutura**
   - Conexão com Redis para cache
   - Conexão com PostgreSQL para dados relacionais
   - Docker configurado para Qdrant (banco vetorial)

### Problemas Resolvidos Recentemente

1. **Erro no HubCrew**
   - Adicionado atributo `_role` à classe `HubCrew` para resolver o erro `'HubCrew' object has no attribute 'role'`

2. **Erro no DataProxyAgent**
   - Implementado o método `fetch_data` no `DataProxyAgent` para resolver o erro `'DataProxyAgent' object has no attribute 'fetch_data'`

3. **Erro no SalesAgent**
   - Corrigido o `SalesAgent` para usar o método `fetch_data` do `DataProxyAgent` em vez de `query_data`

4. **Erro na Configuração do Domínio**
   - Corrigido o campo `version` no domínio "cosmetics" de um número float (2.1) para uma string ("2.1") para resolver problemas de validação Pydantic

### Avisos e Problemas Pendentes

1. **Inicialização de Ferramentas do Domínio**
   - Aviso: `DomainManager não disponível, ferramentas não serão inicializadas`
   - O `DomainManager` precisa ser disponibilizado para o `DataProxyAgent`

2. **Serviço de Busca Vetorial**
   - Aviso: `Tentativa de acessar serviço não registrado: 'VectorSearchService'`
   - O `VectorSearchService` precisa ser implementado e registrado no `DataServiceHub`

3. **Referência a Crew Inexistente**
   - Aviso: `Crew 'general' não encontrada`
   - Referências à crew 'general' devem ser removidas ou ajustadas

## Próximos Passos

### 1. Implementar o VectorSearchService

O `VectorSearchService` é necessário para busca semântica em documentos e bases de conhecimento. O banco vetorial Qdrant já está configurado em Docker e pode ser acessado pelo `DataServiceHub`.

**Tarefas:**
- Criar a classe `VectorSearchService` em `src/services/data/vector_search_service.py`
- Implementar a conexão com o Qdrant
- Registrar o serviço no `DataServiceHub`
- Atualizar o `DataProxyAgent` para utilizar o serviço corretamente

**Exemplo de Implementação:**
```python
from src.services.data.base_data_service import BaseDataService
from qdrant_client import QdrantClient
from qdrant_client.http import models

class VectorSearchService(BaseDataService):
    """Serviço para busca semântica em documentos e bases de conhecimento."""
    
    def __init__(self, data_service_hub, config=None):
        super().__init__(data_service_hub, "VectorSearchService", config)
        self._connect_to_qdrant()
        
    def _connect_to_qdrant(self):
        """Conecta ao Qdrant."""
        try:
            self.client = QdrantClient(
                url=self.config.get("url", "http://localhost:6333"),
                api_key=self.config.get("api_key", "")
            )
            self.logger.info("Conexão com Qdrant estabelecida")
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao Qdrant: {str(e)}")
            
    def search(self, query_text, collection_name=None, limit=5):
        """Realiza busca semântica."""
        try:
            # Implementar a lógica de busca
            # ...
            return results
        except Exception as e:
            self.logger.error(f"Erro na busca vetorial: {str(e)}")
            return []
```

### 2. Corrigir Referências à Crew 'general'

A crew 'general' não existe e todas as referências a ela devem ser removidas ou ajustadas para usar crews existentes.

**Tarefas:**
- Identificar todas as referências à crew 'general' no código
- Remover ou ajustar essas referências para usar crews existentes
- Atualizar a lógica de roteamento no `HubCrew`

**Locais a verificar:**
- `src/core/hub.py`
- `src/webhook/webhook_handler.py`
- `scripts/test_message_manually.py`

### 3. Melhorar a Inicialização de Ferramentas do Domínio

O `DomainManager` precisa ser disponibilizado para o `DataProxyAgent` para que as ferramentas específicas do domínio possam ser inicializadas corretamente.

**Tarefas:**
- Garantir que o `DomainManager` seja passado corretamente para o `DataProxyAgent`
- Verificar a inicialização do `DomainManager` no `HubCrew`
- Corrigir o método `_initialize_tools` no `DataProxyAgent`

**Exemplo de Correção:**
```python
# Em src/core/hub.py
def __init__(self, ...):
    # ...
    self._data_proxy_agent = DataProxyAgent(
        data_service_hub=data_service_hub,
        memory_system=memory_system,
        domain_manager=domain_manager  # Garantir que este parâmetro seja passado
    )
```

### 4. Expandir os Testes

É necessário criar testes mais abrangentes para validar o fluxo completo de mensagens e testar diferentes tipos de consultas e domínios.

**Tarefas:**
- Criar testes unitários para os componentes principais
- Criar testes de integração para o fluxo completo de mensagens
- Testar diferentes tipos de consultas e domínios
- Implementar testes automatizados para CI/CD

**Exemplo de Teste:**
```python
# Em tests/integration/test_message_flow.py
def test_product_query_flow():
    """Testa o fluxo completo de uma consulta de produto."""
    # Configurar o ambiente de teste
    # ...
    
    # Simular uma mensagem do cliente
    message = {
        "content": "Você tem creme para as mãos?",
        "sender_id": "12345",
        "conversation_id": "67890",
        "channel_type": "whatsapp"
    }
    
    # Processar a mensagem
    result = webhook_handler.process_webhook({
        "event": "message_created",
        "message": message
    })
    
    # Verificar o resultado
    assert result["status"] == "success"
    assert "response" in result
    assert "creme para as mãos" in result["response"].lower()
```

## Guia de Desenvolvimento

### Estrutura do Projeto

```
/home/giovano/Projetos/Chatwoot V4/
├── config/
│   ├── domains/
│   │   ├── _base/
│   │   ├── cosmetics/
│   │   ├── health/
│   │   └── retail/
├── docs/
├── scripts/
├── src/
│   ├── agents/
│   │   └── specialized/
│   │       ├── sales_agent.py
│   │       └── ...
│   ├── api/
│   │   └── chatwoot/
│   ├── core/
│   │   ├── data_proxy_agent.py
│   │   ├── data_service_hub.py
│   │   ├── domain/
│   │   ├── hub.py
│   │   └── memory.py
│   ├── crews/
│   │   ├── sales_crew.py
│   │   └── ...
│   ├── plugins/
│   ├── services/
│   │   └── data/
│   │       ├── product_data_service.py
│   │       └── ...
│   ├── tools/
│   └── webhook/
├── tests/
│   ├── integration/
│   └── unit/
└── .env
```

### Fluxo de Desenvolvimento

1. **Entender a Arquitetura**
   - Revisar a documentação em `/docs/`
   - Estudar o fluxo de mensagens e a arquitetura hub-and-spoke
   - Entender o papel central do `DataProxyAgent` e do `DataServiceHub`

2. **Configurar o Ambiente**
   - Instalar dependências: `pip install -r requirements.txt`
   - Configurar variáveis de ambiente no arquivo `.env`
   - Iniciar os serviços Docker: `docker-compose up -d`

3. **Desenvolver Novos Recursos**
   - Seguir a arquitetura existente
   - Manter o acesso a dados centralizado via `DataProxyAgent`
   - Adaptar comportamentos por domínio via configurações YAML

4. **Testar Alterações**
   - Executar testes unitários: `pytest tests/unit/`
   - Executar testes de integração: `pytest tests/integration/`
   - Testar manualmente: `python scripts/test_message_manually.py`

5. **Documentar Alterações**
   - Atualizar a documentação em `/docs/`
   - Adicionar comentários ao código
   - Manter o histórico de alterações

### Boas Práticas

1. **Acesso a Dados**
   - Todo acesso a dados DEVE ser feito via `DataProxyAgent`
   - Nunca acessar diretamente os serviços de dados

2. **Configuração por Domínio**
   - Usar configurações YAML para comportamentos específicos por domínio
   - Manter a configuração base em `/config/domains/_base/`

3. **Tratamento de Erros**
   - Usar exceções específicas do domínio em `src/core/exceptions.py`
   - Logar erros com nível apropriado

4. **Testes**
   - Escrever testes unitários para novos componentes
   - Manter testes de integração atualizados

## Conclusão

O projeto ChatwootAI está em um estado funcional, com a arquitetura hub-and-spoke implementada e o fluxo de mensagens funcionando corretamente. Os próximos passos envolvem a implementação do `VectorSearchService`, a correção de referências à crew 'general', a melhoria da inicialização de ferramentas do domínio e a expansão dos testes.

A arquitetura modular e a centralização do acesso a dados via `DataProxyAgent` fornecem uma base sólida para o desenvolvimento futuro do sistema, permitindo a adaptação a diferentes domínios de negócio e a extensão via plugins.

---

Documento criado em: 2025-03-22
Última atualização: 2025-03-22
