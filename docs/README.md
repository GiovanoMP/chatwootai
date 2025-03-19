# ChatwootAI: Sistema Multiagente Inteligente

## Visão Geral

O ChatwootAI é uma plataforma modular que integra múltiplas tecnologias para criar um sistema de atendimento inteligente adaptável a diversos domínios de negócio. Esta documentação detalha a arquitetura, componentes, e caminhos de implementação do sistema.

## Componentes Principais

### 1. Hub de Comunicação: Chatwoot

O Chatwoot atua como hub central de comunicação, integrando múltiplos canais:
- WhatsApp
- Instagram
- Facebook Messenger
- Telegram
- Email
- Chat Web

### 2. Orquestração de Agentes: CrewAI

A CrewAI permite a criação e gerenciamento de agentes inteligentes organizados em equipes (crews) especializadas:
- **Channel Crews**: Integração com canais específicos
- **Hub Crew**: Orquestração central e roteamento de mensagens
- **Functional Crews**: Especialização em domínios de negócio (Vendas, Suporte, etc.)

### 3. Banco de Dados Vetorial: Qdrant

O Qdrant armazena embeddings para busca semântica de:
- Produtos
- Regras de negócio
- Histórico de conversas
- FAQs e documentação

### 4. Cache e Estado: Redis

O Redis implementa:
- Sistema de cache em dois níveis (L1/L2)
- Armazenamento de estado de conversas
- Publicação/assinatura para comunicação assíncrona

### 5. Regras de Negócio: Simulação de Odoo

Uma simulação do Odoo (ou outro ERP) gerencia regras de negócio para:
- Catálogo de produtos
- Regras de preços e descontos
- Políticas de entrega
- Base de conhecimento para suporte
- Agendamentos e disponibilidade

## Arquitetura do Sistema

O sistema utiliza uma arquitetura Hub-and-Spoke com camadas hierárquicas:

1. **Camada de Entrada** (Channel Crews)
   - Processamento de mensagens de diferentes canais
   - Normalização para o formato padrão interno
   
2. **Camada de Hub Central** (Hub Crew)
   - Análise de intenções e roteamento
   - Gerenciamento de contexto
   - Proxy para acesso a dados

3. **Camada de Processamento** (Functional Crews)
   - **SalesCrew**: Processamento de vendas e recomendações
   - **DeliveryCrew**: Gerenciamento de entregas e logística
   - **SupportCrew**: Atendimento de suporte e resolução de problemas
   - **InfoCrew**: Fornecimento de informações gerais e FAQs
   - **SchedulingCrew**: Gerenciamento de agendamentos e compromissos

4. **Camada de Data Services** (Nova)
   - Interface unificada para serviços de dados
   - Abstração de operações de banco de dados
   - Sistema de eventos para comunicação assíncrona

5. **Camada de Integração**
   - Conectores para Odoo (ou outro ERP)
   - Webhooks para sistemas externos
   - APIs para extensibilidade

## Módulos e Serviços

### Módulos do Odoo Suportados

1. **Vendas (Sales)**
   - Gerenciamento de produtos e preços
   - Processamento de pedidos
   - Campanhas e promoções

2. **Delivery**
   - Opções de entrega
   - Rastreamento
   - Cálculo de custos de envio

3. **Suporte (Helpdesk)**
   - Tickets e casos
   - Base de conhecimento
   - SLAs e métricas

4. **Informações (Knowledge)**
   - FAQs
   - Documentação
   - Políticas e termos

5. **Agendamento (Appointment)**
   - Calendários de disponibilidade
   - Reservas e confirmações
   - Lembretes e notificações

### Serviços de Dados

1. **ProductDataService**: Busca híbrida de produtos
2. **CustomerDataService**: Gerenciamento de dados de clientes
3. **ConversationContextService**: Contexto de conversas
4. **DomainRulesService**: Regras de negócio específicas do domínio
5. **SalesDataService**: Dados específicos para vendas
6. **DeliveryDataService**: Dados para entregas
7. **SupportDataService**: Dados para suporte
8. **InfoDataService**: Dados informativos
9. **SchedulingDataService**: Dados para agendamentos

## Características Avançadas

### 1. Processamento Hierárquico

- Agente gerente coordena o fluxo de trabalho
- Delegação eficiente de tarefas
- Validação de resultados

### 2. Busca Híbrida Otimizada

- Combinação de busca semântica (vetorial) e estruturada (SQL)
- Filtros e facets para refinamento
- Caching inteligente com invalidação baseada em eventos

### 3. Arquitetura Orientada a Eventos

- Comunicação assíncrona entre componentes
- Redução de acoplamento
- Melhor escalabilidade

### 4. Sistema de Cache em Dois Níveis

- L1: Cache local em memória
- L2: Cache distribuído via Redis
- Políticas de TTL adaptativas

### 5. Personalização Contextual Avançada

- **Memória de Longa Duração**: Armazenamento persistente de preferências e histórico do cliente
- **Análise de Intenções Cruzadas**: Identificação de oportunidades baseadas no contexto conversacional
- **Recomendações Proativas**: Sugestões inteligentes baseadas na análise do histórico e contexto atual
- **Transições Suaves de Contexto**: Capacidade de manter o contexto entre diferentes domínios funcionais
- **Exemplos Práticos**:
  - "Já que você está interessado em proteção solar, pode querer agendar uma consulta de avaliação dermatológica"
  - "Notei que você costuma comprar produtos para pele sensível. Este novo lançamento foi formulado especificamente para seu tipo de pele"
  - "Com base no seu histórico de agendamentos, seria um bom momento para marcar sua revisão trimestral"

### 6. Análise de Histórico e Perfil Enriquecido de Cliente

- **Extração de Pontos-Chave**: Armazenamento inteligente apenas dos pontos principais das conversas para análises futuras
- **Perfil Completo do Cliente**: Construção de um perfil detalhado incluindo preferências, comportamentos e dados relevantes
- **Saudações Personalizadas**: Capacidade de chamar o cliente pelo nome e referir-se a interações anteriores
- **Memória de Endereços**: Armazenamento de endereços de entrega com possibilidade de reutilização
- **Análise de Tendências**: Identificação de padrões e comportamentos para aprimoramento de produtos e serviços
- **Exemplos Práticos**:
  - "Olá, [Nome]! Que bom ver você novamente. Deseja usar o mesmo endereço da última entrega?"
  - "Baseado na análise das últimas 1000 conversas, identificamos que 78% dos clientes estão interessados em proteção solar no verão"
  - "Seu histórico mostra interesse em produtos naturais - gostaria de conhecer nossa nova linha eco-friendly?"

## Adaptabilidade a Domínios de Negócio

O sistema é adaptável a diferentes modelos de negócio B2C através de:

1. **Sistema de Domínios de Negócio**
   - Arquivos YAML de configuração
   - Regras específicas do domínio
   - Fluxos de conversação personalizados

2. **Agentes Adaptáveis**
   - Ajustam comportamento com base no domínio
   - Prompts específicos do contexto
   - Conhecimento especializado

3. **Sistema de Plugins**
   - Extensões para funcionalidades específicas
   - Interface padronizada
   - Carregamento dinâmico

4. **Abstração de ERP**
   - Camada de adaptação para diferentes ERPs
   - Mapeamento de entidades
   - Conversores de formato

## Implementação e Próximos Passos

Consulte o documento [ARQUITETURA_DATA_SERVICES_OTIMIZADA.md](./ARQUITETURA_DATA_SERVICES_OTIMIZADA.md) para detalhes sobre a implementação da nova camada de Data Services e os próximos passos do projeto.
