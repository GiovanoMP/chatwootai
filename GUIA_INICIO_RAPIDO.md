# Guia de Início Rápido - ChatwootAI

Este guia contém os passos necessários para iniciar o ambiente de desenvolvimento local do ChatwootAI e conectar-se ao Chatwoot para testes.

## Passo 1: Iniciar o Servidor Webhook e Ngrok

O primeiro passo é iniciar o servidor webhook e configurar o túnel ngrok para receber webhooks do Chatwoot:

```bash
# No diretório raiz do projeto
./scripts/webhook/start_webhook_connection.sh
```

Este script irá:
- Verificar se o servidor webhook está rodando
- Iniciar o servidor webhook se necessário
- Verificar se o túnel ngrok está ativo
- Iniciar o túnel ngrok se necessário
- Mostrar a URL pública do ngrok

Quando solicitado, você pode optar por atualizar a URL do webhook na VPS e testar o webhook.

## Passo 2: Atualizar a URL do Webhook no Chatwoot

Se você estiver usando uma instância remota do Chatwoot, atualize a URL do webhook:

```bash
# Substitua a URL pelo valor fornecido pelo script anterior
./scripts/webhook/update_webhook_url.sh https://sua-url-ngrok.ngrok-free.app/webhook
```

## Passo 3: Iniciar o Ambiente CrewAI

Para iniciar o ambiente CrewAI e processar mensagens do Chatwoot:

```bash
# No diretório raiz do projeto
python -m src.main
```

Este comando iniciará o serviço principal que:
- Conecta-se à API do Chatwoot
- Carrega os agentes e crews configurados
- Processa mensagens recebidas via webhook

## Verificação do Funcionamento

Para verificar se tudo está funcionando corretamente:

1. **Verificar o servidor webhook**:
   ```bash
   curl http://localhost:8001/health
   ```
   Deve retornar `{"status":"ok"}`.

2. **Verificar a conexão com o Chatwoot**:
   ```bash
   curl -H "api_access_token: $CHATWOOT_API_KEY" $CHATWOOT_BASE_URL/accounts/$CHATWOOT_ACCOUNT_ID/contacts
   ```
   Deve retornar uma lista de contatos.

3. **Testar o webhook**:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"event": "test_event", "data": "test_data"}' http://localhost:8001/webhook
   ```
   Deve retornar `{"status":"success","message":"Evento test_event processado com sucesso"}`.

## Solução de Problemas

### Servidor webhook não inicia

Verifique se não há outro processo usando a porta 8001:
```bash
lsof -i :8001
```

### Ngrok não inicia

Verifique se não há outra sessão do ngrok ativa:
```bash
ps aux | grep ngrok
```

### CrewAI não processa mensagens

Verifique os logs do serviço principal:
```bash
tail -f logs/chatwoot_integration.log
```

## Encerrando os Serviços

Para encerrar os serviços:

1. Interrompa o serviço principal do CrewAI com `Ctrl+C`
2. Interrompa o servidor webhook e o ngrok:
   ```bash
   pkill -f "webhook_server.py"
   pkill -f "ngrok"
   ```

## Próximos Passos

Para implantação em produção, consulte:
- `docs/webhook_integration.md` para detalhes sobre a integração com webhook
- `scripts/webhook/deploy_webhook_swarm.sh` para implantar no Docker Swarm
