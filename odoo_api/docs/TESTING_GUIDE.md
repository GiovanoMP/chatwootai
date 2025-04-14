# Guia de Testes para Integração com Odoo

Este guia descreve como testar a integração entre o módulo Odoo `business_rules` e a API.

## Pré-requisitos

1. Módulo Odoo `business_rules` instalado e configurado
2. API rodando e acessível
3. Redis rodando
4. Qdrant rodando
5. Variáveis de ambiente configuradas

## Configuração do Ambiente

### 1. Iniciar a API

```bash
cd odoo_api
uvicorn main:app --reload --port 8000
```

### 2. Configurar o Módulo Odoo

1. Acesse o Odoo
2. Vá para Configurações > Regras de Negócio > Configurações
3. Configure a URL da API: `http://localhost:8000`
4. Configure o token de autenticação (se necessário)
5. Salve as configurações

## Testes Manuais

### 1. Teste de Sincronização

1. Crie algumas regras de negócio no Odoo:
   - Horário de Funcionamento
   - Política de Devolução
   - Promoção Temporária

2. Acesse uma regra de negócio e clique no botão "Sincronizar com IA"

3. Verifique se:
   - O status muda para "Sincronizando" e depois para "Sincronizado"
   - Não ocorrem erros durante a sincronização
   - A data da última sincronização é atualizada

### 2. Teste de Busca Semântica

1. Use o endpoint de busca semântica para buscar regras:

```bash
curl -X GET "http://localhost:8000/api/v1/business_rules/search?account_id=account_1&query=Qual%20é%20o%20horário%20de%20funcionamento?"
```

2. Verifique se:
   - As regras relevantes são retornadas
   - Os scores de similaridade são calculados corretamente
   - As regras são ordenadas por relevância

### 3. Teste de Sincronização em Lote

1. Selecione várias regras de negócio no Odoo
2. Use a ação em lote "Sincronizar com IA"
3. Verifique se todas as regras são sincronizadas corretamente

## Testes Automatizados

### 1. Executar Testes Unitários

```bash
cd odoo_api/tests
./run_unit_tests.py
```

### 2. Executar Testes de Integração

```bash
cd odoo_api/tests
./run_integration_tests.py
```

### 3. Executar Todos os Testes

```bash
cd odoo_api/tests
./run_all_tests.py
```

## Verificação de Resultados

### 1. Verificar Redis

```bash
redis-cli
> keys account_1:*
```

Verifique se as chaves para as regras de negócio existem.

### 2. Verificar Qdrant

Use a interface web do Qdrant (http://localhost:6333/dashboard) para verificar se:
- A coleção `business_rules_account_1` existe
- Os pontos foram adicionados à coleção
- Os payloads contêm as informações corretas

## Solução de Problemas

### Problemas de Conexão

1. Verifique se a API está rodando:
```bash
curl http://localhost:8000/health
```

2. Verifique se o Redis está rodando:
```bash
redis-cli ping
```

3. Verifique se o Qdrant está rodando:
```bash
curl http://localhost:6333/collections
```

### Problemas de Sincronização

1. Verifique os logs da API:
```bash
tail -f odoo_api/logs/api.log
```

2. Verifique os logs do Odoo:
```bash
tail -f /var/log/odoo/odoo.log
```

### Problemas de Busca Semântica

1. Verifique se os embeddings foram gerados corretamente:
```bash
curl -X GET "http://localhost:8000/api/v1/business_rules/check_embeddings?account_id=account_1"
```

2. Verifique se a consulta está sendo processada corretamente:
```bash
curl -X GET "http://localhost:8000/api/v1/business_rules/process_query?query=Qual%20é%20o%20horário%20de%20funcionamento?"
```

## Próximos Passos

Após verificar que a integração funciona corretamente, você pode:

1. Implementar testes automatizados adicionais
2. Configurar monitoramento para a API
3. Implementar melhorias na qualidade dos embeddings
4. Otimizar o desempenho da busca semântica
