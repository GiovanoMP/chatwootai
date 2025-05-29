# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EnrichProductsWizard(models.TransientModel):
    _name = 'product.enrich.wizard'
    _description = 'Assistente de Enriquecimento de Produtos'

    product_ids = fields.Many2many(
        'product.template', 
        string='Produtos', 
        required=True,
        readonly=True
    )
    
    enrichment_profile_id = fields.Many2one(
        'product.enrichment.profile',
        string='Perfil de Enriquecimento',
        required=True,
        domain=[('active', '=', True)]
    )
    
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        domain=[('active', '=', True)]
    )
    
    create_marketplace_descriptions = fields.Boolean(
        string='Criar Descrições de Marketplace',
        default=False,
        help='Se marcado, serão criadas descrições específicas para o marketplace selecionado'
    )
    
    suggest_images = fields.Boolean(
        string='Sugerir Imagens',
        default=False,
        help='Se marcado, a IA irá sugerir imagens para os produtos'
    )
    
    vectorize_products = fields.Boolean(
        string='Vetorizar Produtos',
        default=True,
        help='Se marcado, os produtos serão vetorizados para busca semântica'
    )
    
    auto_process = fields.Boolean(
        string='Processar Automaticamente',
        default=False,
        help='Se marcado, os enriquecimentos serão processados automaticamente'
    )
    
    product_count = fields.Integer(
        string='Quantidade de Produtos',
        compute='_compute_product_count'
    )
    
    @api.depends('product_ids')
    def _compute_product_count(self):
        for wizard in self:
            wizard.product_count = len(wizard.product_ids)
    
    def action_enrich_products(self):
        self.ensure_one()
        
        if not self.product_ids:
            raise UserError(_('Nenhum produto selecionado para enriquecimento.'))
        
        if self.product_count > 50 and not self.auto_process:
            raise UserError(_('Para enriquecer mais de 50 produtos, é necessário ativar o processamento automático.'))
        
        # Criar enriquecimentos para cada produto
        enrichment_ids = []
        for product in self.product_ids:
            vals = {
                'product_id': product.id,
                'name': product.name,
                'original_name': product.name,
                'original_description': product.description_sale or '',
                'enrichment_profile_id': self.enrichment_profile_id.id,
                'marketplace_id': self.marketplace_id.id if self.marketplace_id else False,
                'create_marketplace_description': self.create_marketplace_descriptions,
                'suggest_images': self.suggest_images,
                'vectorize': self.vectorize_products,
                'state': 'draft',
            }
            
            enrichment = self.env['product.enrichment'].create(vals)
            enrichment_ids.append(enrichment.id)
            
            # Processar automaticamente se solicitado
            if self.auto_process:
                enrichment.action_process()
        
        # Retornar ação para visualizar os enriquecimentos criados
        action = {
            'name': _('Enriquecimentos Criados'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.enrichment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', enrichment_ids)],
            'context': {'create': False},
        }
        
        return action
