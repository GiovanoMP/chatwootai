# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime

class BusinessRulesDashboard(models.TransientModel):
    _name = 'business.rules.dashboard'
    _description = 'Dashboard de Regras de Negócio'

    business_rule_id = fields.Many2one('business.rules', string='Regra de Negócio', required=True)

    active_permanent_rules_count = fields.Integer(string='Regras Permanentes Ativas', compute='_compute_rules_count')
    active_temporary_rules_count = fields.Integer(string='Promoções e Regras Temporárias Ativas', compute='_compute_rules_count')

    active_permanent_rules = fields.Many2many('business.rule.item', string='Regras de Negócio Ativas', compute='_compute_active_rules')
    active_temporary_rules = fields.Many2many('business.temporary.rule', string='Promoções e Regras Temporárias Ativas', compute='_compute_active_rules')

    last_sync_date = fields.Datetime(string='Última Sincronização', related='business_rule_id.last_sync_date')
    sync_status = fields.Selection(related='business_rule_id.sync_status', string='Status de Sincronização')

    @api.depends('business_rule_id')
    def _compute_rules_count(self):
        for record in self:
            if record.business_rule_id:
                record.active_permanent_rules_count = len(record.business_rule_id.rule_ids.filtered(lambda r: r.active))

                # Contar apenas regras temporárias ativas e dentro do período de validade
                now = fields.Datetime.now()
                active_temp_rules = record.business_rule_id.temporary_rule_ids.filtered(
                    lambda r: r.active and
                    (not r.date_start or r.date_start <= now) and
                    (not r.date_end or r.date_end >= now)
                )
                record.active_temporary_rules_count = len(active_temp_rules)
            else:
                record.active_permanent_rules_count = 0
                record.active_temporary_rules_count = 0

    @api.depends('business_rule_id')
    def _compute_active_rules(self):
        for record in self:
            if record.business_rule_id:
                # Regras permanentes ativas
                record.active_permanent_rules = record.business_rule_id.rule_ids.filtered(lambda r: r.active).ids

                # Regras temporárias ativas e dentro do período de validade
                now = fields.Datetime.now()
                active_temp_rules = record.business_rule_id.temporary_rule_ids.filtered(
                    lambda r: r.active and
                    (not r.date_start or r.date_start <= now) and
                    (not r.date_end or r.date_end >= now)
                )
                record.active_temporary_rules = active_temp_rules.ids
            else:
                record.active_permanent_rules = []
                record.active_temporary_rules = []
