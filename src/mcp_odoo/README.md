# MCP-Odoo: Message Control Program para Odoo

Este módulo implementa um servidor MCP (Message Control Protocol) para integração com o Odoo ERP, permitindo que agentes de IA possam interagir com dados do Odoo de forma eficiente e transparente.

## Visão Geral

O MCP-Odoo atua como uma camada de abstração entre os agentes de IA e o Odoo, fornecendo uma interface consistente para operações comuns como busca de produtos, criação de pedidos, agendamento de compromissos e muito mais.

## Componentes Principais

### OdooClient

Cliente para comunicação com o Odoo via XML-RPC, implementando métodos para:

- Autenticação e conexão com o Odoo
- Operações CRUD (Create, Read, Update, Delete)
- Busca de modelos e campos
- Execução de métodos específicos do Odoo

### FastMCP Server

Servidor MCP baseado na biblioteca FastMCP, que expõe ferramentas (tools) para interação com o Odoo:

#### Ferramentas de Vendas
- `create_sales_order`: Criar pedidos de venda
- `confirm_sales_order`: Confirmar pedidos de venda
- `create_invoice_from_sales_order`: Criar faturas a partir de pedidos

#### Ferramentas de Calendário
- `create_calendar_event`: Criar eventos de calendário/compromissos
- `check_calendar_availability`: Verificar disponibilidade para compromissos

#### Ferramentas de Produtos
- `search_products`: Buscar produtos com diversos critérios
- `get_product_details`: Obter detalhes de produtos específicos

#### Ferramentas de Clientes
- `search_customers`: Buscar clientes com diversos critérios

#### Ferramentas de Estoque
- `get_stock_quantities`: Obter quantidades em estoque para produtos

#### Ferramentas de Preços
- `get_product_prices`: Obter preços de produtos para clientes específicos

#### Ferramentas de Pagamento
- `get_payment_methods`: Obter métodos de pagamento disponíveis

## Configuração

### Configuração Multi-Tenant

O MCP-Odoo foi projetado para suportar uma arquitetura multi-tenant, onde:

1. Cada **domínio** representa um modelo de negócio (furniture, cosmetics, etc.)
2. Cada **account_id** representa um cliente específico dentro daquele domínio
3. Não existe um "cliente padrão" - cada cliente tem sua própria configuração

#### Estrutura de Configuração YAML

As credenciais e configurações do Odoo são carregadas de arquivos YAML localizados em:

```
@config/<domínio>/<account_id>.yaml
```

Exemplo de configuração:

```yaml
# Configuração para o domínio de móveis, account_2
name: "Móveis Elegantes"
description: "Loja de móveis elegantes e modernos"
domain: "furniture"
account_id: "account_2"

# Configurações de integração
integrations:
  # Configuração do MCP (Message Control Program)
  mcp:
    type: "odoo-mcp"  # Tipo de MCP a ser usado
    config:
      url: "http://localhost:8069"
      db: "account_2"
      username: "usuario@exemplo.com"
      password: "senha"
      timeout: 30
      verify_ssl: false
```

#### Variáveis de Ambiente (Apenas para Desenvolvimento)

Apenas para fins de desenvolvimento e testes, o cliente Odoo pode ser configurado através de variáveis de ambiente, mas em produção sempre deve-se usar as configurações YAML:

- `ODOO_URL`: URL do servidor Odoo
- `ODOO_DB`: Nome do banco de dados Odoo
- `ODOO_USERNAME`: Nome de usuário para autenticação
- `ODOO_PASSWORD`: Senha para autenticação
- `ODOO_TIMEOUT`: Timeout para conexão em segundos
- `ODOO_VERIFY_SSL`: Verificar certificados SSL

## Uso

### Iniciar o Servidor MCP-Odoo

```python
from src.mcp_odoo import mcp

# Iniciar o servidor MCP-Odoo
mcp.run(transport='sse')  # ou 'stdio'
```

### Usar o Cliente Odoo Diretamente

```python
from src.mcp_odoo import OdooClient, get_odoo_client_for_account
from src.core.domain.domain_manager import DomainManager

# Obter o DomainManager
domain_manager = DomainManager()

# Obter cliente Odoo para um domínio e conta específicos
client = get_odoo_client_for_account(
    domain_name="furniture",
    account_id="account_2",
    domain_manager=domain_manager
)

# Ou criar um cliente com parâmetros específicos para testes
client = OdooClient(
    url="http://localhost:8069",
    db="nome_do_banco",
    username="usuario",
    password="senha",
    timeout=30,
    verify_ssl=False
)

# Buscar parceiros
partner_ids = client.search(
    model_name='res.partner',
    domain=[('is_company', '=', True)],
    limit=5
)

# Ler dados dos parceiros
partners = client.read_records(
    model_name='res.partner',
    ids=partner_ids,
    fields=['name', 'email', 'phone']
)

# Criar um novo parceiro
new_partner_id = client.create(
    model_name='res.partner',
    values={
        'name': 'Novo Parceiro',
        'email': 'novo@exemplo.com',
        'phone': '(11) 1234-5678'
    }
)

# Atualizar um parceiro existente
client.write(
    model_name='res.partner',
    record_id=new_partner_id,
    values={
        'name': 'Parceiro Atualizado'
    }
)

# Excluir um parceiro
client.unlink(
    model_name='res.partner',
    record_id=new_partner_id
)
```

## Integração com DataProxyAgent

O DataProxyAgent pode usar o MCP-Odoo para acessar dados do Odoo, fornecendo uma interface consistente para os agentes de IA. A integração é feita através do MCP, que atua como uma camada de abstração entre o DataProxyAgent e o Odoo.

## Considerações sobre o Odoo 14

Este módulo foi desenvolvido especificamente para o Odoo 14, levando em consideração as particularidades da API XML-RPC desta versão. Algumas adaptações foram necessárias para lidar com as diferenças na forma como os métodos são chamados, especialmente para operações de busca e leitura de registros.

## Próximos Passos

- Implementar cache com Redis para melhorar o desempenho
- Adicionar suporte a operações em lote para melhorar a eficiência
- Implementar métodos adicionais para operações específicas do negócio
- Melhorar a documentação e adicionar exemplos de uso
- Implementar testes automatizados para garantir a qualidade do código
