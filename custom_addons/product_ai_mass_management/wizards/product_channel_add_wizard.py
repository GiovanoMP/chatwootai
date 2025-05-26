# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductChannelAddWizard(models.TransientModel):
    _name = 'product.channel.add.wizard'
    _description = 'Assistente para Adicionar Produtos a Canais'

    product_ids = fields.Many2many(
        'product.template',
        string='Produtos',
        required=True
    )
    
    channel_id = fields.Many2one(
        'product.sales.channel',
        string='Canal de Vendas',
        required=True
    )
    
    price_option = fields.Selection([
        ('standard', 'Usar Preço Padrão'),
        ('multiplier', 'Aplicar Multiplicador'),
        ('fixed', 'Definir Preço Específico')
    ], string='Opção de Preço', default='standard', required=True)
    
    price_multiplier = fields.Float(
        string='Multiplicador',
        default=1.0,
        help='Multiplicador a ser aplicado ao preço padrão'
    )
    
    fixed_price = fields.Float(
        string='Preço Específico',
        digits='Product Price',
        help='Preço específico a ser usado para todos os produtos'
    )
    
    auto_sync = fields.Boolean(
        string='Sincronizar Automaticamente',
        default=True,
        help='Sincronizar produtos com o canal após adicionar'
    )
    
    def action_add_to_channel(self):
        """Adiciona os produtos selecionados ao canal."""
        self.ensure_one()
        
        if not self.product_ids:
            raise UserError(_('Selecione pelo menos um produto para adicionar ao canal.'))
        
        # Contador para notificação
        success_count = 0
        error_count = 0
        
        for product in self.product_ids:
            try:
                # Verificar se já existe mapeamento para este canal
                existing = self.env['product.channel.mapping'].search([
                    ('product_id', '=', product.id),
                    ('channel_id', '=', self.channel_id.id)
                ], limit=1)
                
                if existing:
                    # Atualizar mapeamento existente
                    self._update_channel_mapping(existing, product)
                    _logger.info(f"Mapeamento atualizado para produto {product.name} no canal {self.channel_id.name}")
                else:
                    # Criar novo mapeamento
                    self._create_channel_mapping(product)
                    _logger.info(f"Produto {product.name} adicionado ao canal {self.channel_id.name}")
                
                success_count += 1
            except Exception as e:
                _logger.error(f"Erro ao adicionar produto {product.name} ao canal {self.channel_id.name}: {str(e)}")
                error_count += 1
        
        # Sincronizar se solicitado
        if self.auto_sync and success_count > 0:
            self._sync_products_with_channel()
        
        # Mensagem de resultado
        message = f'{success_count} produtos adicionados ao canal {self.channel_id.name}.'
        if error_count > 0:
            message += f' {error_count} produtos com erro.'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Adição ao Canal Concluída',
                'message': message,
                'sticky': False,
                'type': 'success' if error_count == 0 else 'warning'
            }
        }
    
    def _create_channel_mapping(self, product):
        """Cria um novo mapeamento de canal para o produto."""
        # Calcular preço específico conforme opção selecionada
        specific_price = self._calculate_specific_price(product)
        
        # Criar mapeamento
        self.env['product.channel.mapping'].create({
            'product_id': product.id,
            'channel_id': self.channel_id.id,
            'specific_price': specific_price,
            'use_specific_price': self.price_option != 'standard',
            'sync_status': 'not_synced'
        })
    
    def _update_channel_mapping(self, mapping, product):
        """Atualiza um mapeamento de canal existente."""
        # Calcular preço específico conforme opção selecionada
        specific_price = self._calculate_specific_price(product)
        
        # Atualizar mapeamento
        mapping.write({
            'specific_price': specific_price,
            'use_specific_price': self.price_option != 'standard',
            'sync_status': 'needs_update'
        })
    
    def _calculate_specific_price(self, product):
        """Calcula o preço específico para o produto conforme a opção selecionada."""
        if self.price_option == 'standard':
            return product.list_price
        elif self.price_option == 'multiplier':
            return product.list_price * self.price_multiplier
        elif self.price_option == 'fixed':
            return self.fixed_price
        return product.list_price
    
    def _sync_products_with_channel(self):
        """Sincroniza os produtos adicionados com o canal."""
        mappings = self.env['product.channel.mapping'].search([
            ('product_id', 'in', self.product_ids.ids),
            ('channel_id', '=', self.channel_id.id)
        ])
        
        for mapping in mappings:
            try:
                mapping.sync_with_channel()
            except Exception as e:
                _logger.error(f"Erro ao sincronizar produto {mapping.product_id.name}: {str(e)}")
