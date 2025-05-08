# Documentação para Desenvolvedores - Sistema de Configuração e Visualização

Este documento fornece informações importantes sobre o sistema de configuração e visualização, incluindo os problemas atuais, os arquivos importantes e o contexto necessário para continuar a resolução dos problemas.

## Visão Geral do Sistema

O sistema é composto por três componentes principais:

1. **Servidor Principal**: Responsável por processar webhooks e interagir com o Chatwoot e Odoo
2. **Serviço de Configuração**: Microserviço que gerencia configurações e mapeamentos no PostgreSQL.
3. **Visualizador de Configurações**: Interface web para visualizar as configurações armazenadas no PostgreSQL.

## Problemas Atuais

### 1. Problema com o script `reiniciar_tudo.sh`

O script `reiniciar_tudo.sh` não estava apontando para o diretório correto do visualizador de configurações. Este problema foi corrigido, mas ainda pode haver problemas com a inicialização dos serviços.

### 2. Problema com a atualização do arquivo JSON no sistema de visualização

Quando o webhook é recebido, o `channel_mapping_handler.py` está salvando o arquivo JSON localmente e também tentando atualizar o serviço de configuração, mas há um problema na comunicação entre os dois. Embora as versões estejam sendo atualizadas, informações importantes nos arquivos de configuração YAML não estão sendo processadas corretamente.

### 3. Problema com a conversão de YAML para JSON

Os módulos Odoo usam arquivos YAML para configurações e credenciais, que são convertidos para JSON no PostgreSQL. O sistema de visualização extrai as informações do PostgreSQL, mas parece haver um problema na conversão ou no processamento dessas informações.

## Arquivos Importantes

### Servidor Principal

- **src/webhook/channel_mapping_handler.py**: Processa webhooks do Chatwoot e Odoo, identifica e possui um identicador sobre qual é qual.
- **src/utils/config_service_client.py**: Cliente para interagir com o serviço de configuração.

### Serviço de Configuração

- **config-service/app/api/mapping.py**: Endpoints para gerenciar o mapeamento Chatwoot.
- **config-service/app/services/mapping_service.py**: Serviços para gerenciar o mapeamento no banco de dados.
- **config-service/app/models/mapping.py**: Modelo de dados para o mapeamento.
- **config-service/app/schemas/mapping.py**: Esquemas para validação de dados.

### Visualizador de Configurações

- **config-viewer/app.py**: Aplicação Flask para visualizar as configurações.

### Scripts

- **scripts/reiniciar_tudo.sh**: Script para reiniciar todos os serviços.

## Fluxo de Atualização do Mapeamento

1. Um webhook é recebido pelo sistema, contendo informações sobre uma atualização no Chatwoot.
2. O `channel_mapping_handler.py` processa esse webhook e extrai as informações relevantes.
3. O handler tenta atualizar o mapeamento no serviço de configuração usando o `config_service_client.py`.
4. O cliente do serviço de configuração envia uma requisição para o endpoint `/mapping/` do serviço de configuração.
5. O serviço de configuração processa a requisição e atualiza o mapeamento no banco de dados PostgreSQL.
6. O visualizador de configurações lê o mapeamento atualizado do banco de dados quando solicitado.

## Fluxo de Atualização de Configurações

1. Os módulos Odoo geram arquivos YAML para configurações e credenciais.
2. Esses arquivos são enviados para o serviço de configuração.
3. O serviço de configuração converte os arquivos YAML para JSON e os armazena no PostgreSQL.
4. O visualizador de configurações lê as configurações do PostgreSQL e as exibe.

## Melhorias Implementadas

1. Adicionamos mais logs no `channel_mapping_handler.py` para identificar onde está ocorrendo o problema.
2. Adicionamos um endpoint de saúde (health check) no visualizador de configurações.
3. Melhoramos o script de reinicialização para garantir que todos os serviços sejam iniciados corretamente, com verificações de saúde mais robustas.
4. Melhoramos o cliente do serviço de configuração para fornecer mais informações de depuração.

## Próximos Passos

1. **Verificar os logs**: Analisar os logs do servidor principal, do serviço de configuração e do visualizador de configurações para identificar onde está ocorrendo o problema.
2. **Testar o fluxo completo**: Testar o fluxo completo de atualização do mapeamento e das configurações para identificar onde está ocorrendo o problema.
3. **Verificar a conversão YAML para JSON**: Verificar se a conversão de YAML para JSON está sendo feita corretamente.
4. **Verificar a comunicação entre os serviços**: Verificar se a comunicação entre o servidor principal, o serviço de configuração e o visualizador de configurações está funcionando corretamente.
5. **Verificar o banco de dados**: Verificar se os dados estão sendo armazenados corretamente no PostgreSQL.

## Comandos Úteis

### Reiniciar todos os serviços

```bash
./scripts/reiniciar_tudo.sh
```

### Verificar o status dos serviços

```bash
ps aux | grep -E "python|uvicorn"
```

### Verificar as portas em uso

```bash
netstat -tulpn | grep -E "8001|8002|8080"
```

### Verificar a saúde do serviço de configuração

```bash
curl -s http://localhost:8002/health
```

### Verificar a saúde do visualizador de configurações

```bash
curl -s http://localhost:8080/health
```

## Notas Adicionais

- O sistema usa o PostgreSQL com a extensão pgvector para armazenar as configurações e os mapeamentos.
- O sistema usa o Redis para cache.
- O sistema usa o Qdrant para busca vetorial.
- O sistema é multi-tenant, onde cada cliente (identificado por account_id) tem uma configuração diferente.
- O sistema usa o Chatwoot como plataforma de comunicação.
- O sistema usa o Odoo como ERP.

## Contato

Para mais informações, entre em contato com o desenvolvedor responsável.
