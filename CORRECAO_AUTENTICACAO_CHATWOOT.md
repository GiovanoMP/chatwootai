# Correção da Autenticação do Cliente Chatwoot

## Problema Identificado

O sistema estava enfrentando um erro 401 (Unauthorized) ao tentar enviar mensagens para o Chatwoot. Este erro ocorria porque o formato do cabeçalho de autenticação estava incorreto.

### Detalhes do Erro

Nos logs, era possível observar o seguinte erro:

```
2025-05-01 02:34:42,276 - chatwoot_client - INFO - [debug_logger.py:116] - Response status: 401
2025-05-01 02:34:42,276 - chatwoot_client - ERROR - [debug_logger.py:124] - Erro de autenticação. Verifique se o token de API está correto e não expirou.
2025-05-01 02:34:42,277 - chatwoot_client - ERROR - [debug_logger.py:124] - Error making request to Chatwoot API: 401 Client Error: Unauthorized for url: https://chat.sprintia.com.br/api/v1/accounts/1/conversations/4/messages
```

O sistema estava usando o seguinte formato de autenticação:

```python
headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}
```

## Solução Implementada

Após pesquisa na documentação do Chatwoot, identificamos que o formato correto para autenticação na API do Chatwoot é usando o cabeçalho `api_access_token` em vez de `Authorization: Bearer`.

### Alterações Realizadas

Modificamos o arquivo `odoo_api/integrations/chatwoot/client.py` para usar o formato correto de autenticação:

```python
headers = {
    'api_access_token': api_token,
    'Content-Type': 'application/json'
}
```

## Resultado

Após a implementação da correção, o sistema passou a enviar mensagens com sucesso para o Chatwoot, como evidenciado pelos logs:

```
2025-05-01 03:03:48,292 - chatwoot_client - INFO - [debug_logger.py:116] - Response status: 200
2025-05-01 03:03:48,293 - src.webhook.webhook_handler - INFO - Resposta enviada para conversa 4
```

## Observações Adicionais

1. **Diferentes Tipos de APIs no Chatwoot**:
   - **Application APIs**: Usam `access_token` no cabeçalho de autorização
   - **Client APIs**: Usam `api_access_token` no cabeçalho

2. **Multitenancy**:
   - O sistema está configurado para suportar múltiplos tenants, onde cada cliente (identificado por account_id) pode ter uma URL diferente do Chatwoot
   - Atualmente, o sistema usa um único cliente Chatwoot global com as configurações do `.env`
   - Para implementar completamente a multitenancy, seria necessário criar clientes dinâmicos com base nas configurações específicas de cada account_id

## Próximos Passos

1. **Implementar Multitenancy Completa**:
   - Modificar o código para criar clientes Chatwoot dinâmicos com base nas configurações específicas de cada account_id
   - Carregar as configurações específicas do Chatwoot (URL base e token) para cada account_id

2. **Melhorar Tratamento de Erros**:
   - Implementar retry em caso de falhas temporárias
   - Melhorar as mensagens de erro para facilitar o diagnóstico

3. **Documentação**:
   - Atualizar a documentação do sistema para refletir o formato correto de autenticação
   - Adicionar exemplos de uso do cliente Chatwoot

## Referências

- [Documentação da API do Chatwoot](https://www.chatwoot.com/developers/api/)
- [Discussão sobre autenticação no GitHub do Chatwoot](https://github.com/orgs/chatwoot/discussions/1572)
