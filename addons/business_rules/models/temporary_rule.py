# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class BusinessTemporaryRule(models.Model):
    _name = 'business.temporary.rule'
    _description = 'Regra Temporária de Negócio'
    _order = 'date_start desc, id'

    name = fields.Char(string='Nome da Regra', required=True)
    description = fields.Text(string='Descrição', required=True)
    business_rule_id = fields.Many2one('business.rules', string='Regra de Negócio', required=True, ondelete='cascade')

    date_start = fields.Datetime(string='Data de Início', default=fields.Datetime.now)
    date_end = fields.Datetime(string='Data de Término')

    # Campo de prioridade removido conforme solicitado

    rule_type = fields.Selection([
        ('general', 'Geral'),
        ('product', 'Produto'),
        ('service', 'Serviço'),
        ('delivery', 'Entrega'),
        ('payment', 'Pagamento'),
        ('return', 'Devolução'),
        ('schedule', 'Horário'),
        ('other', 'Outro')
    ], string='Tipo de Regra', default='general', required=True)

    active = fields.Boolean(default=True, string='Ativo')
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('active', 'Ativa'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada')
    ], string='Status', default='draft', compute='_compute_state', store=True)

    # Campos para rastreamento
    create_date = fields.Datetime(string='Data de Criação', readonly=True)
    create_uid = fields.Many2one('res.users', string='Criado por', readonly=True)
    write_date = fields.Datetime(string='Última Atualização', readonly=True)
    write_uid = fields.Many2one('res.users', string='Atualizado por', readonly=True)

    @api.depends('active', 'date_start', 'date_end')
    def _compute_state(self):
        now = fields.Datetime.now()
        for rule in self:
            if not rule.active:
                rule.state = 'cancelled'
            elif rule.date_end and rule.date_end < now:
                rule.state = 'expired'
            elif not rule.date_start or rule.date_start <= now:
                rule.state = 'active'
            else:
                rule.state = 'draft'

    def toggle_active(self):
        """Alternar o status ativo/inativo da regra"""
        for record in self:
            record.active = not record.active

    def action_activate(self):
        """Ativar a regra temporária"""
        self.write({'active': True})

    def action_cancel(self):
        """Cancelar a regra temporária"""
        self.write({'active': False})

    @api.model
    def create(self, vals):
        """Ao criar uma regra temporária, verificar se a data de término está definida"""
        if not vals.get('date_end'):
            # Se não houver data de término, definir como 7 dias a partir da data de início
            start_date = vals.get('date_start') or fields.Datetime.now()
            if isinstance(start_date, str):
                start_date = fields.Datetime.from_string(start_date)
            vals['date_end'] = fields.Datetime.to_string(start_date + timedelta(days=7))

        return super(BusinessTemporaryRule, self).create(vals)

    @api.model
    def _expire_temporary_rules(self):
        """Método para ser chamado por agendador para expirar regras temporárias"""
        now = fields.Datetime.now()
        expired_rules = self.search([
            ('active', '=', True),
            ('date_end', '<', now)
        ])
        if expired_rules:
            expired_rules.write({'active': False})
            # Notificar usuários sobre regras expiradas
            for rule in expired_rules:
                self.env['mail.message'].create({
                    'model': 'business.rules',
                    'res_id': rule.business_rule_id.id,
                    'message_type': 'notification',
                    'body': _('A regra temporária "%s" expirou.') % rule.name,
                })
        return True
