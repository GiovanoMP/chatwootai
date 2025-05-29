# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class MarketplaceAttribute(models.Model):
    _name = 'product.marketplace.attribute'
    _description = 'Atributo de Marketplace'
    
    name = fields.Char(
        string='Nome',
        required=True,
        help='Nome do atributo'
    )
    
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        required=True,
        ondelete='cascade',
        help='Marketplace ao qual este atributo pertence'
    )
    
    attribute_code = fields.Char(
        string='Código do Atributo',
        required=True,
        help='Código do atributo no marketplace'
    )
    
    is_required = fields.Boolean(
        string='Obrigatório',
        default=False,
        help='Indica se este atributo é obrigatório para publicação'
    )
    
    odoo_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo Odoo',
        domain=[('model', 'in', ['product.template', 'product.product'])],
        help='Campo do Odoo que corresponde a este atributo'
    )
    
    default_value = fields.Char(
        string='Valor Padrão',
        help='Valor padrão para este atributo quando não mapeado'
    )
    
    validation_regex = fields.Char(
        string='Regex de Validação',
        help='Expressão regular para validar o valor do atributo'
    )
    
    description = fields.Text(
        string='Descrição',
        help='Descrição detalhada deste atributo'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        related='marketplace_id.company_id',
        store=True,
        readonly=True,
        help='Empresa à qual este atributo pertence'
    )
    
    @api.constrains('attribute_code', 'marketplace_id')
    def _check_unique_attribute(self):
        for record in self:
            if self.search_count([
                ('attribute_code', '=', record.attribute_code),
                ('marketplace_id', '=', record.marketplace_id.id),
                ('id', '!=', record.id)
            ]):
                raise ValidationError(_("Já existe um atributo com este código para este marketplace"))
