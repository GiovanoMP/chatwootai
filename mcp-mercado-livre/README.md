# MCP Mercado Livre - Documentação

## Visão Geral

Este projeto implementa um Model Context Protocol (MCP) para integração entre o ERP Odoo e o Mercado Livre. O servidor MCP atua como uma camada intermediária que facilita a comunicação entre os sistemas, permitindo que agentes de IA realizem operações via linguagem natural.

## Estrutura do Projeto

```
mcp_mercado_livre/
├── src/
│   └── main.py         # Aplicação principal Flask
├── .env.example        # Exemplo de configuração de variáveis de ambiente
├── requirements.txt    # Dependências do projeto
└── run.sh              # Script para iniciar o servidor
```

## Funcionalidades Implementadas

### Autenticação OAuth 2.0
- Rota para iniciar o fluxo de autorização
- Callback para receber o código de autorização
- Troca do código por token de acesso
- Renovação automática de tokens expirados

### Gerenciamento de Produtos
- Listar produtos
- Obter detalhes de um produto
- Criar novos produtos
- Atualizar produtos existentes
- Remover produtos

### Gerenciamento de Pedidos
- Listar pedidos
- Obter detalhes de um pedido
- Atualizar status de pedidos

### Mensagens
- Listar mensagens de um pedido
- Enviar novas mensagens

### Categorias e Atributos
- Listar categorias disponíveis
- Obter atributos de uma categoria

### Integração com Odoo
- Sincronização de produtos
- Sincronização de pedidos

### Webhooks para Notificações
- Recebimento de notificações do Mercado Livre

### Interface para Agentes de IA
- Análise de dados de vendas
- Análise de desempenho

## Configuração

1. Clone o repositório
2. Crie um arquivo `.env` baseado no `.env.example`
3. Preencha as credenciais do Mercado Livre (Client ID e Client Secret)
4. Execute o script `run.sh` para iniciar o servidor

## Requisitos

- Python 3.8+
- Flask
- Requests
- python-dotenv
- flask-cors
- PyJWT

## Uso

### Autenticação

Para iniciar o fluxo de autenticação, acesse:
```
GET /auth/mercadolivre
```

### Produtos

Listar produtos:
```
GET /products
```

Criar produto:
```
POST /products
Content-Type: application/json

{
  "title": "Produto de Exemplo",
  "category_id": "MLB123456",
  "price": 100.0,
  "currency_id": "BRL",
  "available_quantity": 10,
  "buying_mode": "buy_it_now",
  "listing_type_id": "gold_special",
  "condition": "new",
  "description": "Descrição detalhada do produto",
  "pictures": [
    {"source": "https://exemplo.com/imagem1.jpg"}
  ]
}
```

### Pedidos

Listar pedidos:
```
GET /orders
```

### Integração com Odoo

Sincronizar produtos:
```
POST /odoo/sync_products
```

## Próximos Passos

1. Implementar testes unitários e de integração
2. Expandir a documentação da API
3. Adicionar mais endpoints específicos para o Odoo
4. Implementar cache para melhorar performance
5. Adicionar monitoramento e logging avançado

## Notas

- Este servidor MCP foi desenvolvido para ser integrado com o módulo Odoo "Estúdio de Produtos com IA"
- As credenciais do Mercado Livre devem ser mantidas em segurança
- Recomenda-se usar HTTPS em ambiente de produção
