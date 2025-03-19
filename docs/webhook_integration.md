# Integração de Webhook Chatwoot-CrewAI

Este documento descreve a integração entre o Chatwoot e o sistema ChatwootAI através de webhooks, permitindo a comunicação entre os sistemas e o processamento automatizado de mensagens.

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Configuração Atual](#configuração-atual)
4. [Fluxo de Dados](#fluxo-de-dados)
5. [Guia de Implementação](#guia-de-implementação)
6. [Manutenção](#manutenção)
7. [Solução de Problemas](#solução-de-problemas)
8. [Limitações Conhecidas](#limitações-conhecidas)
9. [Próximos Passos](#próximos-passos)
10. [Histórico de Implementação](#histórico-de-implementação)

## Visão Geral

A integração permite que eventos do Chatwoot (como novas mensagens, novas conversas, etc.) sejam enviados para o sistema ChatwootAI, que pode então processá-los e responder automaticamente. Esta integração é fundamental para permitir que os agentes de IA construídos com CrewAI possam interagir com as conversas no Chatwoot.

## Arquitetura

```
┌─────────────┐       ┌───────────────────┐       ┌────────────────┐
│   Chatwoot   │──────▶│  Simple Webhook   │──────▶│  Ambiente Local │
│  (VPS/Docker) │       │    (VPS/Docker)    │       │  (Desenvolvimento) │
└─────────────┘       └───────────────────┘       └────────────────┘
```

### Componentes

1. **Chatwoot**: Sistema central de comunicação, hospedado na VPS em Docker Swarm
2. **Simple Webhook**: Serviço intermediário que recebe webhooks do Chatwoot e os encaminha para o ambiente de desenvolvimento
3. **Ambiente Local**: Ambiente de desenvolvimento onde o código do ChatwootAI é executado

### Arquivos Relevantes

#### Na VPS (Servidor de Produção)

**Diretório Atual (em uso)**
- `~/simple_webhook/simple_webhook.py`: Código principal do webhook forwarder (atualmente em uso)
- `~/simple_webhook/Dockerfile`: Configuração para construir a imagem Docker
- `~/simple_webhook/docker-stack.yml`: Configuração para implantar no Docker Swarm
- `~/simple_webhook/README.md`: Documentação do serviço

**Diretórios Legados (não usados atualmente)**
- `~/chatwoot_webhook/webhook_forwarder.py`: Implementação anterior do webhook forwarder
- `~/chatwoot_webhook/Dockerfile`: Configuração anterior para construir a imagem Docker
- `~/chatwoot_webhook/docker-stack.yml`: Configuração anterior para implantar no Docker Swarm
- `~/chatwoot_webhook/docs`: Documentação anterior
- `~/chatwoot_webhook_backup`: Diretório de backup

#### No Repositório Local
- `/webhook/simple_webhook.py`: Versão local do simple_webhook para referência
- `/src/api/webhook_server.py`: Servidor webhook que recebe eventos encaminhados

## Configuração Atual

### Na VPS (Servidor de Produção)

O serviço `simple_webhook_simple_webhook` está configurado para:
- Receber webhooks na porta 8802
- Encaminhar para a URL do ngrok configurada no arquivo `simple_webhook.py`

```bash
# Verificar status do serviço
docker service ls | grep webhook

# Ver logs do serviço
docker service logs -f simple_webhook_simple_webhook
```

### No Ambiente Local

O servidor webhook local está configurado para:
- Receber webhooks na porta 8000
- Processar eventos do Chatwoot e executar ações correspondentes

```bash
# Iniciar o túnel ngrok
./scripts/webhook/start_ngrok.sh

# Iniciar o servidor webhook local
python -m src.api.webhook_server
```

### Parâmetros de Configuração

- **URL do Webhook no Chatwoot**: `http://147.93.9.211:8802/webhook`
- **Serviço em uso**: `simple_webhook_simple_webhook` (porta 8802)
- **Autenticação**: Desativada para facilitar o desenvolvimento
- **Encaminhamento**: Para URL do ngrok que aponta para o ambiente local

## Fluxo de Dados

1. Um evento ocorre no Chatwoot (nova mensagem, nova conversa, etc.)
2. O Chatwoot envia um webhook para `http://147.93.9.211:8802/webhook`
3. O serviço Simple Webhook recebe o webhook e o encaminha para o ambiente local via ngrok
4. O servidor webhook local processa o evento e executa as ações necessárias

## Guia de Implementação

### Configuração para Desenvolvimento

1. **Iniciar o túnel ngrok**:
   ```bash
   ./scripts/webhook/start_ngrok.sh
   ```

2. **Atualizar a URL do ngrok na VPS**:
   ```bash
   ./scripts/webhook/update_webhook_url.sh https://seu-url-ngrok.ngrok-free.app
   ```

3. **Iniciar o servidor webhook local**:
   ```bash
   python -m src.api.webhook_server
   ```

### Configuração para Produção

Para o ambiente de produção, a configuração será modificada:

1. **Ativar a autenticação**:
   - Modificar o `webhook.py` para verificar o token de autenticação
   - Configurar o Chatwoot para enviar o token via parâmetro na URL: `?token=efetivia_webhook_secret_token_2025`

2. **Usar comunicação interna do Docker Swarm**:
   - Configurar o `FORWARD_URL` para apontar para o serviço interno: `http://chatwootai_webhook_server:8001/webhook`
   - Restringir o acesso ao webhook apenas para a rede interna do Docker

## Manutenção

### Atualizar a URL do ngrok

Quando a URL do ngrok mudar (por exemplo, ao reiniciar o túnel), é necessário atualizar a configuração na VPS:

1. Usar o script automatizado:
   ```bash
   ./scripts/webhook/update_webhook_url.sh https://seu-url-ngrok.ngrok-free.app
   ```

2. Ou manualmente:
   ```bash
   # Na VPS
   cd ~/simple_webhook
   nano simple_webhook.py
   # Atualizar a variável FORWARD_URL
   
   # Reconstruir a imagem e atualizar o serviço
   docker build -t simple_webhook:latest .
   docker service update --force simple_webhook_simple_webhook
   ```

### Limpeza e Manutenção da VPS

A VPS contém vários diretórios relacionados a webhook, mas apenas o `simple_webhook` está em uso atualmente. Para manter a VPS organizada, considere as seguintes ações:

#### Estrutura de Diretórios na VPS

```
~/simple_webhook/         # Diretório atual, em uso
~/chatwoot_webhook/      # Implementação anterior, não usada
~/chatwoot_webhook_backup/ # Backup, não usado
```

#### Comandos para Limpeza

```bash
# Verificar serviços em execução
docker service ls | grep webhook

# Remover serviços não utilizados (se houver)
# docker service rm nome_do_servico

# Limpar recursos Docker não utilizados
docker container prune -f
docker image prune -a -f
docker volume prune -f
docker network prune -f

# Fazer backup dos diretórios legados antes de removê-los (opcional)
mkdir -p ~/backups/webhook_$(date +%Y%m%d)
cp -r ~/chatwoot_webhook ~/backups/webhook_$(date +%Y%m%d)/
cp -r ~/chatwoot_webhook_backup ~/backups/webhook_$(date +%Y%m%d)/
rm -rf ~/chatwoot_webhook ~/chatwoot_webhook_backup
```

## Solução de Problemas

### Verificar se o webhook está sendo recebido

```bash
# Na VPS
docker service logs -f simple_webhook_simple_webhook
```

### Verificar se o webhook está sendo encaminhado corretamente

```bash
# No ambiente local
# Verificar os logs do servidor webhook local
```

### Testar o webhook manualmente

```bash
# Enviar um webhook de teste para o serviço na VPS
curl -X POST -H "Content-Type: application/json" -d '{"event": "test_event", "data": "test_data"}' http://147.93.9.211:8802/webhook

# Enviar um webhook de teste diretamente para o ambiente local via ngrok
curl -X POST -H "Content-Type: application/json" -d '{"event": "test_event", "data": "test_data"}' https://seu-url-ngrok.ngrok-free.app/webhook
```

### Problemas Comuns

- **Erro 401 Unauthorized**: Verifique se a autenticação está configurada corretamente
- **Erro de conexão**: Verifique se o FORWARD_URL está acessível
- **Webhook não recebendo eventos**: Verifique a configuração no painel do Chatwoot

## Limitações Conhecidas

- O Chatwoot v4.0 não suporta adicionar cabeçalhos personalizados aos webhooks
- A autenticação precisa ser implementada via parâmetros de URL ou verificação de IP

## Próximos Passos

1. **Implementar autenticação**: Adicionar verificação de token para aumentar a segurança
2. **Configurar para produção**: Modificar a configuração para o ambiente de produção
3. **Implementar tratamento de eventos específicos**: Adicionar lógica para processar diferentes tipos de eventos do Chatwoot

## Histórico de Implementação

Inicialmente tentamos implementar um serviço webhook personalizado (`chatwootai_webhook_server`), mas enfrentamos problemas com a autenticação. Atualmente estamos usando o serviço `simple_webhook` que já estava funcionando corretamente.
