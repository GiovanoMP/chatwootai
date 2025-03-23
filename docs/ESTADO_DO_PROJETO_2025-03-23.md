# Estado do Projeto - 2025-03-23

## Resumo Geral

Estamos desenvolvendo uma plataforma de automação de atendimento baseada no Chatwoot como hub central, utilizando a CrewAI para orquestração de agentes inteligentes. A arquitetura segue um padrão hub-and-spoke, onde o HubCrew atua como orquestrador central para mensagens e interações.

Atualmente, estamos na fase de integrar o Ngrok ao ambiente de desenvolvimento local para permitir o recebimento em tempo real de webhooks do servidor Chatwoot em produção através do proxy na VPS. Isso permitirá iniciar os testes com mensagens reais de clientes, validando todo o fluxo de processamento.

## Componentes Principais da Arquitetura

1. **Hub Central (hub.py)**
   - `HubCrew`: Orquestração principal
   - `OrchestratorAgent`: Roteamento inteligente
   - `ContextManagerAgent`: Gestão de contexto
   - `IntegrationAgent`: Integrações externas
   - `DataProxyAgent`: Único ponto de acesso a dados

2. **Crews Especializadas**
   - `SalesCrew`: Processamento de vendas
   - `SupportCrew`: Suporte ao cliente
   - `MarketingCrew`: Campanhas e promoções

3. **Camada de Dados**
   - `DataServiceHub`: Coordenação de serviços
   - `ProductDataService`: Dados de produtos
   - `CustomerDataService`: Dados de clientes

4. **Domínios de Negócio**
   - Configurações YAML por domínio (cosméticos, saúde, etc)
   - Adaptação dinâmica via `DomainManager`

## Atualizações Recentes

### 1. Limpeza e Organização do Código

Identificamos e corrigimos duplicidades na implementação da classe `ChatwootClient`:

- Removidos os arquivos duplicados:
  - `/src/api/chatwoot_integration.py` (implementação básica)
  - `/src/api/chatwoot.py` (implementação assíncrona)

- Mantida a implementação oficial em `/src/api/chatwoot/client.py` que segue o padrão hub-and-spoke da arquitetura

### 2. Integração com Ngrok

Implementamos a integração entre o servidor webhook local e o Chatwoot em produção através do Ngrok:

- Configurado o script `scripts/webhook/start_ngrok.py` para iniciar um túnel Ngrok
- Ajustada a porta padrão para 8001 para corresponder ao servidor webhook
- Implementada automação para atualizar o proxy na VPS sempre que a URL do Ngrok mudar
- Adicionada a biblioteca `paramiko` para permitir conexão SSH automatizada com a VPS

### 3. Sistema de Configuração

- Atualizadas as variáveis de ambiente no arquivo `.env` para incluir:
  - Credenciais do Chatwoot
  - Configurações do servidor webhook
  - Token de autenticação do Ngrok
  - Credenciais e configurações da VPS para atualização automática

## Estado Atual do Fluxo de Mensagens

O fluxo atual para processamento de mensagens é:

1. **Cliente envia mensagem** → WhatsApp ou outro canal
2. **Mensagem recebida pelo Chatwoot**
3. **Chatwoot envia webhook** → VPS (http://147.93.9.211:8802/webhook)
4. **Proxy na VPS redireciona** → URL do Ngrok
5. **Ngrok redireciona** → Servidor webhook local (porta 8001)
6. **Servidor webhook processa** → HubCrew
7. **HubCrew roteia** → Crew especializada
8. **Crew processa e responde** → HubCrew → Chatwoot → Cliente

## Testes Realizados

### 1. Teste de Integração Ngrok

- ✅ Configuração do Ngrok para exposição do servidor webhook local
- ✅ Obtenção de URL pública do Ngrok
- ❌ Atualização automática do webhook no Chatwoot API (falhou com erro "Erro ao comunicar com a API do Chatwoot: 0")
- ⏳ Atualização automática do proxy na VPS (pendente de configuração)

### 2. Fluxo de Mensagens

- ⏳ Testes com mensagens reais (pendente após configuração completa do proxy)

## Problemas Identificados

1. **Erros de Configuração**:
   - Avisos durante a inicialização do servidor webhook:
     - "DomainManager não disponível, ferramentas não serão inicializadas."
     - "Diretório de domínios não encontrado: src/business_domain."

2. **Comunicação com Chatwoot API**:
   - Falha na atualização automática do webhook através da API

## Arquivos Importantes para Leitura

Para um novo desenvolvedor se contextualizar rapidamente no projeto, recomendamos a leitura dos seguintes arquivos:

1. **[docs/ESTADO_DO_PROJETO_2025-03-22.md](docs/ESTADO_DO_PROJETO_2025-03-22.md)** - Estado anterior do projeto
2. **[docs/ESTADO_DO_PROJETO_2025-03-23.md](docs/ESTADO_DO_PROJETO_2025-03-23.md)** - Este documento (estado atual)
3. **[README_NEW_ARCHITECTURE.md](README_NEW_ARCHITECTURE.md)** - Detalhes da nova arquitetura hub-and-spoke
4. **[src/webhook/server.py](src/webhook/server.py)** - Implementação do servidor webhook
5. **[src/core/hub.py](src/core/hub.py)** - Implementação do HubCrew
6. **[scripts/webhook/start_ngrok.py](scripts/webhook/start_ngrok.py)** - Script para inicialização do Ngrok

## Próximos Passos

### 1. Configuração Completa da Integração

- Preencher a senha da VPS no arquivo `.env`
- Verificar o nome correto do container do proxy na VPS
- Confirmar o caminho correto do arquivo do proxy

### 2. Testes com Mensagens Reais

- Iniciar o Ngrok e verificar a atualização automática do proxy
- Enviar mensagens de teste pelo WhatsApp ou outro canal
- Monitorar todo o fluxo desde o recebimento pelo Chatwoot até o processamento pelo HubCrew

### 3. Correção dos Avisos de Inicialização

- Investigar e corrigir os avisos relacionados ao DomainManager
- Configurar ou criar o diretório de domínios de negócio

### 4. Implementação de Melhorias

- Implementar mecanismo de log mais detalhado para facilitar o diagnóstico
- Adicionar configuração para manter URL fixa do Ngrok (necessita conta paga)
- Implementar testes automatizados para validar o fluxo completo

## Conclusão

O projeto está progredindo bem na implementação da arquitetura hub-and-spoke e na integração com o Chatwoot. O próximo marco importante é completar a configuração da integração Ngrok-VPS-Webhook para iniciar os testes com mensagens reais, validando o fluxo completo de processamento e resposta.

Com a infraestrutura básica em funcionamento, poderemos avançar para o refinamento das Crews especializadas e a implementação de funcionalidades específicas para diferentes domínios de negócio.
