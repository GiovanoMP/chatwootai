import os
import sys
from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
import requests
import json
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')

# Configurações do Mercado Livre
ML_CLIENT_ID = os.getenv('ML_CLIENT_ID', '')
ML_CLIENT_SECRET = os.getenv('ML_CLIENT_SECRET', '')
ML_REDIRECT_URI = os.getenv('ML_REDIRECT_URI', 'https://www.sprintia.com.br/callback')
ML_API_BASE_URL = 'https://api.mercadolibre.com'

# Rotas para autenticação
@app.route('/auth/mercadolivre')
def auth_mercadolivre():
    """
    Redireciona o usuário para a página de autorização do Mercado Livre
    """
    auth_url = f"https://auth.mercadolibre.com.br/authorization?response_type=code&client_id={ML_CLIENT_ID}&redirect_uri={ML_REDIRECT_URI}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """
    Recebe o código de autorização e troca por um token de acesso
    """
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Código de autorização não recebido"}), 400
    
    # Troca o código por um token de acesso
    token_url = f"{ML_API_BASE_URL}/oauth/token"
    data = {
        'grant_type': 'authorization_code',
        'client_id': ML_CLIENT_ID,
        'client_secret': ML_CLIENT_SECRET,
        'code': code,
        'redirect_uri': ML_REDIRECT_URI
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter token de acesso", "details": response.text}), 400
    
    token_data = response.json()
    # Armazena o token na sessão (em produção, use um armazenamento mais seguro)
    session['ml_access_token'] = token_data.get('access_token')
    session['ml_refresh_token'] = token_data.get('refresh_token')
    session['ml_user_id'] = token_data.get('user_id')
    
    return jsonify({"message": "Autenticação realizada com sucesso", "user_id": token_data.get('user_id')})

@app.route('/refresh_token')
def refresh_token():
    """
    Atualiza o token de acesso usando o refresh token
    """
    refresh_token = session.get('ml_refresh_token')
    if not refresh_token:
        return jsonify({"error": "Refresh token não encontrado"}), 400
    
    token_url = f"{ML_API_BASE_URL}/oauth/token"
    data = {
        'grant_type': 'refresh_token',
        'client_id': ML_CLIENT_ID,
        'client_secret': ML_CLIENT_SECRET,
        'refresh_token': refresh_token
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao atualizar token de acesso", "details": response.text}), 400
    
    token_data = response.json()
    session['ml_access_token'] = token_data.get('access_token')
    session['ml_refresh_token'] = token_data.get('refresh_token')
    
    return jsonify({"message": "Token atualizado com sucesso"})

# Rotas para produtos
@app.route('/products', methods=['GET'])
def get_products():
    """
    Obtém a lista de produtos do usuário
    """
    access_token = session.get('ml_access_token')
    user_id = session.get('ml_user_id')
    
    if not access_token or not user_id:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/users/{user_id}/items/search"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter produtos", "details": response.text}), 400
    
    return jsonify(response.json())

@app.route('/products/<item_id>', methods=['GET'])
def get_product(item_id):
    """
    Obtém detalhes de um produto específico
    """
    access_token = session.get('ml_access_token')
    
    if not access_token:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/items/{item_id}"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter detalhes do produto", "details": response.text}), 400
    
    return jsonify(response.json())

@app.route('/products', methods=['POST'])
def create_product():
    """
    Cria um novo produto
    """
    access_token = session.get('ml_access_token')
    
    if not access_token:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/items"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=request.json, headers=headers)
    if response.status_code not in [200, 201]:
        return jsonify({"error": "Falha ao criar produto", "details": response.text}), 400
    
    return jsonify(response.json())

@app.route('/products/<item_id>', methods=['PUT'])
def update_product(item_id):
    """
    Atualiza um produto existente
    """
    access_token = session.get('ml_access_token')
    
    if not access_token:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/items/{item_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.put(url, json=request.json, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao atualizar produto", "details": response.text}), 400
    
    return jsonify(response.json())

@app.route('/products/<item_id>', methods=['DELETE'])
def delete_product(item_id):
    """
    Remove um produto
    """
    access_token = session.get('ml_access_token')
    
    if not access_token:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/items/{item_id}"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.delete(url, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao remover produto", "details": response.text}), 400
    
    return jsonify({"message": "Produto removido com sucesso"})

# Rotas para pedidos
@app.route('/orders', methods=['GET'])
def get_orders():
    """
    Obtém a lista de pedidos
    """
    access_token = session.get('ml_access_token')
    seller_id = session.get('ml_user_id')
    
    if not access_token or not seller_id:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/orders/search"
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'seller': seller_id}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter pedidos", "details": response.text}), 400
    
    return jsonify(response.json())

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """
    Obtém detalhes de um pedido específico
    """
    access_token = session.get('ml_access_token')
    
    if not access_token:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/orders/{order_id}"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter detalhes do pedido", "details": response.text}), 400
    
    return jsonify(response.json())

# Rotas para mensagens
@app.route('/messages/orders/<order_id>', methods=['GET'])
def get_messages(order_id):
    """
    Obtém mensagens de um pedido
    """
    access_token = session.get('ml_access_token')
    
    if not access_token:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/messages/orders/{order_id}"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter mensagens", "details": response.text}), 400
    
    return jsonify(response.json())

@app.route('/messages/orders/<order_id>', methods=['POST'])
def send_message(order_id):
    """
    Envia uma mensagem para um pedido
    """
    access_token = session.get('ml_access_token')
    
    if not access_token:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    url = f"{ML_API_BASE_URL}/messages/orders/{order_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=request.json, headers=headers)
    if response.status_code not in [200, 201]:
        return jsonify({"error": "Falha ao enviar mensagem", "details": response.text}), 400
    
    return jsonify(response.json())

# Rota para categorias
@app.route('/categories/<site_id>', methods=['GET'])
def get_categories(site_id='MLB'):
    """
    Obtém as categorias do Mercado Livre
    """
    url = f"{ML_API_BASE_URL}/sites/{site_id}/categories"
    
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter categorias", "details": response.text}), 400
    
    return jsonify(response.json())

# Rota para atributos de categoria
@app.route('/categories/<category_id>/attributes', methods=['GET'])
def get_category_attributes(category_id):
    """
    Obtém os atributos de uma categoria
    """
    url = f"{ML_API_BASE_URL}/categories/{category_id}/attributes"
    
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter atributos da categoria", "details": response.text}), 400
    
    return jsonify(response.json())

# Rota para integração com Odoo
@app.route('/odoo/sync_products', methods=['POST'])
def sync_products_to_odoo():
    """
    Sincroniza produtos do Mercado Livre para o Odoo
    """
    # Esta é uma implementação de exemplo que seria expandida com a integração real com o Odoo
    access_token = session.get('ml_access_token')
    user_id = session.get('ml_user_id')
    
    if not access_token or not user_id:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    # Obter produtos do Mercado Livre
    url = f"{ML_API_BASE_URL}/users/{user_id}/items/search"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter produtos", "details": response.text}), 400
    
    products = response.json()
    
    # Aqui seria implementada a lógica para enviar os produtos para o Odoo
    # Exemplo: odoo_client.create_products(products)
    
    return jsonify({"message": "Produtos sincronizados com sucesso", "count": len(products.get('results', []))})

@app.route('/odoo/sync_orders', methods=['POST'])
def sync_orders_to_odoo():
    """
    Sincroniza pedidos do Mercado Livre para o Odoo
    """
    # Esta é uma implementação de exemplo que seria expandida com a integração real com o Odoo
    access_token = session.get('ml_access_token')
    seller_id = session.get('ml_user_id')
    
    if not access_token or not seller_id:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    # Obter pedidos do Mercado Livre
    url = f"{ML_API_BASE_URL}/orders/search"
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'seller': seller_id}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return jsonify({"error": "Falha ao obter pedidos", "details": response.text}), 400
    
    orders = response.json()
    
    # Aqui seria implementada a lógica para enviar os pedidos para o Odoo
    # Exemplo: odoo_client.create_orders(orders)
    
    return jsonify({"message": "Pedidos sincronizados com sucesso", "count": len(orders.get('results', []))})

# Rota para webhooks (notificações)
@app.route('/webhooks/mercadolivre', methods=['POST'])
def mercadolivre_webhook():
    """
    Recebe notificações do Mercado Livre
    """
    notification = request.json
    
    # Aqui seria implementada a lógica para processar as notificações
    # Exemplo: processar_notificacao(notification)
    
    return jsonify({"message": "Notificação recebida com sucesso"})

# Rota para status do servidor
@app.route('/status', methods=['GET'])
def status():
    """
    Verifica o status do servidor
    """
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "authenticated": 'ml_access_token' in session
    })

# Rota para interface com agentes de IA
@app.route('/ai/analyze', methods=['POST'])
def ai_analyze():
    """
    Endpoint para análise de dados por agentes de IA
    """
    # Esta é uma implementação de exemplo que seria expandida com a integração real com agentes de IA
    data_type = request.json.get('type')
    period = request.json.get('period', '30d')
    
    if data_type == 'sales':
        # Análise de vendas
        return jsonify({
            "message": "Análise de vendas realizada com sucesso",
            "insights": [
                "As vendas aumentaram 15% no último mês",
                "Produtos da categoria X têm melhor desempenho",
                "Recomenda-se ajustar preços dos produtos Y"
            ]
        })
    elif data_type == 'performance':
        # Análise de desempenho
        return jsonify({
            "message": "Análise de desempenho realizada com sucesso",
            "insights": [
                "Taxa de conversão média de 3.2%",
                "Tempo médio de resposta: 4 horas",
                "Satisfação do cliente: 4.7/5.0"
            ]
        })
    else:
        return jsonify({"error": "Tipo de análise não suportado"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
