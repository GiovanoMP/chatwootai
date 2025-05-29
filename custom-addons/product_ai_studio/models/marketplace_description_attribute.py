# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class MarketplaceDescriptionAttribute(models.Model):
    _name = 'product.marketplace.description.attribute'
    _description = 'Atributo de Descrição de Marketplace'
    
    description_id = fields.Many2one(
        'product.marketplace.description',
        string='Descrição',
        required=True,
        ondelete='cascade',
        help='Descrição relacionada'
    )
    
    name = fields.Char(
        string='Nome',
        required=True,
        help='Nome do atributo'
    )
    
    value = fields.Char(
        string='Valor',
        required=True,
        help='Valor do atributo'
    )
    
    is_required = fields.Boolean(
        string='Obrigatório',
        default=False,
        help='Indica se este atributo é obrigatório para o marketplace'
    )
    
    is_variant = fields.Boolean(
        string='Variante',
        default=False,
        help='Indica se este atributo é usado para variantes do produto'
    )
    
    sequence = fields.Integer(
        string='Sequência',
        default=10,
        help='Determina a ordem de exibição dos atributos'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        related='description_id.company_id',
        store=True,
        readonly=True,
        help='Empresa à qual este atributo pertence'
    )
    
    @api.constrains('name', 'description_id')
    def _check_unique_attribute(self):
        for record in self:
            if self.search_count([
                ('name', '=', record.name),
                ('description_id', '=', record.description_id.id),
                ('id', '!=', record.id)
            ]):
                raise ValidationError(_("Já existe um atributo com este nome para esta descrição"))
