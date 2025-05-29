# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class OrderMapping(models.Model):
    _name = 'odoo.integration.order.mapping'
    _description = 'Mapeamento de Pedido'
    
    connector_id = fields.Many2one('odoo.integration.connector', string='Conector', required=True, ondelete='cascade')
    order_id = fields.Many2one('sale.order', string='Pedido Odoo', required=True, ondelete='cascade')
    external_id = fields.Char(string='ID Externo', required=True)
    external_url = fields.Char(string='URL Externa')
    
    last_sync = fields.Datetime(string='Última Sincronização')
    last_sync_status = fields.Selection([
        ('success', 'Sucesso'),
        ('error', 'Erro'),
    ], string='Status da Última Sincronização')
    
    _sql_constraints = [
        ('unique_order_connector', 'unique(order_id, connector_id)', 'Já existe um mapeamento para este pedido e conector'),
        ('unique_external_id_connector', 'unique(external_id, connector_id)', 'Já existe um mapeamento para este ID externo e conector'),
    ]

class MessageMapping(models.Model):
    _name = 'odoo.integration.message.mapping'
    _description = 'Mapeamento de Mensagem'
    
    connector_id = fields.Many2one('odoo.integration.connector', string='Conector', required=True, ondelete='cascade')
    message_id = fields.Many2one('mail.message', string='Mensagem Odoo', required=True, ondelete='cascade')
    external_id = fields.Char(string='ID Externo', required=True)
    external_url = fields.Char(string='URL Externa')
    
    product_mapping_id = fields.Many2one('odoo.integration.product.mapping', string='Produto Relacionado')
    order_mapping_id = fields.Many2one('odoo.integration.order.mapping', string='Pedido Relacionado')
    
    last_sync = fields.Datetime(string='Última Sincronização')
    last_sync_status = fields.Selection([
        ('success', 'Sucesso'),
        ('error', 'Erro'),
    ], string='Status da Última Sincronização')
    
    _sql_constraints = [
        ('unique_message_connector', 'unique(message_id, connector_id)', 'Já existe um mapeamento para esta mensagem e conector'),
        ('unique_external_id_connector', 'unique(external_id, connector_id)', 'Já existe um mapeamento para este ID externo e conector'),
    ]

class OrderSynchronizer(models.Model):
    _inherit = 'odoo.integration.synchronizer'
    
    def _sync_orders(self):
        """
        Sincroniza pedidos.
        """
        try:
            if self.direction in ['odoo_to_mcp', 'bidirectional']:
                self._sync_orders_to_mcp()
                
            if self.direction in ['mcp_to_odoo', 'bidirectional']:
                self._sync_orders_from_mcp()
                
            return {'success': True, 'message': _("Pedidos sincronizados com sucesso")}
        except Exception as e:
            _logger.error("Erro ao sincronizar pedidos: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    def _sync_orders_to_mcp(self):
        """
        Sincroniza pedidos do Odoo para o MCP.
        """
        # Implementação para sincronizar pedidos do Odoo para o MCP
        orders = self.env['sale.order'].search(eval(self.filter_domain) if self.filter_domain else [])
        
        _logger.info("Sincronizando %d pedidos para o MCP", len(orders))
        
        for order in orders:
            # Verifica se já existe mapeamento
            mapping = self.env['odoo.integration.order.mapping'].search([
                ('connector_id', '=', self.connector_id.id),
                ('order_id', '=', order.id),
            ], limit=1)
            
            # Prepara dados do pedido
            order_data = {
                'name': order.name,
                'date': order.date_order.isoformat(),
                'customer': {
                    'name': order.partner_id.name,
                    'email': order.partner_id.email or '',
                    'phone': order.partner_id.phone or '',
                },
                'items': [],
                'total': order.amount_total,
                'currency': order.currency_id.name,
                'state': order.state,
            }
            
            # Adiciona itens do pedido
            for line in order.order_line:
                # Busca mapeamento do produto
                product_mapping = self.env['odoo.integration.product.mapping'].search([
                    ('connector_id', '=', self.connector_id.id),
                    ('product_id', '=', line.product_id.id),
                ], limit=1)
                
                if not product_mapping:
                    _logger.warning("Produto %s não mapeado para o MCP", line.product_id.name)
                    continue
                
                order_data['items'].append({
                    'product_id': product_mapping.external_id,
                    'name': line.name,
                    'quantity': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'subtotal': line.price_subtotal,
                })
            
            if mapping:
                # Atualiza pedido existente
                result = self.connector_id.send_request({
                    'action': 'update_order',
                    'external_id': mapping.external_id,
                    'data': order_data,
                })
                
                mapping.write({
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                })
            else:
                # Cria novo pedido
                result = self.connector_id.send_request({
                    'action': 'create_order',
                    'data': order_data,
                })
                
                # Cria mapeamento
                self.env['odoo.integration.order.mapping'].create({
                    'connector_id': self.connector_id.id,
                    'order_id': order.id,
                    'external_id': result.get('external_id'),
                    'external_url': result.get('external_url'),
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                })
    
    def _sync_orders_from_mcp(self):
        """
        Sincroniza pedidos do MCP para o Odoo.
        """
        # Implementação para sincronizar pedidos do MCP para o Odoo
        result = self.connector_id.send_request({
            'action': 'get_orders',
            'filter': {},
        })
        
        orders = result.get('orders', [])
        _logger.info("Recebidos %d pedidos do MCP", len(orders))
        
        for order_data in orders:
            external_id = order_data.get('id')
            
            # Verifica se já existe mapeamento
            mapping = self.env['odoo.integration.order.mapping'].search([
                ('connector_id', '=', self.connector_id.id),
                ('external_id', '=', external_id),
            ], limit=1)
            
            if mapping:
                # Atualiza pedido existente
                order = mapping.order_id
                
                # Atualiza status do pedido
                if order.state != order_data.get('state'):
                    if order_data.get('state') == 'cancel':
                        if order.state not in ['done', 'cancel']:
                            order.action_cancel()
                    elif order_data.get('state') == 'done':
                        if order.state not in ['done', 'cancel']:
                            # Confirma e entrega
                            if order.state != 'sale':
                                order.action_confirm()
                            # Cria e valida fatura
                            # Marca como entregue
                            # Nota: Implementação simplificada
                
                mapping.write({
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                    'external_url': order_data.get('url'),
                })
            else:
                # Cria novo pedido
                try:
                    # Busca ou cria cliente
                    customer_data = order_data.get('customer', {})
                    partner = self._find_or_create_partner(customer_data)
                    
                    # Cria pedido
                    order_vals = {
                        'partner_id': partner.id,
                        'date_order': datetime.fromisoformat(order_data.get('date')),
                        'state': 'draft',
                        'order_line': [],
                    }
                    
                    # Adiciona linhas de pedido
                    for item in order_data.get('items', []):
                        # Busca produto pelo ID externo
                        product_mapping = self.env['odoo.integration.product.mapping'].search([
                            ('connector_id', '=', self.connector_id.id),
                            ('external_id', '=', item.get('product_id')),
                        ], limit=1)
                        
                        if not product_mapping:
                            _logger.warning("Produto com ID externo %s não encontrado", item.get('product_id'))
                            continue
                        
                        order_vals['order_line'].append((0, 0, {
                            'product_id': product_mapping.product_id.id,
                            'name': item.get('name'),
                            'product_uom_qty': item.get('quantity'),
                            'price_unit': item.get('price_unit'),
                            'discount': item.get('discount', 0.0),
                        }))
                    
                    # Cria o pedido
                    order = self.env['sale.order'].create(order_vals)
                    
                    # Atualiza status conforme MCP
                    if order_data.get('state') == 'confirmed':
                        order.action_confirm()
                    elif order_data.get('state') == 'cancel':
                        order.action_cancel()
                    
                    # Cria mapeamento
                    self.env['odoo.integration.order.mapping'].create({
                        'connector_id': self.connector_id.id,
                        'order_id': order.id,
                        'external_id': external_id,
                        'external_url': order_data.get('url'),
                        'last_sync': fields.Datetime.now(),
                        'last_sync_status': 'success',
                    })
                except Exception as e:
                    _logger.error("Erro ao criar pedido do MCP: %s", str(e))
    
    def _find_or_create_partner(self, customer_data):
        """
        Busca ou cria um parceiro com base nos dados do cliente.
        """
        Partner = self.env['res.partner']
        
        # Busca por email
        if customer_data.get('email'):
            partner = Partner.search([('email', '=', customer_data.get('email'))], limit=1)
            if partner:
                return partner
        
        # Busca por telefone
        if customer_data.get('phone'):
            partner = Partner.search([('phone', '=', customer_data.get('phone'))], limit=1)
            if partner:
                return partner
        
        # Busca por nome
        if customer_data.get('name'):
            partner = Partner.search([('name', '=', customer_data.get('name'))], limit=1)
            if partner:
                return partner
        
        # Cria novo parceiro
        return Partner.create({
            'name': customer_data.get('name', 'Cliente MCP'),
            'email': customer_data.get('email'),
            'phone': customer_data.get('phone'),
            'customer_rank': 1,
        })

class MessageSynchronizer(models.Model):
    _inherit = 'odoo.integration.synchronizer'
    
    def _sync_messages(self):
        """
        Sincroniza mensagens.
        """
        try:
            if self.direction in ['odoo_to_mcp', 'bidirectional']:
                self._sync_messages_to_mcp()
                
            if self.direction in ['mcp_to_odoo', 'bidirectional']:
                self._sync_messages_from_mcp()
                
            return {'success': True, 'message': _("Mensagens sincronizadas com sucesso")}
        except Exception as e:
            _logger.error("Erro ao sincronizar mensagens: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    def _sync_messages_to_mcp(self):
        """
        Sincroniza mensagens do Odoo para o MCP.
        """
        # Implementação para sincronizar mensagens do Odoo para o MCP
        # Busca mensagens relacionadas a produtos ou pedidos mapeados
        product_mappings = self.env['odoo.integration.product.mapping'].search([
            ('connector_id', '=', self.connector_id.id),
        ])
        
        order_mappings = self.env['odoo.integration.order.mapping'].search([
            ('connector_id', '=', self.connector_id.id),
        ])
        
        # Busca mensagens relacionadas a produtos
        for product_mapping in product_mappings:
            product = product_mapping.product_id
            
            # Busca mensagens relacionadas ao produto
            messages = self.env['mail.message'].search([
                ('model', '=', 'product.product'),
                ('res_id', '=', product.id),
                ('message_type', 'in', ['comment', 'email']),
            ])
            
            for message in messages:
                # Verifica se já existe mapeamento
                mapping = self.env['odoo.integration.message.mapping'].search([
                    ('connector_id', '=', self.connector_id.id),
                    ('message_id', '=', message.id),
                ], limit=1)
                
                if mapping:
                    continue  # Mensagem já sincronizada
                
                # Prepara dados da mensagem
                message_data = {
                    'type': 'product_message',
                    'product_id': product_mapping.external_id,
                    'author': message.author_id.name if message.author_id else 'Sistema',
                    'content': message.body,
                    'date': message.date.isoformat(),
                }
                
                # Envia mensagem para o MCP
                result = self.connector_id.send_request({
                    'action': 'create_message',
                    'data': message_data,
                })
                
                # Cria mapeamento
                self.env['odoo.integration.message.mapping'].create({
                    'connector_id': self.connector_id.id,
                    'message_id': message.id,
                    'external_id': result.get('external_id'),
                    'product_mapping_id': product_mapping.id,
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                })
        
        # Busca mensagens relacionadas a pedidos
        for order_mapping in order_mappings:
            order = order_mapping.order_id
            
            # Busca mensagens relacionadas ao pedido
            messages = self.env['mail.message'].search([
                ('model', '=', 'sale.order'),
                ('res_id', '=', order.id),
                ('message_type', 'in', ['comment', 'email']),
            ])
            
            for message in messages:
                # Verifica se já existe mapeamento
                mapping = self.env['odoo.integration.message.mapping'].search([
                    ('connector_id', '=', self.connector_id.id),
                    ('message_id', '=', message.id),
                ], limit=1)
                
                if mapping:
                    continue  # Mensagem já sincronizada
                
                # Prepara dados da mensagem
                message_data = {
                    'type': 'order_message',
                    'order_id': order_mapping.external_id,
                    'author': message.author_id.name if message.author_id else 'Sistema',
                    'content': message.body,
                    'date': message.date.isoformat(),
                }
                
                # Envia mensagem para o MCP
                result = self.connector_id.send_request({
                    'action': 'create_message',
                    'data': message_data,
                })
                
                # Cria mapeamento
                self.env['odoo.integration.message.mapping'].create({
                    'connector_id': self.connector_id.id,
                    'message_id': message.id,
                    'external_id': result.get('external_id'),
                    'order_mapping_id': order_mapping.id,
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                })
    
    def _sync_messages_from_mcp(self):
        """
        Sincroniza mensagens do MCP para o Odoo.
        """
        # Implementação para sincronizar mensagens do MCP para o Odoo
        result = self.connector_id.send_request({
            'action': 'get_messages',
            'filter': {},
        })
        
        messages = result.get('messages', [])
        _logger.info("Recebidas %d mensagens do MCP", len(messages))
        
        for message_data in messages:
            external_id = message_data.get('id')
            
            # Verifica se já existe mapeamento
            mapping = self.env['odoo.integration.message.mapping'].search([
                ('connector_id', '=', self.connector_id.id),
                ('external_id', '=', external_id),
            ], limit=1)
            
            if mapping:
                continue  # Mensagem já sincronizada
            
            # Determina o modelo e ID do registro relacionado
            model = None
            res_id = None
            product_mapping_id = None
            order_mapping_id = None
            
            if message_data.get('type') == 'product_message':
                # Mensagem relacionada a produto
                product_mapping = self.env['odoo.integration.product.mapping'].search([
                    ('connector_id', '=', self.connector_id.id),
                    ('external_id', '=', message_data.get('product_id')),
                ], limit=1)
                
                if not product_mapping:
                    _logger.warning("Produto com ID externo %s não encontrado", message_data.get('product_id'))
                    continue
                
                model = 'product.product'
                res_id = product_mapping.product_id.id
                product_mapping_id = product_mapping.id
                
            elif message_data.get('type') == 'order_message':
                # Mensagem relacionada a pedido
                order_mapping = self.env['odoo.integration.order.mapping'].search([
                    ('connector_id', '=', self.connector_id.id),
                    ('external_id', '=', message_data.get('order_id')),
                ], limit=1)
                
                if not order_mapping:
                    _logger.warning("Pedido com ID externo %s não encontrado", message_data.get('order_id'))
                    continue
                
                model = 'sale.order'
                res_id = order_mapping.order_id.id
                order_mapping_id = order_mapping.id
            
            if not model or not res_id:
                _logger.warning("Não foi possível determinar o modelo ou ID para a mensagem %s", external_id)
                continue
            
            # Cria a mensagem no Odoo
            message = self.env['mail.message'].create({
                'model': model,
                'res_id': res_id,
                'body': message_data.get('content'),
                'message_type': 'comment',
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'date': datetime.fromisoformat(message_data.get('date')),
                'email_from': message_data.get('author'),
            })
            
            # Cria mapeamento
            self.env['odoo.integration.message.mapping'].create({
                'connector_id': self.connector_id.id,
                'message_id': message.id,
                'external_id': external_id,
                'product_mapping_id': product_mapping_id,
                'order_mapping_id': order_mapping_id,
                'last_sync': fields.Datetime.now(),
                'last_sync_status': 'success',
            })
