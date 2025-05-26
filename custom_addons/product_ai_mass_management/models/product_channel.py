# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ProductSalesChannel(models.Model):
    _name = 'product.sales.channel'
    _description = 'Canal de Vendas de Produtos'
    _order = 'sequence, name'

    name = fields.Char(string='Nome do Canal', required=True)
    code = fields.Char(string='Código', required=True)
    sequence = fields.Integer(string='Sequência', default=10)
    active = fields.Boolean(string='Ativo', default=True)
    description = fields.Text(string='Descrição')
    
    # Configurações do canal
    price_multiplier = fields.Float(
        string='Multiplicador de Preço Padrão', 
        default=1.0,
        help='Multiplicador aplicado ao preço base do produto para este canal'
    )
    
    auto_sync = fields.Boolean(
        string='Sincronização Automática', 
        default=True,
        help='Sincronizar automaticamente produtos com este canal quando houver alterações'
    )
    
    product_count = fields.Integer(
        string='Produtos no Canal',
        compute='_compute_product_count'
    )
    
    color = fields.Integer(string='Cor', default=0)
    
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'O código do canal deve ser único!')
    ]
    
    @api.depends()
    def _compute_product_count(self):
        for channel in self:
            channel.product_count = self.env['product.channel.mapping'].search_count([
                ('channel_id', '=', channel.id)
            ])
    
    def action_view_products(self):
        self.ensure_one()
        return {
            'name': f'Produtos em {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [('channel_ids', 'in', self.id)],
            'context': {'default_channel_ids': [(4, self.id)]},
        }
