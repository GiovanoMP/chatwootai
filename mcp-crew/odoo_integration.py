"""
Módulo para integração com o Odoo ERP.
Este módulo contém funções para comunicação com o Odoo via XML-RPC.
"""

import xmlrpc.client
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class OdooClient:
    """Cliente para comunicação com o Odoo ERP"""
    
    def __init__(self, url=None, db=None, username=None, password=None):
        """
        Inicializa o cliente Odoo com credenciais
        
        Args:
            url: URL do servidor Odoo
            db: Nome do banco de dados
            username: Nome de usuário
            password: Senha
        """
        self.url = url or os.getenv('ODOO_URL')
        self.db = db or os.getenv('ODOO_DB')
        self.username = username or os.getenv('ODOO_USERNAME')
        self.password = password or os.getenv('ODOO_PASSWORD')
        
        if not all([self.url, self.db, self.username, self.password]):
            raise ValueError("Credenciais do Odoo incompletas")
        
        # Inicializa conexões
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        
        # Autentica e obtém uid
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        
    def create_product(self, product_data):
        """
        Cria um produto no Odoo
        
        Args:
            product_data: Dicionário com dados do produto
            
        Returns:
            ID do produto criado
        """
        # Mapeia dados do Mercado Livre para o formato do Odoo
        odoo_product = {
            'name': product_data.get('title'),
            'description': product_data.get('description', ''),
            'description_sale': product_data.get('description', ''),
            'type': 'product',
            'list_price': float(product_data.get('price', 0)),
            'default_code': product_data.get('id'),
            'mercado_livre_id': product_data.get('id'),
            'mercado_livre_url': product_data.get('permalink'),
            'mercado_livre_status': product_data.get('status'),
            'mercado_livre_category_id': product_data.get('category_id'),
        }
        
        # Cria o produto no Odoo
        product_id = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.template', 'create',
            [odoo_product]
        )
        
        return product_id
    
    def update_product(self, odoo_product_id, product_data):
        """
        Atualiza um produto no Odoo
        
        Args:
            odoo_product_id: ID do produto no Odoo
            product_data: Dicionário com dados do produto
            
        Returns:
            True se atualizado com sucesso
        """
        # Mapeia dados do Mercado Livre para o formato do Odoo
        odoo_product = {
            'name': product_data.get('title'),
            'description': product_data.get('description', ''),
            'description_sale': product_data.get('description', ''),
            'list_price': float(product_data.get('price', 0)),
            'mercado_livre_status': product_data.get('status'),
        }
        
        # Atualiza o produto no Odoo
        result = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.template', 'write',
            [[odoo_product_id], odoo_product]
        )
        
        return result
    
    def get_product_by_ml_id(self, ml_product_id):
        """
        Busca um produto no Odoo pelo ID do Mercado Livre
        
        Args:
            ml_product_id: ID do produto no Mercado Livre
            
        Returns:
            Dados do produto ou None se não encontrado
        """
        product_ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.template', 'search',
            [[['mercado_livre_id', '=', ml_product_id]]]
        )
        
        if not product_ids:
            return None
        
        product_data = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.template', 'read',
            [product_ids]
        )
        
        return product_data[0] if product_data else None
    
    def create_order(self, order_data):
        """
        Cria um pedido no Odoo
        
        Args:
            order_data: Dicionário com dados do pedido
            
        Returns:
            ID do pedido criado
        """
        # Mapeia dados do Mercado Livre para o formato do Odoo
        partner_data = {
            'name': order_data.get('buyer', {}).get('nickname', 'Cliente Mercado Livre'),
            'email': order_data.get('buyer', {}).get('email', ''),
            'phone': order_data.get('buyer', {}).get('phone', {}).get('number', ''),
            'mercado_livre_id': order_data.get('buyer', {}).get('id'),
        }
        
        # Busca ou cria o parceiro
        partner_ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.partner', 'search',
            [[['mercado_livre_id', '=', partner_data['mercado_livre_id']]]]
        )
        
        if partner_ids:
            partner_id = partner_ids[0]
        else:
            partner_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'create',
                [partner_data]
            )
        
        # Cria o pedido
        order_lines = []
        for item in order_data.get('order_items', []):
            product = self.get_product_by_ml_id(item.get('item', {}).get('id'))
            if product:
                order_lines.append((0, 0, {
                    'product_id': product['id'],
                    'name': item.get('item', {}).get('title'),
                    'product_uom_qty': item.get('quantity', 1),
                    'price_unit': float(item.get('unit_price', 0)),
                }))
        
        sale_order = {
            'partner_id': partner_id,
            'date_order': order_data.get('date_created'),
            'mercado_livre_id': order_data.get('id'),
            'mercado_livre_status': order_data.get('status'),
            'order_line': order_lines,
            'note': f"Pedido do Mercado Livre #{order_data.get('id')}",
        }
        
        order_id = self.models.execute_kw(
            self.db, self.uid, self.password,
            'sale.order', 'create',
            [sale_order]
        )
        
        return order_id
    
    def update_order_status(self, odoo_order_id, ml_status):
        """
        Atualiza o status de um pedido no Odoo
        
        Args:
            odoo_order_id: ID do pedido no Odoo
            ml_status: Status do pedido no Mercado Livre
            
        Returns:
            True se atualizado com sucesso
        """
        # Mapeia status do Mercado Livre para status do Odoo
        status_mapping = {
            'confirmed': 'sale',
            'payment_required': 'draft',
            'payment_in_process': 'draft',
            'partially_paid': 'draft',
            'paid': 'sale',
            'cancelled': 'cancel',
        }
        
        odoo_status = status_mapping.get(ml_status, 'draft')
        
        result = self.models.execute_kw(
            self.db, self.uid, self.password,
            'sale.order', 'write',
            [[odoo_order_id], {'state': odoo_status, 'mercado_livre_status': ml_status}]
        )
        
        return result
    
    def get_order_by_ml_id(self, ml_order_id):
        """
        Busca um pedido no Odoo pelo ID do Mercado Livre
        
        Args:
            ml_order_id: ID do pedido no Mercado Livre
            
        Returns:
            Dados do pedido ou None se não encontrado
        """
        order_ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'sale.order', 'search',
            [[['mercado_livre_id', '=', ml_order_id]]]
        )
        
        if not order_ids:
            return None
        
        order_data = self.models.execute_kw(
            self.db, self.uid, self.password,
            'sale.order', 'read',
            [order_ids]
        )
        
        return order_data[0] if order_data else None
    
    def sync_products(self, ml_products):
        """
        Sincroniza produtos do Mercado Livre com o Odoo
        
        Args:
            ml_products: Lista de produtos do Mercado Livre
            
        Returns:
            Dicionário com estatísticas de sincronização
        """
        stats = {
            'created': 0,
            'updated': 0,
            'failed': 0,
            'total': len(ml_products)
        }
        
        for product in ml_products:
            try:
                existing_product = self.get_product_by_ml_id(product.get('id'))
                
                if existing_product:
                    # Atualiza produto existente
                    self.update_product(existing_product['id'], product)
                    stats['updated'] += 1
                else:
                    # Cria novo produto
                    self.create_product(product)
                    stats['created'] += 1
            except Exception as e:
                print(f"Erro ao sincronizar produto {product.get('id')}: {str(e)}")
                stats['failed'] += 1
        
        return stats
    
    def sync_orders(self, ml_orders):
        """
        Sincroniza pedidos do Mercado Livre com o Odoo
        
        Args:
            ml_orders: Lista de pedidos do Mercado Livre
            
        Returns:
            Dicionário com estatísticas de sincronização
        """
        stats = {
            'created': 0,
            'updated': 0,
            'failed': 0,
            'total': len(ml_orders)
        }
        
        for order in ml_orders:
            try:
                existing_order = self.get_order_by_ml_id(order.get('id'))
                
                if existing_order:
                    # Atualiza pedido existente
                    self.update_order_status(existing_order['id'], order.get('status'))
                    stats['updated'] += 1
                else:
                    # Cria novo pedido
                    self.create_order(order)
                    stats['created'] += 1
            except Exception as e:
                print(f"Erro ao sincronizar pedido {order.get('id')}: {str(e)}")
                stats['failed'] += 1
        
        return stats
