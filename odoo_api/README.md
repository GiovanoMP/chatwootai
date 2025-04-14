# Odoo API

API REST para integração com Odoo, permitindo a comunicação entre os módulos Odoo e o sistema de IA.

## Visão Geral

Esta API fornece endpoints para:

- Geração de descrições semânticas para produtos
- Sincronização de produtos com banco de dados vetorial
- Busca semântica de produtos
- Gerenciamento em massa de produtos
- Gerenciamento de regras de negócio

## Estrutura do Projeto

```
odoo_api/
├── __init__.py
├── main.py                  # Ponto de entrada da aplicação
├── config/                  # Configurações
│   ├── __init__.py
│   └── settings.py          # Configurações da aplicação
├── core/                    # Componentes centrais
│   ├── __init__.py
│   ├── auth.py              # Autenticação e autorização
│   ├── exceptions.py        # Exceções personalizadas
│   ├── odoo_connector.py    # Conector base para Odoo
│   └── middleware.py        # Middlewares da aplicação
├── modules/                 # Módulos da API
│   ├── __init__.py
│   ├── semantic_product/    # API para descrições semânticas
│   │   ├── __init__.py
│   │   ├── routes.py        # Endpoints da API
│   │   ├── schemas.py       # Modelos de dados
│   │   └── services.py      # Lógica de negócio
│   ├── product_management/  # API para gerenciamento de produtos
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   └── business_rules/      # API para regras de negócio
│       ├── __init__.py
│       ├── routes.py
│       ├── schemas.py
│       └── services.py
├── services/                # Serviços compartilhados
│   ├── __init__.py
│   ├── cache_service.py     # Serviço de cache com Redis
│   ├── vector_service.py    # Serviço de vetorização e Qdrant
│   └── notification_service.py  # Serviço de notificações
├── utils/                   # Utilitários
│   ├── __init__.py
│   ├── logging.py           # Configuração de logging
│   ├── validators.py        # Validadores comuns
│   └── helpers.py           # Funções auxiliares
├── tests/                   # Testes automatizados
│   ├── __init__.py
│   ├── conftest.py          # Configurações de teste
│   ├── unit/                # Testes unitários
│   └── integration/         # Testes de integração
└── docs/                    # Documentação
    ├── PLANO_DE_ACAO.md     # Plano de ação
    ├── API_REFERENCE.md     # Referência da API
    └── ARCHITECTURE.md      # Detalhes da arquitetura
```

## Requisitos

- Python 3.8+
- Redis
- Qdrant
- Odoo 14+

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/odoo-api.git
cd odoo-api
```

2. Crie um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## Execução

Para iniciar o servidor de desenvolvimento:

```bash
uvicorn odoo_api.main:app --reload
```

A API estará disponível em http://localhost:8000.

A documentação da API estará disponível em http://localhost:8000/docs.

## Endpoints Principais

### Módulo Semantic Product

- `POST /api/v1/products/{product_id}/description`: Gera uma descrição semântica para um produto
- `POST /api/v1/products/{product_id}/sync`: Sincroniza um produto com o banco de dados vetorial
- `POST /api/v1/products/search`: Realiza uma busca semântica de produtos

### Módulo Product Management

- `POST /api/v1/products/sync-batch`: Sincroniza múltiplos produtos
- `POST /api/v1/products/update-prices`: Atualiza preços em massa
- `GET /api/v1/products/sync-status`: Verifica o status de sincronização

### Módulo Business Rules

- `POST /api/v1/business-rules`: Cria uma nova regra de negócio
- `POST /api/v1/business-rules/temporary`: Cria uma nova regra temporária
- `POST /api/v1/business-rules/sync`: Sincroniza regras com o sistema de IA
- `GET /api/v1/business-rules/active`: Lista regras ativas

## Testes

Para executar os testes:

```bash
pytest
```

## Documentação

A documentação completa está disponível na pasta `docs/`:

- [Plano de Ação](docs/PLANO_DE_ACAO.md): Plano detalhado para o desenvolvimento da API
- [Referência da API](docs/API_REFERENCE.md): Documentação dos endpoints da API
- [Arquitetura](docs/ARCHITECTURE.md): Detalhes da arquitetura do sistema

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
