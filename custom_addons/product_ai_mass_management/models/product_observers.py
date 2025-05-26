# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplateObserver(models.Model):
    _inherit = 'product.template'
    
    # Observador para criação de produtos
    @api.model_create_multi
    def create(self, vals_list):
        # Criar os produtos normalmente
        products = super(ProductTemplateObserver, self).create(vals_list)
        
        # Sincronizar automaticamente com o sistema de gestão
        for product in products:
            self.env['product.stock.integration'].auto_sync_new_products(product)
        
        return products
    
    # Observador para alterações em produtos
    def write(self, vals):
        # Verificar se há alterações relevantes para sincronização
        sync_fields = ['name', 'list_price', 'standard_price', 'description', 'description_sale', 'active']
        needs_sync = any(field in vals for field in sync_fields)
        
        # Realizar a escrita normalmente
        result = super(ProductTemplateObserver, self).write(vals)
        
        # Se houver alterações relevantes, atualizar os mapeamentos de canal
        if needs_sync:
            for product in self:
                for mapping in product.channel_mapping_ids:
                    # Se o preço do produto foi alterado e o mapeamento não usa preço específico
                    if 'list_price' in vals and not mapping.use_specific_price:
                        mapping.specific_price = product.list_price
                    
                    # Marcar para sincronização
                    mapping.sync_status = 'needs_update'
                    
                    # Registrar a alteração
                    _logger.info(f"Produto {product.id} - {product.name} marcado para sincronização devido a alterações")
        
        return result
    
    # Método para sincronizar automaticamente com o sistema de IA
    def auto_sync_with_ai(self):
        """Sincroniza automaticamente com o sistema de IA."""
        for product in self:
            try:
                # Verificar se o produto tem canal de IA
                ai_channel = self.env['product.sales.channel'].search([('code', '=', 'ai_system')], limit=1)
                if not ai_channel:
                    continue
                
                # Verificar se o produto tem mapeamento para o canal de IA
                mapping = self.env['product.channel.mapping'].search([
                    ('product_id', '=', product.id),
                    ('channel_id', '=', ai_channel.id)
                ], limit=1)
                
                if not mapping:
                    continue
                
                # Se o mapeamento precisa de atualização, sincronizar
                if mapping.sync_status in ['not_synced', 'needs_update']:
                    # Usar o método de sincronização do mapeamento
                    mapping.sync_with_channel()
                    
                    _logger.info(f"Produto {product.id} - {product.name} sincronizado automaticamente com o sistema de IA")
            
            except Exception as e:
                _logger.error(f"Erro ao sincronizar automaticamente produto {product.id} - {product.name} com IA: {str(e)}")
        
        return True
