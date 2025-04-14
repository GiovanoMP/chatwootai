# Webhook para Sincronização de Credenciais

Este documento descreve como utilizar o webhook para sincronizar credenciais entre o módulo `ai_credentials_manager` do Odoo e o sistema de IA.

## Visão Geral

O webhook de credenciais é um endpoint seguro que permite sincronizar credenciais entre o módulo `ai_credentials_manager` do Odoo e o sistema de IA. Ele implementa:

1. **Verificação de Token**: Garante que apenas requisições autenticadas sejam processadas.
2. **Armazenamento Seguro**: Armazena apenas referências para credenciais sensíveis, não os valores reais.
3. **Mesclagem Inteligente**: Preserva a estrutura existente do arquivo YAML enquanto atualiza apenas o necessário.

## Endpoint

```
POST /webhook
```

## Headers

```
Content-Type: application/json
```

## Payload

```json
{
  "source": "credentials",
  "event": "credentials_sync",
  "account_id": "account_1",
  "token": "a1b2c3d4-e5f6-g7h8-i9j0",  // Token de autenticação
  "credentials": {
    "domain": "cosmetics",
    "name": "Cliente Teste",
    "odoo_url": "http://localhost:8069",
    "odoo_db": "account_1",
    "odoo_username": "admin",
    "token": "a1b2c3d4-e5f6-g7h8-i9j0",  // Token de referência
    "qdrant_collection": "business_rules_account_1",
    "redis_prefix": "account_1",
    "facebook_app_id": "123456789",
    "facebook_app_secret": "abcdefghijklmnopqrstuvwxyz",
    "facebook_access_token": "EAAG1234567890",
    "instagram_client_id": "987654321",
    "instagram_client_secret": "zyxwvutsrqponmlkjihgfedcba",
    "instagram_access_token": "IGQVJYabc123",
    "mercado_livre_app_id": "ML123456",
    "mercado_livre_client_secret": "ML_SECRET_123",
    "mercado_livre_access_token": "APP_USR-123456"
  }
}
```

### Campos Obrigatórios

- `source`: Deve ser "credentials" para identificar a origem da requisição
- `event`: Deve ser "credentials_sync" para identificar o tipo de evento
- `account_id`: ID da conta no formato "account_X" (ex: "account_1")
- `token`: Token de autenticação que deve corresponder ao token nas credenciais
- `credentials`: Objeto contendo as credenciais a serem sincronizadas

### Campos de Credenciais

- `domain`: Domínio de negócio (ex: "cosmetics")
- `name`: Nome do cliente
- `odoo_url`: URL do servidor Odoo
- `odoo_db`: Nome do banco de dados Odoo
- `odoo_username`: Nome de usuário para autenticação no Odoo
- `token`: Token de referência para as credenciais

### Campos Opcionais

- `qdrant_collection`: Nome da coleção no Qdrant
- `redis_prefix`: Prefixo para chaves no Redis
- `facebook_app_id`: ID do aplicativo Facebook
- `facebook_app_secret`: Segredo do aplicativo Facebook
- `facebook_access_token`: Token de acesso do Facebook
- `instagram_client_id`: ID do cliente Instagram
- `instagram_client_secret`: Segredo do cliente Instagram
- `instagram_access_token`: Token de acesso do Instagram
- `mercado_livre_app_id`: ID do aplicativo Mercado Livre
- `mercado_livre_client_secret`: Segredo do cliente Mercado Livre
- `mercado_livre_access_token`: Token de acesso do Mercado Livre

## Resposta

```json
{
  "success": true,
  "message": "Credenciais sincronizadas com sucesso",
  "account_id": "account_1",
  "config_path": "config/domains/cosmetics/account_1/config.yaml"
}
```

### Campos da Resposta

- `success`: Indica se a sincronização foi bem-sucedida
- `message`: Mensagem descritiva do resultado
- `account_id`: ID da conta processada
- `config_path`: Caminho do arquivo de configuração atualizado

## Exemplo de Uso

### Requisição

```bash
curl -X POST -H "Content-Type: application/json" -d @credentials.json http://localhost:8001/webhook
```

Onde `credentials.json` contém:

```json
{
  "source": "credentials",
  "event": "credentials_sync",
  "account_id": "account_1",
  "token": "a1b2c3d4-e5f6-g7h8-i9j0",
  "credentials": {
    "domain": "cosmetics",
    "name": "Cliente Teste",
    "odoo_url": "http://localhost:8069",
    "odoo_db": "account_1",
    "odoo_username": "admin",
    "token": "a1b2c3d4-e5f6-g7h8-i9j0"
    // ... outras credenciais
  }
}
```

### Resposta

```json
{
  "success": true,
  "message": "Credenciais sincronizadas com sucesso",
  "account_id": "account_1",
  "config_path": "config/domains/cosmetics/account_1/config.yaml"
}
```

## Fluxo de Comunicação

1. O módulo `ai_credentials_manager` envia as credenciais para o webhook
2. O webhook processa as credenciais e atualiza o arquivo YAML de configuração
3. O webhook retorna uma resposta indicando o resultado da sincronização
4. Os outros módulos Odoo obtêm as credenciais do `ai_credentials_manager` e usam para se comunicar diretamente com o sistema de IA

## Notas

### Armazenamento Seguro de Credenciais

- As credenciais são armazenadas em arquivos YAML no diretório `config/domains/{domain}/{account_id}/`
- Credenciais sensíveis (senhas, chaves de API, tokens de acesso) são armazenadas como referências, não como valores reais
- As referências seguem o formato `*_ref` (ex: `credential_ref`, `app_secret_ref`, `access_token_ref`)
- Exemplo de como as credenciais são armazenadas no YAML:

```yaml
integrations:
  mcp:
    type: "odoo-mcp"
    config:
      url: "http://localhost:8069"
      db: "account_1"
      username: "admin"
      credential_ref: "a1b2c3d4-e5f6-g7h8-i9j0"  # Referência, não a senha real
  facebook:
    app_id: "123456789"
    app_secret_ref: "fb_secret_account_1"  # Referência, não o segredo real
    access_token_ref: "fb_token_account_1"  # Referência, não o token real
```

### Mesclagem Inteligente

- O arquivo YAML é atualizado usando mesclagem inteligente, que preserva a estrutura existente
- Apenas campos com valores não vazios são atualizados
- Configurações existentes que não são afetadas pelas credenciais são mantidas intactas

### Uso das Credenciais

- As credenciais são usadas pelos outros módulos Odoo para se comunicar diretamente com o sistema de IA
- Os módulos Odoo obtêm as credenciais do `ai_credentials_manager` e usam para autenticar suas requisições
