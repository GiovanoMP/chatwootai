# ChatwootAI: Metadados e Análise de Dados

## Visão Geral

O ChatwootAI é um sistema avançado de atendimento ao cliente que integra o Chatwoot como hub central de mensagens com uma arquitetura baseada em CrewAI para orquestração de agentes inteligentes. Este documento descreve como o sistema coleta e utiliza metadados para análises futuras.

## Nova Arquitetura

A nova arquitetura do ChatwootAI foi projetada para ser mais eficiente, escalável e adaptável a diferentes domínios de negócio:

1. **Simplificação do Fluxo**: Direcionamento direto para crews específicas com base na origem da mensagem
2. **Processamento Paralelo**: Agentes dentro de cada crew trabalham em paralelo para reduzir latência
3. **Configuração via YAML**: Dois arquivos YAML (config.yaml e credentials.yaml) para cada account_id
4. **Mapeamento Centralizado**: Mapeamento de canais do Chatwoot para account_id interno e domínio

## Implementação do Mapeamento de Canais

Recentemente implementamos um sistema de mapeamento de canais que permite:

1. **Mapear Canais do Chatwoot**: Associar account_id e inbox_id do Chatwoot a um account_id interno e domínio
2. **Configurar Fallbacks**: Definir mapeamentos de fallback para quando nenhum mapeamento específico for encontrado
3. **Números Especiais**: Configurar números de WhatsApp especiais que serão direcionados para a crew analytics
4. **Sincronização Automática**: Sincronizar mapeamentos com o sistema de IA via webhook

### Componentes Implementados

1. **Modelo `ai.channel.mapping`**: Extensão do módulo `ai_credentials_manager` para gerenciar mapeamentos
2. **Interface no Odoo**: Views para criar, editar e sincronizar mapeamentos
3. **Processamento de Eventos**: Manipulador de eventos de mapeamento no webhook_handler
4. **Arquivo de Mapeamento**: Atualização automática do arquivo `chatwoot_mapping.yaml`

## Coleta e Armazenamento de Metadados

O sistema coleta e armazena diversos metadados valiosos durante o processamento de mensagens:

### Metadados do Chatwoot

- **Conversas**: IDs, timestamps, duração, status
- **Contatos**: Nomes, números de telefone, emails, histórico de interações
- **Mensagens**: Conteúdo, tipo, timestamp, anexos
- **Canais**: Tipo de canal (WhatsApp, Instagram, etc.), inbox_id, account_id

### Metadados de Processamento

- **Intenções**: Intenções identificadas pelos agentes
- **Entidades**: Entidades extraídas das mensagens (produtos, datas, valores, etc.)
- **Confiança**: Níveis de confiança das classificações e extrações
- **Desempenho**: Tempo de processamento, latência, uso de recursos
- **Roteamento**: Crews e agentes envolvidos no processamento

### Metadados de Negócio

- **Domínio**: Área de negócio (retail, healthcare, etc.)
- **Account**: Identificador interno da conta
- **Regras**: Regras de negócio aplicadas durante o processamento
- **Produtos**: Produtos/serviços mencionados ou consultados
- **Ações**: Ações realizadas pelos agentes (consultas, agendamentos, etc.)

## Possibilidades de Análise de Dados

Os metadados coletados abrem diversas possibilidades para análises futuras:

### 1. Análise de Desempenho

- **Métricas de Atendimento**: Tempo médio de resposta, taxa de resolução, satisfação do cliente
- **Desempenho por Domínio**: Comparação de desempenho entre diferentes áreas de negócio
- **Eficácia dos Agentes**: Avaliação da eficácia dos diferentes agentes especializados
- **Otimização de Recursos**: Identificação de gargalos e oportunidades de otimização

### 2. Análise de Comportamento do Cliente

- **Padrões de Comunicação**: Horários de pico, frequência de contato, duração das conversas
- **Tópicos Recorrentes**: Assuntos mais frequentemente abordados pelos clientes
- **Análise de Sentimento**: Evolução do sentimento do cliente ao longo da conversa
- **Jornada do Cliente**: Mapeamento da jornada do cliente através de múltiplos canais

### 3. Análise de Negócio

- **Produtos Populares**: Produtos/serviços mais mencionados ou consultados
- **Problemas Recorrentes**: Identificação de problemas frequentes relatados pelos clientes
- **Oportunidades de Venda**: Detecção de oportunidades de upsell/cross-sell
- **Tendências Sazonais**: Identificação de padrões sazonais nas interações

### 4. Análise Multicanal

- **Comparação de Canais**: Desempenho e eficácia de diferentes canais de comunicação
- **Preferências por Segmento**: Preferências de canal por segmento de cliente
- **Consistência de Experiência**: Avaliação da consistência da experiência entre canais
- **Otimização de Canal**: Recomendações para otimização de cada canal

## Crew Analytics: Análise via Linguagem Natural

Uma das inovações planejadas é a implementação da **Crew Analytics**, que permitirá:

1. **Consultas em Linguagem Natural**: Realizar análises complexas usando linguagem natural
2. **Acesso via WhatsApp**: Números especiais de WhatsApp para interagir diretamente com o sistema de análise
3. **Dashboards Dinâmicos**: Geração de visualizações e dashboards sob demanda
4. **Insights Automatizados**: Detecção automática de padrões e anomalias relevantes

### Exemplos de Consultas

A Crew Analytics permitirá consultas como:

- "Mostre-me o desempenho do atendimento ao cliente no último mês"
- "Quais são os produtos mais mencionados nas conversas do WhatsApp?"
- "Compare o tempo médio de resposta entre os canais Instagram e WhatsApp"
- "Identifique os principais motivos de contato no canal de suporte"

## Implementação Técnica

Para viabilizar essas análises, estamos implementando:

### 1. Coleta Estruturada de Dados

- **Logs Estruturados**: Formato JSON para facilitar a análise
- **Eventos Padronizados**: Padronização de eventos para consistência
- **Metadados Enriquecidos**: Enriquecimento de metadados com informações contextuais

### 2. Armazenamento e Processamento

- **Redis**: Cache e armazenamento temporário
- **Qdrant**: Armazenamento vetorial para busca semântica
- **Banco Relacional**: Armazenamento estruturado para análises tradicionais
- **Processamento em Tempo Real**: Análise de streams de eventos em tempo real

### 3. Interfaces de Análise

- **API REST**: Endpoints para consulta de metadados e análises
- **Integração com BI**: Exportação para ferramentas como Metabase, Tableau ou PowerBI
- **Interface de Linguagem Natural**: Processamento de consultas em linguagem natural

## Próximos Passos

1. **Implementar a Customer Service Crew**: Desenvolver a crew de atendimento ao cliente com processamento paralelo
2. **Expandir a Coleta de Metadados**: Adicionar mais pontos de coleta de metadados relevantes
3. **Desenvolver a Crew Analytics**: Implementar a crew especializada em análise de dados
4. **Criar Dashboards Iniciais**: Desenvolver visualizações básicas para métricas-chave
5. **Integrar com Ferramentas de BI**: Estabelecer conexões com ferramentas de Business Intelligence

## Conclusão

A nova arquitetura do ChatwootAI, com sua estrutura organizada e centralizada, fornece uma base sólida para análises de dados avançadas. Os metadados coletados serão valiosos para otimizar o sistema, melhorar o atendimento ao cliente e gerar insights de negócio significativos.

A implementação do mapeamento de canais é um passo importante nessa direção, permitindo uma visão unificada das interações do cliente através de múltiplos canais e domínios de negócio.

---

*Documento criado em: Abril 2025*  
*Última atualização: Abril 2025*
