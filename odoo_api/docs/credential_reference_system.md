# Sistema de Referências para Credenciais

## Visão Geral

O sistema de referências para credenciais é uma abordagem de segurança que evita o armazenamento de credenciais sensíveis (senhas, tokens, chaves de API) diretamente nos arquivos de configuração YAML. Em vez disso, armazenamos apenas referências a essas credenciais, enquanto as credenciais reais são armazenadas em um local seguro.

## Como Funciona

### 1. Armazenamento de Referências

Nos arquivos de configuração YAML, as credenciais sensíveis são substituídas por referências:

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

### 2. Armazenamento de Credenciais Reais

As credenciais reais são armazenadas em um arquivo separado (`credentials.yaml`) que não é versionado:

```yaml
account_1:
  a1b2c3d4-e5f6-g7h8-i9j0: "senha_real_do_odoo"
  fb_secret_account_1: "segredo_real_do_facebook"
  fb_token_account_1: "token_real_do_facebook"
```

### 3. Recuperação de Credenciais

Quando um componente do sistema precisa acessar uma credencial:

1. Ele lê a referência do arquivo de configuração YAML
2. Usa a referência para recuperar a credencial real do armazenamento seguro
3. Usa a credencial real para autenticar com o serviço externo

## Implementação

### OdooConnectorFactory

O `OdooConnectorFactory` foi atualizado para usar o sistema de referências:

1. Carrega a configuração do arquivo YAML
2. Extrai a referência da credencial (`credential_ref`)
3. Usa a referência para recuperar a credencial real
4. Cria um conector Odoo com a credencial real

### Endpoint de Credenciais

Foi implementado um endpoint seguro para recuperar credenciais:

```
POST /api/v1/credentials/get
```

**Payload:**
```json
{
  "credential_ref": "a1b2c3d4-e5f6-g7h8-i9j0",
  "account_id": "account_1"
}
```

**Resposta:**
```json
{
  "credential": "senha_real_do_odoo"
}
```

Este endpoint é protegido por autenticação de token e registra todos os acessos às credenciais.

## Vantagens de Segurança

1. **Proteção contra Exposição**: Credenciais sensíveis não são expostas nos arquivos de configuração
2. **Centralização**: Todas as credenciais são gerenciadas em um único local
3. **Auditoria**: Todos os acessos às credenciais são registrados
4. **Rotação Simplificada**: Facilita a rotação de credenciais sem afetar a configuração

## Configuração

### Arquivos de Configuração

1. **config/account_mapping.yaml**: Mapeia account_ids para domínios
2. **config/domains/{domain}/{account_id}/config.yaml**: Configuração específica do account_id
3. **config/credentials.yaml**: Armazena as credenciais reais (não versionado)

### Ambiente de Desenvolvimento

Em ambiente de desenvolvimento, o sistema pode usar a própria referência como credencial para facilitar o desenvolvimento.

## Integração com o Webhook de Credenciais

O webhook de credenciais do módulo `ai_credentials_manager` do Odoo envia as credenciais para o sistema de IA, que as armazena como referências nos arquivos YAML e como valores reais no arquivo `credentials.yaml`.

## Considerações de Segurança

1. O arquivo `credentials.yaml` deve ser protegido e nunca versionado
2. Em produção, considere usar um serviço de gerenciamento de segredos em vez de um arquivo
3. Implemente rotação regular de credenciais
4. Monitore os logs de acesso às credenciais
