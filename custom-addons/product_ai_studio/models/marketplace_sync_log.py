# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class MarketplaceSyncLog(models.Model):
    _name = 'product.marketplace.sync.log'
    _description = 'Log de Sincronização com Marketplace'
    _order = 'create_date desc'
    
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        required=True,
        ondelete='cascade',
        help='Marketplace relacionado a este log'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        ondelete='set null',
        help='Produto relacionado a esta sincronização'
    )
    
    operation = fields.Selection([
        ('create', 'Criação'),
        ('update', 'Atualização'),
        ('delete', 'Exclusão'),
        ('sync', 'Sincronização'),
        ('publish', 'Publicação'),
        ('unpublish', 'Despublicação'),
    ], string='Operação', required=True, default='sync',
       help='Tipo de operação realizada')
    
    status = fields.Selection([
        ('success', 'Sucesso'),
        ('error', 'Erro'),
        ('warning', 'Aviso'),
        ('pending', 'Pendente'),
    ], string='Status', required=True, default='pending',
       help='Status da operação')
    
    message = fields.Text(
        string='Mensagem',
        help='Mensagem detalhada sobre a operação'
    )
    
    response_data = fields.Text(
        string='Dados da Resposta',
        help='Dados brutos da resposta da API'
    )
    
    execution_time = fields.Float(
        string='Tempo de Execução (s)',
        help='Tempo de execução da operação em segundos'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        related='marketplace_id.company_id',
        store=True,
        readonly=True,
        help='Empresa à qual este log pertence'
    )
