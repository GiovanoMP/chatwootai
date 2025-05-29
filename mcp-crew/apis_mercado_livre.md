# Documentação das APIs do Mercado Livre

## Introdução

Este documento contém informações detalhadas sobre as APIs do Mercado Livre que serão utilizadas para a implementação do MCP (Model Context Protocol) para integração com o Odoo ERP. As informações foram coletadas da documentação oficial do Mercado Livre.

## Autenticação e Autorização

### Fluxo de Autenticação

O Mercado Livre utiliza o protocolo OAuth 2.0 para autenticação e autorização. O fluxo básico é:

1. Redirecionar o usuário para a página de autorização do Mercado Livre
2. O usuário concede permissão à aplicação
3. O Mercado Livre redireciona de volta para a aplicação com um código de autorização
4. A aplicação troca o código por um token de acesso
5. A aplicação usa o token de acesso para fazer chamadas à API

### Obtenção de Credenciais

Para obter as credenciais (Client ID e Client Secret), é necessário:

1. Criar uma conta no Mercado Livre (preferencialmente pessoa jurídica)
2. Acessar o DevCenter do Mercado Livre Brasil
3. Criar uma aplicação, definindo:
   - Nome da aplicação
   - Nome curto
   - Descrição
   - Logo
   - URLs de redirecionamento (HTTPS obrigatório)
   - Escopos (leitura, escrita, acesso offline)
   - Tópicos para notificações

### Escopos de Acesso

- **Leitura**: permite o uso de métodos API GET HTTPS
- **Escrita**: permite o uso de métodos API PUT, POST e DELETE HTTPS
- **Acesso off-line**: permite realizar solicitações via server side e refresh token

## APIs Principais

### 1. API de Produtos

#### Endpoints Principais:

- **Listar produtos**: `GET /users/{user_id}/items/search`
- **Obter detalhes de um produto**: `GET /items/{item_id}`
- **Criar produto**: `POST /items`
- **Atualizar produto**: `PUT /items/{item_id}`
- **Deletar produto**: `DELETE /items/{item_id}`

#### Categorização de Produtos:

- **Obter categorias**: `GET /sites/{site_id}/categories`
- **Obter atributos de categoria**: `GET /categories/{category_id}/attributes`

### 2. API de Vendas/Pedidos

#### Endpoints Principais:

- **Listar pedidos**: `GET /orders/search`
- **Obter detalhes de um pedido**: `GET /orders/{order_id}`
- **Atualizar status de pedido**: `PUT /orders/{order_id}`

### 3. API de Envios

#### Endpoints Principais:

- **Obter métodos de envio**: `GET /shipment_preferences`
- **Criar etiqueta de envio**: `POST /shipments/{shipment_id}/labels`
- **Rastrear envio**: `GET /shipments/{shipment_id}/tracking`

### 4. API de Mensagens

#### Endpoints Principais:

- **Listar mensagens**: `GET /messages/orders/{order_id}`
- **Enviar mensagem**: `POST /messages/orders/{order_id}`

### 5. API de Preços

- **Atualizar preço**: `PUT /items/{item_id}/price`
- **Atualizar estoque**: `PUT /items/{item_id}/stock`

## Tópicos para Notificações

O Mercado Livre oferece um sistema de notificações para eventos importantes:

- **Orders**: Notificações sobre novos pedidos e alterações em pedidos existentes
- **Messages**: Notificações sobre novas mensagens de compradores
- **Items**: Notificações sobre alterações em produtos
- **Catalog**: Notificações sobre alterações no catálogo
- **Shipments**: Notificações sobre alterações em envios
- **Promotions**: Notificações sobre promoções

## Limites e Restrições

- **Rate Limiting**: O Mercado Livre impõe limites de requisições por minuto/hora
- **Tamanho de Payload**: Existem limites para o tamanho dos dados enviados
- **Formato de Imagens**: Requisitos específicos para imagens de produtos
- **Campos Obrigatórios**: Cada endpoint possui campos obrigatórios específicos

## Boas Práticas

1. **Armazenamento Seguro de Tokens**: Nunca armazene tokens em código-fonte
2. **Renovação de Tokens**: Implemente a renovação automática de tokens expirados
3. **Tratamento de Erros**: Implemente tratamento adequado para todos os códigos de erro
4. **Webhooks**: Configure corretamente os webhooks para receber notificações em tempo real
5. **Testes**: Utilize o ambiente de sandbox para testes antes de ir para produção

## Exemplos de Uso

### Autenticação

```python
import requests

def get_access_token(code, redirect_uri, client_id, client_secret):
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }
    response = requests.post(url, data=payload)
    return response.json()
```

### Listar Produtos

```python
import requests

def get_user_items(access_token, user_id):
    url = f"https://api.mercadolibre.com/users/{user_id}/items/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json()
```

### Criar Produto

```python
import requests

def create_item(access_token, item_data):
    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=item_data, headers=headers)
    return response.json()
```

## Recursos Adicionais

- [Documentação Oficial do Mercado Livre](https://developers.mercadolivre.com.br/pt_br/api-docs-pt-br)
- [Guia de Autenticação](https://developers.mercadolivre.com.br/pt_br/autenticacao-e-autorizacao)
- [Guia para Produtos](https://developers.mercadolivre.com.br/pt_br/guia-para-produtos)
