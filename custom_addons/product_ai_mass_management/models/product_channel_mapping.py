# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ProductChannelMapping(models.Model):
    _name = 'product.channel.mapping'
    _description = 'Mapeamento de Produto para Canal de Vendas'
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.template', 
        string='Produto',
        required=True,
        ondelete='cascade'
    )
    
    channel_id = fields.Many2one(
        'product.sales.channel', 
        string='Canal de Vendas',
        required=True,
        ondelete='cascade'
    )
    
    # Preço específico para este canal
    specific_price = fields.Float(
        string='Preço Específico',
        digits='Product Price'
    )
    
    price_difference = fields.Float(
        string='Diferença de Preço (%)',
        compute='_compute_price_difference',
        store=True
    )
    
    use_specific_price = fields.Boolean(
        string='Usar Preço Específico',
        default=False
    )
    
    # Status de sincronização
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Sincronizando'),
        ('synced', 'Sincronizado'),
        ('needs_update', 'Atualização Necessária')
    ], string='Status de Sincronização',
       default='not_synced'
    )
    
    last_sync = fields.Datetime(
        string='Última Sincronização',
        readonly=True
    )
    
    active = fields.Boolean(
        string='Ativo',
        default=True
    )
    
    # Estatísticas do canal
    views_count = fields.Integer(
        string='Visualizações',
        default=0,
        help='Número de visualizações deste produto no canal'
    )
    
    sales_count = fields.Integer(
        string='Vendas',
        default=0,
        help='Número de vendas deste produto no canal'
    )
    
    popularity_score = fields.Float(
        string='Popularidade',
        default=0.0,
        help='Pontuação de popularidade deste produto no canal'
    )
    
    popularity_level = fields.Selection([
        ('new', 'Novo no Canal'),
        ('low', 'Baixa Popularidade'),
        ('medium', 'Média Popularidade'),
        ('high', 'Alta Popularidade')
    ], string='Nível de Popularidade',
       compute='_compute_popularity_level',
       store=True
    )
    
    _sql_constraints = [
        ('product_channel_uniq', 'unique (product_id, channel_id)', 
         'Um produto só pode ser mapeado uma vez para cada canal!')
    ]
    
    @api.depends('product_id.list_price', 'specific_price', 'use_specific_price')
    def _compute_price_difference(self):
        for mapping in self:
            if mapping.use_specific_price and mapping.specific_price and mapping.product_id.list_price:
                mapping.price_difference = ((mapping.specific_price - mapping.product_id.list_price) / 
                                           mapping.product_id.list_price) * 100
            else:
                mapping.price_difference = 0
    
    @api.depends('popularity_score')
    def _compute_popularity_level(self):
        for mapping in self:
            if mapping.popularity_score <= 0:
                mapping.popularity_level = 'new'
            elif mapping.popularity_score < 30:
                mapping.popularity_level = 'low'
            elif mapping.popularity_score < 70:
                mapping.popularity_level = 'medium'
            else:
                mapping.popularity_level = 'high'
    
    def sync_with_channel(self):
        """Sincroniza o produto com o canal específico"""
        for mapping in self:
            try:
                # Aqui implementaríamos a lógica específica para cada canal
                # Por exemplo, para o canal de IA:
                if mapping.channel_id.code == 'ai_system':
                    product = mapping.product_id
                    # Usar o preço específico se configurado, ou calcular com o multiplicador
                    price = mapping.specific_price if mapping.use_specific_price else (
                        product.list_price * mapping.channel_id.price_multiplier
                    )
                    
                    # Chamar método de sincronização com o sistema de IA
                    # Isso depende da implementação específica do sistema de IA
                    if hasattr(product, '_call_mcp_sync_product_minimal'):
                        minimal_text = f"{product.name} - {product.categ_id.name}"
                        product._call_mcp_sync_product_minimal(product.id, minimal_text, price)
                
                # Atualizar status
                mapping.write({
                    'sync_status': 'synced',
                    'last_sync': fields.Datetime.now()
                })
                
                _logger.info(f"Produto {mapping.product_id.name} sincronizado com o canal {mapping.channel_id.name}")
                
            except Exception as e:
                mapping.sync_status = 'needs_update'
                _logger.error(f"Erro ao sincronizar produto {mapping.product_id.name} com o canal {mapping.channel_id.name}: {str(e)}")
                
        return True
