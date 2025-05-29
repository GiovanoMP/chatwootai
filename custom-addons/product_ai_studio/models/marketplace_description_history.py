# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class MarketplaceDescriptionHistory(models.Model):
    _name = 'product.marketplace.description.history'
    _description = 'Histórico de Descrição de Marketplace'
    _order = 'create_date desc'
    
    description_id = fields.Many2one(
        'product.marketplace.description',
        string='Descrição',
        required=True,
        ondelete='cascade',
        help='Descrição relacionada'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Usuário',
        default=lambda self: self.env.user,
        help='Usuário que realizou a alteração'
    )
    
    old_state = fields.Selection([
        ('draft', 'Rascunho'),
        ('review', 'Em Revisão'),
        ('approved', 'Aprovado'),
        ('published', 'Publicado'),
        ('inactive', 'Inativo')
    ], string='Estado Anterior',
       help='Estado anterior da descrição')
    
    new_state = fields.Selection([
        ('draft', 'Rascunho'),
        ('review', 'Em Revisão'),
        ('approved', 'Aprovado'),
        ('published', 'Publicado'),
        ('inactive', 'Inativo')
    ], string='Novo Estado',
       help='Novo estado da descrição')
    
    action = fields.Selection([
        ('create', 'Criação'),
        ('update', 'Atualização'),
        ('publish', 'Publicação'),
        ('unpublish', 'Despublicação'),
        ('validate', 'Validação'),
        ('approve', 'Aprovação'),
        ('reject', 'Rejeição')
    ], string='Ação',
       help='Ação realizada')
    
    notes = fields.Text(
        string='Observações',
        help='Observações sobre esta alteração'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        related='description_id.company_id',
        store=True,
        readonly=True,
        help='Empresa à qual este histórico pertence'
    )
