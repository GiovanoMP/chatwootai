# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class MarketplaceDescriptionImage(models.Model):
    _name = 'product.marketplace.description.image'
    _description = 'Imagem de Descrição de Marketplace'
    _order = 'sequence, id'
    
    description_id = fields.Many2one(
        'product.marketplace.description',
        string='Descrição',
        required=True,
        ondelete='cascade',
        help='Descrição relacionada'
    )
    
    name = fields.Char(
        string='Nome',
        help='Nome da imagem'
    )
    
    image_1920 = fields.Binary(
        string='Imagem',
        attachment=True,
        required=True,
        help='Imagem em alta resolução'
    )
    
    image_128 = fields.Binary(
        string='Miniatura',
        attachment=True,
        help='Miniatura da imagem para exibição'
    )
    
    sequence = fields.Integer(
        string='Sequência',
        default=10,
        help='Determina a ordem de exibição das imagens'
    )
    
    marketplace_image_url = fields.Char(
        string='URL da Imagem no Marketplace',
        help='URL da imagem após publicação no marketplace'
    )
    
    is_main = fields.Boolean(
        string='Imagem Principal',
        default=False,
        help='Indica se esta é a imagem principal do produto'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        related='description_id.company_id',
        store=True,
        readonly=True,
        help='Empresa à qual esta imagem pertence'
    )
    
    @api.constrains('is_main', 'description_id')
    def _check_main_image(self):
        for record in self:
            if record.is_main and self.search_count([
                ('is_main', '=', True),
                ('description_id', '=', record.description_id.id),
                ('id', '!=', record.id)
            ]):
                raise ValidationError(_("Só pode haver uma imagem principal por descrição"))
