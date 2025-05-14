# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date

class BusinessTemporaryRule(models.Model):
    _name = 'business.temporary.rule'
    _description = 'Regra Temporária'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Nome da Regra', required=True, tracking=True)
    description = fields.Text(string='Descrição', required=True, tracking=True)
    business_rule_id = fields.Many2one('business.rules', string='Regra de Negócio', required=True, ondelete='cascade')

    rule_type = fields.Selection([
        ('promotion', 'Promoção'),
        ('discount', 'Desconto'),
        ('seasonal', 'Sazonal'),
        ('event', 'Evento'),
        ('holiday', 'Feriado'),
        ('other', 'Outro')
    ], string='Tipo de Regra', default='promotion', required=True, tracking=True)

    # Datas de validade
    date_start = fields.Date(string='Data de Início', required=True, tracking=True)
    date_end = fields.Date(string='Data de Término', required=True, tracking=True)
    
    # Estado da regra
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('active', 'Ativa'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada')
    ], string='Estado', compute='_compute_state', store=True, tracking=True)
    
    active = fields.Boolean(default=True, string='Ativo', tracking=True)
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, esta regra será incluída no sistema de IA',
                                  tracking=True)

    @api.depends('date_start', 'date_end', 'active')
    def _compute_state(self):
        """Calcular o estado da regra com base nas datas"""
        today = date.today()
        for record in self:
            if not record.active:
                record.state = 'cancelled'
            elif record.date_start and record.date_end:
                if record.date_start > today:
                    record.state = 'draft'
                elif record.date_end < today:
                    record.state = 'expired'
                else:
                    record.state = 'active'
            else:
                record.state = 'draft'

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização da regra principal"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'description', 'rule_type', 'date_start', 'date_end', 
            'active', 'visible_in_ai'
        ]

        result = super(BusinessTemporaryRule, self).write(vals)

        # Verificar se algum campo relevante foi alterado
        if any(field in vals for field in sync_fields):
            # Atualizar a data da última sincronização da regra principal
            for record in self:
                if record.business_rule_id:
                    record.business_rule_id.write({
                        'last_sync_date': False,
                        'sync_status': 'not_synced'
                    })

        return result

    def toggle_active(self):
        """Alternar o status ativo/inativo da regra"""
        for record in self:
            record.active = not record.active
