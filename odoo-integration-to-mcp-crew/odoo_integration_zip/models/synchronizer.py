# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class MCPSynchronizer(models.Model):
    _name = 'odoo.integration.synchronizer'
    _description = 'Sincronizador MCP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(required=True, tracking=True)
    connector_id = fields.Many2one('odoo.integration.connector', string='Conector MCP', required=True, tracking=True)
    sync_type = fields.Selection([
        ('products', 'Produtos'),
        ('orders', 'Pedidos'),
        ('messages', 'Mensagens'),
        ('inventory', 'Estoque'),
    ], required=True, tracking=True)
    
    # Configurações
    direction = fields.Selection([
        ('odoo_to_mcp', 'Odoo para MCP'),
        ('mcp_to_odoo', 'MCP para Odoo'),
        ('bidirectional', 'Bidirecional'),
    ], default='bidirectional', required=True, tracking=True)
    
    auto_sync = fields.Boolean(string='Sincronização Automática', default=True, tracking=True)
    sync_interval = fields.Integer(string="Intervalo de Sincronização (minutos)", default=60, tracking=True)
    last_sync = fields.Datetime(string='Última Sincronização', tracking=True)
    next_sync = fields.Datetime(string='Próxima Sincronização', compute='_compute_next_sync', store=True)
    
    # Filtros
    filter_domain = fields.Char(string="Domínio de Filtro")
    
    # Estatísticas
    sync_count = fields.Integer(string='Total de Sincronizações', default=0)
    success_count = fields.Integer(string='Sincronizações com Sucesso', default=0)
    error_count = fields.Integer(string='Sincronizações com Erro', default=0)
    
    # Relações
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)
    
    @api.depends('last_sync', 'sync_interval', 'auto_sync')
    def _compute_next_sync(self):
        for record in self:
            if record.last_sync and record.auto_sync:
                record.next_sync = record.last_sync + timedelta(minutes=record.sync_interval)
            else:
                record.next_sync = False
    
    def sync_now(self):
        """
        Executa sincronização imediatamente.
        """
        self.ensure_one()
        
        # Verifica se o conector está ativo
        if not self.connector_id.active or self.connector_id.state != 'connected':
            raise ValidationError(_("O conector não está ativo ou conectado"))
        
        # Determina método de sincronização
        if self.sync_type == 'products':
            result = self._sync_products()
        elif self.sync_type == 'orders':
            result = self._sync_orders()
        elif self.sync_type == 'messages':
            result = self._sync_messages()
        elif self.sync_type == 'inventory':
            result = self._sync_inventory()
        else:
            raise ValidationError(_("Tipo de sincronização desconhecido: %s") % self.sync_type)
        
        # Atualiza estatísticas
        vals = {
            'last_sync': fields.Datetime.now(),
            'sync_count': self.sync_count + 1,
        }
        
        if result.get('success', False):
            vals['success_count'] = self.success_count + 1
            self.message_post(body=_("Sincronização concluída com sucesso: %s") % result.get('message', ''))
        else:
            vals['error_count'] = self.error_count + 1
            self.message_post(body=_("Erro na sincronização: %s") % result.get('error', ''))
            
        self.write(vals)
        
        return result
    
    def _sync_products(self):
        """
        Sincroniza produtos.
        """
        try:
            if self.direction in ['odoo_to_mcp', 'bidirectional']:
                self._sync_products_to_mcp()
                
            if self.direction in ['mcp_to_odoo', 'bidirectional']:
                self._sync_products_from_mcp()
                
            return {'success': True, 'message': _("Produtos sincronizados com sucesso")}
        except Exception as e:
            _logger.error("Erro ao sincronizar produtos: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    def _sync_products_to_mcp(self):
        """
        Sincroniza produtos do Odoo para o MCP.
        """
        # Implementação básica para demonstração
        products = self.env['product.product'].search(eval(self.filter_domain) if self.filter_domain else [])
        
        _logger.info("Sincronizando %d produtos para o MCP", len(products))
        
        for product in products:
            # Verifica se já existe mapeamento
            mapping = self.env['odoo.integration.product.mapping'].search([
                ('connector_id', '=', self.connector_id.id),
                ('product_id', '=', product.id),
            ], limit=1)
            
            # Prepara dados do produto
            product_data = {
                'name': product.name,
                'description': product.description or '',
                'price': product.list_price,
                'currency': product.currency_id.name,
                'sku': product.default_code or '',
                'barcode': product.barcode or '',
                'weight': product.weight,
                'image_url': product.image_1920 and f'/web/image/product.product/{product.id}/image_1920' or '',
                'category': product.categ_id.name,
                'type': product.type,
                'active': product.active,
            }
            
            if mapping:
                # Atualiza produto existente
                result = self.connector_id.send_request({
                    'action': 'update_product',
                    'external_id': mapping.external_id,
                    'data': product_data,
                })
                
                mapping.write({
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                })
            else:
                # Cria novo produto
                result = self.connector_id.send_request({
                    'action': 'create_product',
                    'data': product_data,
                })
                
                # Cria mapeamento
                self.env['odoo.integration.product.mapping'].create({
                    'connector_id': self.connector_id.id,
                    'product_id': product.id,
                    'external_id': result.get('external_id'),
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                })
    
    def _sync_products_from_mcp(self):
        """
        Sincroniza produtos do MCP para o Odoo.
        """
        # Implementação básica para demonstração
        result = self.connector_id.send_request({
            'action': 'get_products',
            'filter': {},
        })
        
        products = result.get('products', [])
        _logger.info("Recebidos %d produtos do MCP", len(products))
        
        for product_data in products:
            external_id = product_data.get('id')
            
            # Verifica se já existe mapeamento
            mapping = self.env['odoo.integration.product.mapping'].search([
                ('connector_id', '=', self.connector_id.id),
                ('external_id', '=', external_id),
            ], limit=1)
            
            if mapping:
                # Atualiza produto existente
                product = mapping.product_id
                
                product.write({
                    'name': product_data.get('name'),
                    'description': product_data.get('description'),
                    'list_price': product_data.get('price'),
                    'default_code': product_data.get('sku'),
                    'barcode': product_data.get('barcode'),
                    'weight': product_data.get('weight'),
                    'active': product_data.get('active', True),
                })
                
                mapping.write({
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                })
            else:
                # Cria novo produto
                category = self.env['product.category'].search([('name', '=', product_data.get('category'))], limit=1)
                if not category:
                    category = self.env.ref('product.product_category_all')
                
                product = self.env['product.product'].create({
                    'name': product_data.get('name'),
                    'description': product_data.get('description'),
                    'list_price': product_data.get('price'),
                    'default_code': product_data.get('sku'),
                    'barcode': product_data.get('barcode'),
                    'weight': product_data.get('weight'),
                    'categ_id': category.id,
                    'type': 'product',
                    'active': product_data.get('active', True),
                })
                
                # Cria mapeamento
                self.env['odoo.integration.product.mapping'].create({
                    'connector_id': self.connector_id.id,
                    'product_id': product.id,
                    'external_id': external_id,
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                })
    
    def _sync_orders(self):
        """
        Sincroniza pedidos.
        """
        # Implementação básica
        return {'success': True, 'message': _("Sincronização de pedidos será implementada em breve")}
    
    def _sync_messages(self):
        """
        Sincroniza mensagens.
        """
        # Implementação básica
        return {'success': True, 'message': _("Sincronização de mensagens será implementada em breve")}
    
    def _sync_inventory(self):
        """
        Sincroniza estoque.
        """
        # Implementação básica
        return {'success': True, 'message': _("Sincronização de estoque será implementada em breve")}


class ProductMapping(models.Model):
    _name = 'odoo.integration.product.mapping'
    _description = 'Mapeamento de Produto'
    
    connector_id = fields.Many2one('odoo.integration.connector', string='Conector', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Produto Odoo', required=True, ondelete='cascade')
    external_id = fields.Char(string='ID Externo', required=True)
    external_url = fields.Char(string='URL Externa')
    
    last_sync = fields.Datetime(string='Última Sincronização')
    last_sync_status = fields.Selection([
        ('success', 'Sucesso'),
        ('error', 'Erro'),
    ], string='Status da Última Sincronização')
    
    _sql_constraints = [
        ('unique_product_connector', 'unique(product_id, connector_id)', 'Já existe um mapeamento para este produto e conector'),
        ('unique_external_id_connector', 'unique(external_id, connector_id)', 'Já existe um mapeamento para este ID externo e conector'),
    ]
