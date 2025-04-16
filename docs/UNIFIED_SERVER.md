# Servidor Unificado - Sistema Integrado Odoo-AI

Este documento descreve a nova arquitetura unificada do sistema, que combina o servidor webhook do Chatwoot e a API Odoo em um único aplicativo FastAPI.

## Visão Geral

A arquitetura unificada resolve o problema de comunicação entre o módulo Odoo e o sistema de IA, permitindo que ambos os componentes (webhook do Chatwoot e API Odoo) sejam acessados através da mesma URL.

### Benefícios

- **Simplicidade**: Um único servidor para gerenciar e implantar
- **Organização**: Código bem estruturado com responsabilidades claras
- **Manutenção**: Fácil de manter e estender
- **Profissionalismo**: Arquitetura limpa e bem definida
- **Escalabilidade**: Pode evoluir para uma arquitetura de microserviços no futuro, se necessário

## Arquitetura

O servidor unificado mantém a separação lógica entre os diferentes tipos de endpoints, usando prefixos de rota para direcionar as requisições para os componentes corretos:

- `/webhook/*`: Rotas para o webhook do Chatwoot
- `/api/v1/*`: Rotas para a API Odoo

### Componentes Principais

1. **Servidor Unificado (`main.py`)**
   - Ponto de entrada principal do sistema
   - Configura middlewares, eventos e roteadores
   - Unifica os logs e o tratamento de erros

2. **Webhook (`src/webhook/`)**
   - `routes.py`: Rotas para o webhook do Chatwoot
   - `init.py`: Lógica de inicialização do webhook
   - `webhook_handler.py`: Lógica de processamento de webhooks

3. **API Odoo (`odoo_api/`)**
   - Módulos específicos para diferentes funcionalidades
   - Cada módulo tem seu próprio roteador FastAPI

## Fluxos de Comunicação

### 1. Fluxo de Mensagens do Chatwoot

```
Chatwoot → Webhook Proxy (VPS) → Ngrok → Servidor Unificado (/webhook) → HubCrew → Processamento
```

### 2. Fluxo de Sincronização de Regras de Negócio

```
Módulo Odoo → Ngrok → Servidor Unificado (/api/v1/business-rules/sync) → Processamento
```

## Configuração e Implantação

### Pré-requisitos

- Python 3.10+
- Ngrok instalado
- Conta no Chatwoot configurada
- Variáveis de ambiente configuradas no arquivo `.env`

### Variáveis de Ambiente Importantes

```
# Configurações do Servidor
SERVER_PORT=8000
SERVER_HOST=0.0.0.0

# Configurações do Ngrok
NGROK_AUTH_TOKEN=seu_token_ngrok

# Configurações do Chatwoot
CHATWOOT_API_KEY=sua_chave_api
CHATWOOT_BASE_URL=https://seu.chatwoot.url/api/v1
CHATWOOT_ACCOUNT_ID=1

# Configurações da API Odoo
ODOO_API_URL=http://localhost:8001  # Não mais necessário com o servidor unificado
```

### Iniciando o Sistema

#### Passo 1: Configurar o Sistema de Logs

```bash
# A partir da raiz do projeto
python scripts/webhook/setup_logging.py
```

#### Passo 2: Iniciar o Servidor Unificado

```bash
# A partir da raiz do projeto
python scripts/start_unified_server.py
```

#### Passo 3: Iniciar o Ngrok

```bash
# A partir da raiz do projeto
python scripts/start_ngrok_unified.py
```

#### Passo 4: Atualizar a Configuração na VPS

Siga as instruções fornecidas pelo script `start_ngrok_unified.py` para atualizar a configuração na VPS.

## Monitoramento e Logs

Os logs do sistema são armazenados no diretório `logs/`:

- `logs/webhook.log`: Logs do webhook do Chatwoot
- `logs/hub.log`: Logs do HubCrew
- `logs/odoo_api.log`: Logs da API Odoo
- `logs/YYYYMMDD_unified_server.log`: Logs do servidor unificado

## Solução de Problemas

### Problema: O servidor não inicia

Verifique se todas as dependências estão instaladas:

```bash
pip install -r requirements.txt
```

### Problema: O Ngrok não conecta

Verifique se o token de autenticação do Ngrok está configurado corretamente no arquivo `.env`.

### Problema: O módulo Odoo não consegue acessar o endpoint

Verifique se a URL do Ngrok está configurada corretamente na VPS e se o módulo Odoo está usando a URL correta.

## Próximos Passos

### Curto Prazo

- Implementar testes automatizados para o servidor unificado
- Melhorar o monitoramento e logging
- Adicionar autenticação para endpoints da API

### Longo Prazo

- Migrar para uma arquitetura de microserviços com Docker/Docker Swarm
- Implementar um API Gateway real (como Kong ou Traefik)
- Implementar balanceamento de carga e alta disponibilidade
