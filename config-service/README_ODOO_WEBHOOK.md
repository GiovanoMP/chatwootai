# Webhook do Odoo para o Serviço de Configuração

Este documento descreve a implementação do webhook dedicado para receber atualizações de configuração diretamente do Odoo.

## Visão Geral

O webhook do Odoo é um endpoint dedicado no serviço de configuração que recebe atualizações de configurações e credenciais diretamente do Odoo, sem passar pelo servidor principal. Isso simplifica o fluxo de dados e reduz pontos de falha.

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│  Odoo ERP       │────►│  Config Service │
│  (Módulos AI)   │     │  (Microserviço) │
│                 │     │                 │
└─────────────────┘     └─────────────────┘
```

## Endpoint

- **URL**: `/odoo-webhook`
- **Método**: `POST`
- **Autenticação**: Chave de API via cabeçalho `X-API-Key`

## Tipos de Eventos

O webhook suporta dois tipos de eventos:

1. **Sincronização de Credenciais** (`credentials_sync`): Atualiza as configurações e credenciais de um tenant.
2. **Sincronização de Mapeamento** (`mapping_sync`): Atualiza o mapeamento entre contas do Chatwoot e tenants internos.

## Formato de Payload

### Sincronização de Credenciais

```json
{
  "event_type": "credentials_sync",
  "account_id": "123456",
  "domain": "default",
  "name": "Cliente Exemplo",
  "description": "Configuração para Cliente Exemplo",
  "odoo_url": "https://odoo.example.com",
  "odoo_db": "odoo_db",
  "odoo_username": "admin",
  "odoo_password": "senha_segura",
  "token": "token_referencia",
  "enabled_collections": [
    "business_rules",
    "products_informations",
    "scheduling_rules",
    "support_documents"
  ]
}
```

### Sincronização de Mapeamento

```json
{
  "event_type": "mapping_sync",
  "mapping": {
    "chatwoot_account_id": "987654",
    "chatwoot_inbox_id": "12345",
    "internal_account_id": "123456",
    "domain": "default",
    "is_fallback": true,
    "sequence": 10,
    "special_whatsapp_numbers": [
      {
        "number": "5511999999999",
        "crew": "analytics"
      }
    ]
  }
}
```

## Processamento

1. **Recebimento do Webhook**: O serviço de configuração recebe o webhook e identifica o tipo de evento.
2. **Validação**: Os dados são validados para garantir que todas as informações necessárias estão presentes.
3. **Processamento**:
   - Para credenciais: Cria ou atualiza as configurações e credenciais no banco de dados.
   - Para mapeamento: Atualiza o mapeamento entre contas do Chatwoot e tenants internos.
4. **Resposta**: Retorna uma resposta com o status da operação e informações adicionais.

## Resposta

### Sucesso

```json
{
  "success": true,
  "message": "Credenciais sincronizadas com sucesso",
  "tenant_id": "123456",
  "domain": "default",
  "config_version": 1,
  "credentials_version": 1,
  "timestamp": "2023-06-01T12:00:00.000Z"
}
```

### Erro

```json
{
  "detail": "Erro ao processar evento de credenciais: YAML inválido"
}
```

## Implementação no Módulo Odoo

Para enviar webhooks diretamente para o serviço de configuração, o módulo Odoo deve ser atualizado para usar o novo endpoint:

```python
def sync_credentials(self):
    """Sincroniza as credenciais com o sistema de IA."""
    for record in self:
        # Preparar dados para o webhook
        webhook_data = {
            "event_type": "credentials_sync",
            "account_id": record.account_id,
            "domain": record.domain or "default",
            "name": record.name,
            "odoo_url": record.odoo_url,
            "odoo_db": record.odoo_db,
            "odoo_username": record.odoo_username,
            "odoo_password": record.odoo_password,
            "token": record.token,
            "enabled_collections": record.enabled_collections.mapped("name")
        }
        
        # Enviar webhook diretamente para o microserviço
        try:
            response = requests.post(
                f"{record.config_service_url}/odoo-webhook",
                json=webhook_data,
                headers={"X-API-Key": record.api_key},
                timeout=10
            )
            
            if response.status_code in (200, 201):
                record.last_sync = fields.Datetime.now()
                record.sync_status = 'success'
                record.sync_message = 'Sincronização bem-sucedida'
            else:
                record.sync_status = 'error'
                record.sync_message = f"Erro: {response.status_code} - {response.text}"
        except Exception as e:
            record.sync_status = 'error'
            record.sync_message = f"Erro: {str(e)}"
```

## Testando o Webhook

Um script de teste está disponível para simular o envio de webhooks do Odoo:

```bash
# Testar sincronização de credenciais
python scripts/test_odoo_webhook.py --type credentials --account-id 123456

# Testar sincronização de mapeamento
python scripts/test_odoo_webhook.py --type mapping --account-id 123456
```

## Logs

O serviço de configuração registra logs detalhados para facilitar a depuração:

- Recebimento de webhook
- Validação de dados
- Processamento de configurações
- Erros e exceções

Os logs podem ser visualizados no arquivo `config-service/logs/config_service.log`.

## Segurança

- O webhook é protegido por uma chave de API
- Senhas são armazenadas de forma criptografada no banco de dados
- Validação rigorosa de dados de entrada

## Próximos Passos

1. Implementar validação HMAC para garantir a autenticidade do webhook
2. Adicionar suporte para retentativas em caso de falha
3. Implementar métricas para monitoramento de desempenho
