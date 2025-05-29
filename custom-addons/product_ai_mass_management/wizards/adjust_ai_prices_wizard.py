# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class AdjustAIPricesWizard(models.TransientModel):
    _name = 'product.ai.price.wizard'
    _description = 'Assistente para Ajuste de Preços no Sistema de IA'

    adjustment_type = fields.Selection([
        ('percentage', 'Percentual'),
        ('fixed', 'Valor Fixo'),
        ('match', 'Igualar ao Preço Padrão')
    ], string='Tipo de Ajuste', default='percentage', required=True)
    
    percentage_value = fields.Float(
        string='Percentual (%)',
        default=0.0,
        help='Valor percentual para ajustar o preço. Use valores negativos para desconto.'
    )
    
    fixed_value = fields.Float(
        string='Valor Fixo',
        default=0.0,
        help='Valor fixo para ajustar o preço. Use valores negativos para desconto.'
    )
    
    base_price = fields.Selection([
        ('list_price', 'Preço Padrão'),
        ('ai_price', 'Preço Atual no Sistema de IA')
    ], string='Preço Base', default='list_price', required=True)

    def action_apply_adjustment(self):
        """Aplica o ajuste de preço aos produtos selecionados."""
        active_ids = self.env.context.get('active_ids', [])
        products = self.env['product.template'].browse(active_ids)
        
        # Contador para notificação
        updated_count = 0
        
        for product in products:
            try:
                # Determinar preço base
                base_price = product.list_price if self.base_price == 'list_price' else (product.ai_price or product.list_price)
                
                # Calcular novo preço
                new_price = base_price
                
                if self.adjustment_type == 'percentage':
                    new_price = base_price * (1 + (self.percentage_value / 100))
                elif self.adjustment_type == 'fixed':
                    new_price = base_price + self.fixed_value
                elif self.adjustment_type == 'match':
                    new_price = product.list_price
                
                # Garantir que o preço não seja negativo
                new_price = max(0, new_price)
                
                # Atualizar o preço
                product.write({'ai_price': new_price})
                updated_count += 1
                
            except Exception as e:
                _logger.error(f"Erro ao ajustar preço do produto {product.id} - {product.name}: {str(e)}")
        
        # Mensagem de resultado
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Ajuste de Preços Concluído',
                'message': f'{updated_count} produtos atualizados com sucesso.',
                'sticky': False,
                'type': 'success'
            }
        }
