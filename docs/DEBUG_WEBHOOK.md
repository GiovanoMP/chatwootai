# Guia de Debug do Webhook do ChatwootAI

Este documento explica como usar o ambiente de debug configurado para o sistema de webhook do ChatwootAI, facilitando a identificação e resolução de problemas durante a integração com o Chatwoot.

## Configuração do Ambiente de Debug

### 1. Sistema de Logs Avançado

Foi implementado um sistema de logs detalhados com diferentes níveis de verbosidade:

- **TRACE**: Nível mais detalhado, mostra informações de chamadas de função
- **DEBUG**: Detalhes técnicos úteis para debug
- **INFO**: Informações gerais sobre o fluxo de processamento
- **WARNING**: Alertas sobre situações potencialmente problemáticas
- **ERROR**: Erros que afetam o funcionamento mas permitem continuar
- **CRITICAL**: Erros críticos que impedem o funcionamento

Os logs são salvos em dois locais:
- **Console**: Para visualização em tempo real
- **Arquivos de log**: Armazenados na pasta `logs/` com data no nome do arquivo

### 2. Script de Execução com Debug

Para iniciar o servidor webhook com logs detalhados:

```bash
# Tornar o script executável
chmod +x start_webhook_debug.sh

# Executar o script
./start_webhook_debug.sh
```

Este script faz o seguinte:
- Detecta automaticamente se Ngrok está em execução e usa a URL
- Configura logs com nível de detalhamento DEBUG
- Exibe a URL completa do webhook para configuração no Chatwoot

### 3. Métricas de Performance

Foram adicionadas métricas de desempenho em pontos-chave do sistema:

- Tempo total de processamento de webhooks
- Tempo de processamento de cada handler específico
- Timestamps para análise de latência
- Informações de performance adicionadas às respostas JSON

## Configuração do Webhook no Chatwoot

1. Acesse o painel de administração do Chatwoot
2. Vá para Configurações > Aplicativos > Webhooks
3. Adicione um novo webhook com a URL fornecida pelo script (ex: `https://12345.ngrok.app/webhook`)
4. Selecione os eventos a serem enviados: `message_created`, `conversation_created`, `conversation_status_changed`
5. Salve as configurações

## Anatomia de um Webhook

### Exemplo de Payload para `message_created`:

```json
{
  "event": "message_created",
  "account": {
    "id": 1,
    "name": "Conta de Exemplo"
  },
  "conversation": {
    "id": 123,
    "inbox_id": 1
  },
  "message": {
    "id": 456,
    "content": "Olá, preciso de ajuda",
    "message_type": "incoming",
    "content_type": "text"
  },
  "contact": {
    "id": 789,
    "name": "Cliente Exemplo",
    "phone_number": "+5511999999999"
  }
}
```

## Interpretando os Logs

### Logs Comuns e Seus Significados

1. **Recebimento de webhook**:
   ```
   2025-03-19 03:45:12 - webhook_server - INFO - Webhook recebido: message_created de 192.168.1.100 em 2025-03-19T03:45:12.345678
   ```

2. **Detalhes de processamento**:
   ```
   2025-03-19 03:45:12 - chatwoot_client - DEBUG - Tipo de mensagem recebida: incoming
   2025-03-19 03:45:12 - chatwoot_client - DEBUG - Processando mensagem da conta 1, conversa 123
   ```

3. **Métricas de desempenho**:
   ```
   2025-03-19 03:45:13 - chatwoot_client - INFO - Webhook message_created processado em 0.856s
   ```

4. **Erros comuns**:
   ```
   2025-03-19 03:45:12 - chatwoot_client - ERROR - Erro ao processar webhook: ConnectionError
   ```

## Solução de Problemas Comuns

### 1. Problema: Webhook não está sendo recebido

**Verificações**:
- Confirme se o serviço Ngrok está em execução
- Verifique se a URL do webhook está corretamente configurada no Chatwoot
- Confirme se a porta 8001 está aberta no firewall

### 2. Problema: Webhook é recebido mas não processado

**Verificações**:
- Verifique o tipo de mensagem (deve ser "incoming")
- Confirme se as credenciais do Chatwoot estão corretas em `.env`
- Verifique se o Redis está acessível

### 3. Problema: Webhook processa lentamente

**Verificações**:
- Analise os logs de performance para identificar gargalos
- Verifique a conexão com o Redis e outros serviços externos
- Considere implementar mais cache para consultas frequentes

## Próximos Passos

- Adicionar ferramentas de monitoramento como Prometheus/Grafana
- Implementar alarmes para falhas e erros
- Adicionar mais métricas para análise de latência ponta a ponta
