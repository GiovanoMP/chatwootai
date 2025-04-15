# Testes do Sistema ChatwootAI

Este diretório contém os testes automatizados para o sistema ChatwootAI, incluindo testes unitários e de integração.

## Estrutura de Diretórios

```
tests/
├── conftest.py           # Configurações e fixtures compartilhadas
├── integration/          # Testes de integração
│   ├── test_credentials_system.py    # Testes para o sistema de credenciais
│   └── test_webhook_message_flow.py  # Testes para o fluxo de mensagens do webhook
├── unit/                 # Testes unitários
│   └── test_hybrid_search.py         # Testes para o sistema de busca híbrida
└── run_tests.py          # Script para executar os testes
```

## Requisitos

Para executar os testes, você precisa ter instalado:

- Python 3.7+
- pytest
- pytest-asyncio
- pytest-cov (opcional, para relatórios de cobertura)

Instale as dependências com:

```bash
pip install pytest pytest-asyncio pytest-cov
```

## Executando os Testes

### Todos os Testes

Para executar todos os testes:

```bash
python tests/run_tests.py
```

### Apenas Testes Unitários

Para executar apenas os testes unitários:

```bash
python tests/run_tests.py --unit
```

### Apenas Testes de Integração

Para executar apenas os testes de integração:

```bash
python tests/run_tests.py --integration
```

### Com Relatório de Cobertura

Para gerar um relatório de cobertura de código:

```bash
python tests/run_tests.py --coverage
```

Isso gerará um relatório HTML em `htmlcov/index.html`.

### Modo Verbose

Para exibir informações detalhadas durante a execução dos testes:

```bash
python tests/run_tests.py --verbose
```

## Fixtures

O arquivo `conftest.py` contém fixtures compartilhadas entre os testes:

- `test_config_dir`: Cria um diretório temporário para configurações de teste
- `mock_webhook_handler`: Cria um webhook handler para testes
- `mock_vector_service`: Cria um mock para o serviço de vetorização
- `sample_credentials_payload`: Retorna um payload de exemplo para sincronização de credenciais
- `sample_chatwoot_message`: Retorna uma mensagem de exemplo do Chatwoot
- `mock_redis_client`: Cria um mock para o cliente Redis

## Áreas de Teste

### 1. Sistema de Referências para Credenciais

Testes para verificar se o sistema de referências para credenciais está funcionando corretamente, incluindo:

- Processamento de payloads de credenciais
- Substituição de credenciais sensíveis por referências
- Atualização de configurações existentes
- Validação de tokens

### 2. Fluxo de Mensagens do Webhook

Testes para verificar se o webhook processa corretamente as mensagens do Chatwoot, incluindo:

- Extração de metadados
- Roteamento para o HubCrew
- Tratamento de mensagens de saída
- Tratamento de erros

### 3. Sistema de Busca Híbrida (BM42)

Testes para verificar se o sistema de busca híbrida está funcionando corretamente, incluindo:

- Combinação de busca densa e esparsa
- Filtragem de resultados pelo Odoo
- Ordenação por score combinado
- Cache de resultados com Redis

## Próximos Passos

Áreas que ainda precisam de testes:

1. **Testes de Integração com OpenAI**
   - Geração de embeddings
   - Agentes de embedding

2. **Testes de Persistência com Redis**
   - Persistência de crews
   - Cache de consultas

3. **Testes de Integração entre Módulos Odoo e API**
   - Módulo business_rules
   - Módulo semantic_product_description
   - Módulo product_ai_mass_management

4. **Testes de Desempenho**
   - Tempo de resposta
   - Uso de recursos
   - Escalabilidade
