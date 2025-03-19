# Guia de Escalabilidade do Webhook

Este documento explica como escalar o servidor webhook para lidar com múltiplas instâncias do Chatwoot.

## Capacidade Atual

O servidor webhook atual pode lidar com:
- 10-20 instâncias diferentes do Chatwoot
- 100-200 requisições por segundo
- Milhares de usuários finais simultâneos

## Estratégias de Escalabilidade

### 1. Escalabilidade Vertical

Para aumentar a capacidade do servidor atual:

```bash
# Aumentar o número de workers do uvicorn
uvicorn src.api.webhook_server:app --host 0.0.0.0 --port 8001 --workers 4
```

Configuração recomendada para diferentes tamanhos de servidor:
- Servidor pequeno (2 CPUs): 2 workers
- Servidor médio (4 CPUs): 4 workers
- Servidor grande (8+ CPUs): 8 workers

### 2. Escalabilidade Horizontal

Para distribuir a carga entre múltiplos servidores:

1. **Configurar um balanceador de carga** (Nginx, HAProxy, ou serviço de nuvem)
2. **Implantar múltiplas instâncias** do servidor webhook
3. **Usar Redis para compartilhar estado** entre instâncias

Exemplo de configuração do balanceador de carga Nginx:

```nginx
upstream webhook_servers {
    server webhook1.example.com:8001;
    server webhook2.example.com:8001;
    server webhook3.example.com:8001;
}

server {
    listen 80;
    server_name webhook.example.com;

    location / {
        proxy_pass http://webhook_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Processamento Assíncrono

Para lidar com picos de tráfego:

1. **Implementar uma fila de mensagens** (RabbitMQ, Kafka)
2. **Receber webhooks rapidamente** e colocá-los na fila
3. **Processar as mensagens** de forma assíncrona

## Identificação de Múltiplas Instâncias do Chatwoot

Para identificar diferentes instâncias do Chatwoot:

1. **Usar tokens de autenticação diferentes** para cada instância
2. **Adicionar um cabeçalho personalizado** `X-Chatwoot-Instance-Id` nas requisições
3. **Configurar o webhook_server.py** para rotear eventos baseado na instância

Exemplo de configuração no Chatwoot:

```
URL do Webhook: https://webhook.server.efetivia.com.br/webhook
Cabeçalhos:
  - Authorization: Bearer TOKEN_ESPECÍFICO_DA_INSTÂNCIA
  - X-Chatwoot-Instance-Id: nome_da_instância
```

## Monitoramento e Alertas

Para garantir a disponibilidade:

1. **Monitorar o endpoint /health** regularmente
2. **Configurar alertas** para falhas ou alta latência
3. **Implementar logs detalhados** para diagnóstico de problemas

## Plano de Escalabilidade Recomendado

1. **Fase 1 (1-5 instâncias)**: Usar um único servidor com configuração otimizada
2. **Fase 2 (5-20 instâncias)**: Aumentar recursos do servidor e número de workers
3. **Fase 3 (20+ instâncias)**: Implementar balanceamento de carga e múltiplas instâncias
4. **Fase 4 (50+ instâncias)**: Adicionar processamento assíncrono com filas de mensagens
