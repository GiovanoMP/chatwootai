# Arquitetura de Integração Odoo-MCP-Vetorização

Este documento descreve a arquitetura de integração entre o módulo Odoo de Descrições Inteligentes de Produtos, o MCP-Odoo e o serviço de vetorização, seguindo as melhores práticas da indústria.

## Visão Geral da Arquitetura

```
┌─────────────┐     ┌───────────────┐     ┌───────────────┐     ┌─────────────┐
│             │     │               │     │               │     │             │
│  Cliente    │────►│   Webhook     │────►│     Hub       │────►│    Crew     │
│  (Chatwoot) │     │   Handler     │     │               │     │             │
│             │     │               │     │               │     │             │
└─────────────┘     └───────────────┘     └───────────────┘     └──────┬──────┘
                                                                       │
┌─────────────┐     ┌───────────────┐                                  │
│             │     │               │                                  │
│  Módulo     │────►│   API REST    │──────────────────────────────────┘
│  Odoo       │     │               │
│             │     │               │
└─────────────┘     └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐     ┌─────────────┐
                    │               │     │             │
                    │   MCP-Odoo    │◄───►│    Odoo     │
                    │               │     │             │
                    └───────┬───────┘     └─────────────┘
                            │
                            ▼
                    ┌───────────────┐     ┌─────────────┐
                    │               │     │             │
                    │   Serviço de  │◄───►│   Qdrant    │
                    │  Vetorização  │     │             │
                    │               │     │             │
                    └───────────────┘     └─────────────┘
```

## Princípios da Arquitetura

1. **Separação de Responsabilidades**:
   - **Webhook Handler**: Processa requisições de clientes externos (Chatwoot)
   - **API REST**: Processa requisições do módulo Odoo
   - **Hub**: Identifica o account_id/domínio e direciona para a crew apropriada
   - **Crew**: Orquestra agentes para executar tarefas específicas
   - **MCP-Odoo**: Fornece interface padronizada para o Odoo
   - **Serviço de Vetorização**: Gerencia embeddings e busca semântica

2. **Identificação de Tenant**:
   - Toda requisição deve incluir ou permitir a identificação do account_id
   - O Hub é responsável por validar e mapear o account_id para o domínio correto
   - Configurações específicas são carregadas do YAML correspondente

3. **Comunicação Padronizada**:
   - MCP-Odoo fornece uma interface padronizada para o Odoo
   - Serviço de Vetorização fornece uma interface padronizada para o Qdrant
   - APIs REST seguem padrões consistentes

## Componentes Principais

### 1. Webhook Handler

**Responsabilidade**: Processar requisições de clientes externos (Chatwoot)

**Funcionalidades**:
- Receber webhooks do Chatwoot
- Extrair metadados (account_id, conversation_id, etc.)
- Direcionar para o Hub para processamento

### 2. API REST para Odoo

**Responsabilidade**: Processar requisições do módulo Odoo

**Funcionalidades**:
- Receber requisições do módulo Odoo
- Extrair metadados (account_id, action, etc.)
- Direcionar para o Hub para processamento

### 3. Hub

**Responsabilidade**: Identificar o account_id/domínio e direcionar para a crew apropriada

**Funcionalidades**:
- Validar o account_id contra os YAMLs existentes
- Carregar configurações específicas do account_id
- Obter ou criar a crew apropriada
- Direcionar a requisição para processamento

### 4. Crew

**Responsabilidade**: Orquestrar agentes para executar tarefas específicas

**Funcionalidades**:
- Gerenciar agentes específicos para o account_id
- Executar tarefas como geração de descrição, sincronização, etc.
- Utilizar o MCP-Odoo para comunicação com o Odoo

### 5. MCP-Odoo

**Responsabilidade**: Fornecer interface padronizada para o Odoo

**Funcionalidades**:
- Expor métodos para consultar produtos, clientes, vendas, etc.
- Implementar operações de negócio específicas do Odoo
- Abstrair a complexidade do Odoo para os agentes de IA

### 6. Serviço de Vetorização

**Responsabilidade**: Gerenciar embeddings e busca semântica

**Funcionalidades**:
- Gerar embeddings para descrições de produtos
- Armazenar embeddings no Qdrant
- Fornecer busca semântica

## Fluxos de Trabalho

### 1. Geração de Descrição de Produto

1. Módulo Odoo envia requisição para a API REST:
   ```json
   {
     "account_id": "account_2",
     "action": "generate_description",
     "product_id": 123
   }
   ```

2. API REST direciona para o Hub, que:
   - Valida o account_id
   - Carrega a configuração do YAML
   - Obtém ou cria a crew apropriada

3. Hub direciona para a crew, que:
   - Usa o agente de geração de conteúdo para gerar a descrição
   - Utiliza o MCP-Odoo para obter metadados do produto

4. MCP-Odoo:
   - Consulta o Odoo para obter metadados do produto
   - Retorna os metadados para o agente

5. Agente de geração de conteúdo:
   - Gera a descrição com base nos metadados
   - Retorna a descrição para a crew

6. Crew retorna a descrição para o Hub, que retorna para a API REST, que retorna para o módulo Odoo

### 2. Sincronização de Produto com Qdrant

1. Módulo Odoo envia requisição para a API REST:
   ```json
   {
     "account_id": "account_2",
     "action": "sync_product",
     "product_id": 123,
     "description": "Descrição do produto..."
   }
   ```

2. API REST direciona para o Hub, que:
   - Valida o account_id
   - Carrega a configuração do YAML
   - Obtém ou cria a crew apropriada

3. Hub direciona para a crew, que:
   - Usa o agente de sincronização para sincronizar o produto
   - Utiliza o serviço de vetorização para gerar embeddings e armazenar no Qdrant

4. Serviço de Vetorização:
   - Gera embeddings para a descrição
   - Armazena no Qdrant com metadados apropriados
   - Retorna o ID do vetor

5. Crew retorna o ID do vetor para o Hub, que retorna para a API REST, que retorna para o módulo Odoo

## Próximos Passos

### 1. Implementação da API REST para Odoo

- [ ] Criar estrutura básica da API REST
- [ ] Implementar endpoints para geração de descrição
- [ ] Implementar endpoints para sincronização com Qdrant
- [ ] Implementar endpoints para busca semântica
- [ ] Adicionar autenticação e autorização
- [ ] Implementar logging e monitoramento

### 2. Expansão do MCP-Odoo

- [ ] Adicionar métodos para obter metadados de produtos
- [ ] Adicionar métodos para atualizar status de sincronização
- [ ] Adicionar métodos para operações de vendas
- [ ] Adicionar métodos para operações de calendário
- [ ] Implementar cache para consultas frequentes
- [ ] Otimizar consultas ao Odoo

### 3. Implementação do Serviço de Vetorização

- [ ] Criar estrutura básica do serviço
- [ ] Implementar geração de embeddings
- [ ] Implementar armazenamento no Qdrant
- [ ] Implementar busca semântica
- [ ] Adicionar cache com Redis
- [ ] Implementar busca híbrida (vetorial + filtros)

### 4. Modificação do Hub

- [ ] Estender o Hub para processar diferentes tipos de requisições
- [ ] Implementar mecanismo para carregar configurações específicas do account_id
- [ ] Implementar mecanismo para obter ou criar a crew apropriada
- [ ] Adicionar suporte para diferentes tipos de ações

### 5. Testes e Documentação

- [ ] Implementar testes unitários para cada componente
- [ ] Implementar testes de integração para fluxos completos
- [ ] Implementar testes de carga para verificar desempenho
- [ ] Criar documentação detalhada para cada componente
- [ ] Criar guias de uso para desenvolvedores

## Considerações Futuras

### 1. Integração com Mercado Livre

- Adicionar adaptador específico para Mercado Livre
- Implementar sincronização de produtos com Mercado Livre
- Implementar processamento de pedidos do Mercado Livre

### 2. Integração com Instagram/Facebook

- Adicionar adaptador específico para Instagram/Facebook
- Implementar geração de conteúdo para Instagram/Facebook
- Implementar processamento de interações do Instagram/Facebook

### 3. Escalabilidade

- Implementar sistema de filas para processamento assíncrono
- Adicionar suporte para múltiplas instâncias de cada componente
- Implementar balanceamento de carga

### 4. Monitoramento e Observabilidade

- Implementar métricas de desempenho
- Implementar rastreamento de requisições
- Implementar alertas para falhas

## Conclusão

Esta arquitetura fornece uma base sólida para a integração entre o módulo Odoo, o MCP-Odoo e o serviço de vetorização, seguindo as melhores práticas da indústria. Ela é escalável, flexível e mantém a separação de responsabilidades, permitindo a adição de novos componentes e funcionalidades no futuro.

A implementação desta arquitetura permitirá a geração de descrições de produtos com IA, a sincronização com o banco de dados vetorial e a busca semântica usando linguagem natural, tudo isso mantendo a consistência e a escalabilidade do sistema.
