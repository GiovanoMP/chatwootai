# Módulo de Regras de Negócio para Sistema de IA

## Visão Geral

Este módulo permite configurar regras de negócio específicas para personalizar o comportamento dos agentes de IA de acordo com as necessidades de cada empresa. Através de uma interface intuitiva, os usuários podem definir como os agentes devem se comunicar, quais regras devem seguir e como devem responder em diferentes situações.

## Novidades (Abril 2025)

### Novos Endpoints para Consulta de Dados Processados

Foram implementados novos endpoints para consultar dados processados pelo sistema de IA:

- **GET /api/v1/business-rules/processed/company-metadata**: Retorna os metadados da empresa processados pelo sistema de IA
- **GET /api/v1/business-rules/processed/service-config**: Retorna as configurações de atendimento processadas pelo sistema de IA
- **GET /api/v1/business-rules/processed/scheduling-rules**: Retorna as regras de agendamento processadas pelo sistema de IA
- **GET /api/v1/business-rules/processed/support-documents**: Retorna todos os documentos de suporte processados pelo sistema de IA
- **GET /api/v1/business-rules/processed/support-document/{document_id}**: Retorna um documento de suporte específico processado pelo sistema de IA

Estes endpoints permitem que aplicações externas acessem os dados processados pelo sistema de IA, facilitando a integração com outros sistemas.

### Reorganização dos Agentes de Embedding

Os agentes de embedding foram reorganizados em uma estrutura de diretórios mais modular, agrupados por módulo Odoo:

- **BusinessRulesEmbeddingAgent**: Processa regras de negócio para vetorização
- **SupportDocumentEmbeddingAgent**: Processa documentos de suporte para vetorização
- **CompanyMetadataEmbeddingAgent**: Processa metadados da empresa para vetorização

Esta reorganização facilita a manutenção e a adição de novos agentes no futuro.

## Características Principais

### 1. Informações da Empresa

- **Nome e Descrição**: Configure o nome da empresa e uma descrição curta
- **Site da Empresa**: Informe o site para extração de informações
- **Valores da Marca**: Defina os valores que sua marca representa

### 2. Configurações de Atendimento

- **Saudação Inicial**: Personalize como o agente deve cumprimentar os clientes
- **Estilo de Comunicação**: Escolha entre Formal, Casual, Amigável ou Técnico
- **Uso de Emojis**: Configure se e como os emojis devem ser utilizados
- **Horário de Funcionamento**: Defina os horários e dias de atendimento
- **Tempo de Resposta**: Estabeleça expectativas de tempo de resposta

### 3. Regras Específicas do Negócio

- **Modelo de Negócio**: Selecione entre modelos pré-configurados (Restaurante, E-commerce, Clínica, etc.)
- **Regras Permanentes**: Crie regras que se aplicam permanentemente ao seu negócio
- **Regras Temporárias**: Configure regras com prazo de validade para situações específicas

### 4. Integração com Documentos

- **Suporte ao Cliente**: Envie mensagens e arquivos para o suporte técnico
- **Extração Automática**: O sistema extrai automaticamente regras e informações dos documentos

### 5. Sincronização com IA

- **Sincronização**: Envie todas as regras configuradas para o sistema de IA
- **Dashboard de Regras Ativas**: Visualize todas as regras atualmente ativas

## Modelos de Negócio Pré-configurados

O módulo inclui templates para diversos modelos de negócio:

- **Restaurante/Pizzaria**: Regras sobre entrega, reservas, formas de pagamento e combinações de sabores
- **E-commerce/Loja Virtual**: Políticas de envio, pagamento, trocas e devoluções
- **Clínica/Consultório**: Agendamento, cancelamento e convênios
- **Loja Física**: Formas de pagamento e políticas de troca
- **Prestador de Serviços**: Orçamentos, garantias e formas de pagamento

## Casos de Uso

### Restaurante
Um restaurante pode configurar regras sobre:
- Horários de entrega
- Combinações de sabores permitidas em pizzas
- Valor mínimo para pedidos
- Promoções temporárias

### E-commerce
Uma loja virtual pode definir:
- Políticas de frete grátis
- Prazos de entrega por região
- Condições de devolução
- Campanhas sazonais

### Clínica
Uma clínica pode estabelecer:
- Procedimentos para agendamento
- Políticas de cancelamento
- Convênios aceitos
- Preparação para consultas

## Instalação

1. Instale as dependências necessárias:
   ```
   pip install python-docx==0.8.11 PyPDF2==1.26.0
   ```

2. Copie o módulo para o diretório de addons do Odoo

3. Atualize a lista de módulos e instale "Regras de Negócio para Sistema de IA"

## Configuração

1. Acesse o menu "Regras de Negócio"
2. Crie uma nova regra de negócio
3. Preencha as informações básicas da empresa
4. Selecione o modelo de negócio apropriado
5. Personalize as regras conforme necessário
6. Sincronize com o sistema de IA

## Integração com Outros Módulos

Este módulo se integra com:
- Sistema de IA para atendimento ao cliente
- Módulo de Gerenciamento de Produtos no Sistema de IA
- Módulo de Descrição Semântica de Produtos
- Módulo de Gerenciador de Credenciais para IA

### Integração com Sistema de IA

O módulo se integra com o sistema de IA através de uma API REST, permitindo:

1. **Sincronização de Regras**: Envio de regras de negócio para o sistema de IA
2. **Vetorização de Dados**: Processamento e vetorização de regras, documentos e metadados
3. **Busca Semântica**: Consulta de regras e documentos usando processamento de linguagem natural
4. **Acesso a Dados Processados**: Consulta de dados processados pelo sistema de IA através dos novos endpoints

### Integração com Gerenciador de Credenciais

O módulo agora se integra com o **Gerenciador de Credenciais para IA** para obter as credenciais de autenticação de forma segura:

1. **Autenticação Centralizada**: Utiliza o módulo `ai_credentials_manager` para obter tokens de API e URLs
2. **Fallback Automático**: Se o módulo de credenciais não estiver disponível, usa os parâmetros do sistema
3. **Registro de Acessos**: Todas as operações de acesso às credenciais são registradas para auditoria
4. **Segurança Aprimorada**: Credenciais sensíveis não são armazenadas diretamente no código ou banco de dados

## Notas Técnicas

- O módulo utiliza PyPDF2 para processamento de arquivos PDF
- O módulo utiliza python-docx para processamento de arquivos DOCX
- A sincronização com o sistema de IA é feita via API REST
- Os dados processados são armazenados no Qdrant para busca semântica
- Os agentes de embedding utilizam OpenAI para processamento de linguagem natural
- A estrutura modular dos agentes facilita a manutenção e a adição de novos agentes

---

**Desenvolvido por:** ChatwootAI Team
**Versão:** 1.2
**Compatibilidade:** Odoo 14.0
