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

    is_temporary = fields.Boolean(string='Promoção/Regra Temporária', default=False,
                                help='Se marcado, esta é uma regra temporária ou promoção com período de validade definido.')
    rule_type_display = fields.Char(string='Tipo de Regra', compute='_compute_rule_type_display', store=True)

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
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, esta regra será incluída no sistema de IA')
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

    # Status de sincronização com o sistema de IA
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro na Sincronização')
    ], string='Status de Sincronização', default='not_synced', readonly=True)

    @api.depends('active', 'date_start', 'date_end', 'is_temporary')
    def _compute_state(self):
        now = fields.Datetime.now()
        for rule in self:
            if not rule.active:
                rule.state = 'cancelled'
            elif not rule.is_temporary:
                rule.state = 'active'
            elif rule.date_end and rule.date_end < now:
                rule.state = 'expired'
            elif not rule.date_start or rule.date_start <= now:
                rule.state = 'active'
            else:
                rule.state = 'draft'

    @api.depends('is_temporary', 'rule_type')
    def _compute_rule_type_display(self):
        for rule in self:
            if rule.is_temporary:
                rule.rule_type_display = dict(self._fields['rule_type'].selection).get(rule.rule_type, '') + ' (Temporária)'
            else:
                rule.rule_type_display = dict(self._fields['rule_type'].selection).get(rule.rule_type, '') + ' (Permanente)'

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização da regra principal"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'description', 'rule_type', 'active', 'date_start', 'date_end', 'is_temporary', 'visible_in_ai'
        ]

        result = super(BusinessTemporaryRule, self).write(vals)

        # Se a regra está sendo marcada como não disponível no IA, marcar para sincronização
        if 'visible_in_ai' in vals and vals['visible_in_ai'] is False:
            # Atualizar o status de sincronização da regra principal
            for record in self:
                if record.business_rule_id:
                    record.business_rule_id.write({'sync_status': 'not_synced'})

        # Verificar se algum campo relevante foi alterado
        elif any(field in vals for field in sync_fields):
            # Atualizar o status de sincronização da regra principal
            for record in self:
                if record.business_rule_id and record.business_rule_id.sync_status == 'synced':
                    record.business_rule_id.write({'sync_status': 'not_synced'})

        return result

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
        """Ao criar uma regra, verificar se é temporária e se a data de término está definida"""
        # Verificar se é uma regra temporária
        is_temporary = vals.get('is_temporary', True)

        if is_temporary and not vals.get('date_end'):
            # Se for temporária e não houver data de término, definir como 7 dias a partir da data de início
            start_date = vals.get('date_start') or fields.Datetime.now()
            if isinstance(start_date, str):
                start_date = fields.Datetime.from_string(start_date)
            vals['date_end'] = fields.Datetime.to_string(start_date + timedelta(days=7))

        # Se não for temporária, remover as datas
        if not is_temporary:
            vals.pop('date_start', None)
            vals.pop('date_end', None)

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
