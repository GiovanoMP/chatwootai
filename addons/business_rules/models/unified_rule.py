from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class UnifiedRule(models.Model):
    _name = 'business.unified.rule'
    _description = 'Regra de Negócio Unificada'
    _order = 'sequence, id'

    name = fields.Char('Nome', required=True)
    business_rule_id = fields.Many2one('business.rules', 'Regra de Negócio', required=True, ondelete='cascade')
    rule_type = fields.Selection([
        ('pricing', 'Preços e Descontos'),
        ('shipping', 'Envio e Entrega'),
        ('payment', 'Pagamento'),
        ('return', 'Trocas e Devoluções'),
        ('warranty', 'Garantia'),
        ('stock', 'Estoque'),
        ('other', 'Outro'),
    ], string='Tipo de Regra', required=True, default='other')
    description = fields.Text('Descrição', required=True)
    sequence = fields.Integer('Sequência', default=10)
    active = fields.Boolean('Ativo', default=True)
    
    # Campos para regras temporárias
    is_temporary = fields.Boolean('É Temporário/Promoção', default=False)
    date_start = fields.Datetime('Data de Início', default=lambda self: fields.Datetime.now())
    date_end = fields.Datetime('Data de Término')
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('active', 'Ativa'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
    ], string='Status', default='draft', compute='_compute_state', store=True)
    
    # Campos para sincronização
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Sincronizando'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro'),
    ], string='Status de Sincronização', default='not_synced')
    last_sync_date = fields.Datetime('Última Sincronização')
    vector_id = fields.Char('ID no Sistema de IA', readonly=True)

    @api.depends('date_start', 'date_end', 'active', 'is_temporary')
    def _compute_state(self):
        now = fields.Datetime.now()
        for rule in self:
            if not rule.is_temporary:
                rule.state = 'active' if rule.active else 'cancelled'
                continue
                
            if not rule.active:
                rule.state = 'cancelled'
            elif rule.date_start and rule.date_end:
                if rule.date_start > now:
                    rule.state = 'draft'
                elif rule.date_end < now:
                    rule.state = 'expired'
                else:
                    rule.state = 'active'
            else:
                rule.state = 'draft'

    @api.constrains('date_start', 'date_end', 'is_temporary')
    def _check_dates(self):
        for rule in self:
            if rule.is_temporary and rule.date_start and rule.date_end and rule.date_start > rule.date_end:
                raise ValidationError(_("A data de início não pode ser posterior à data de término."))

    @api.model
    def create(self, vals):
        record = super(UnifiedRule, self).create(vals)
        # Marcar a regra de negócio como não sincronizada
        if record.business_rule_id:
            record.business_rule_id.write({'sync_status': 'not_synced'})
        return record

    def write(self, vals):
        result = super(UnifiedRule, self).write(vals)
        # Marcar a regra de negócio como não sincronizada
        for record in self:
            if record.business_rule_id:
                record.business_rule_id.write({'sync_status': 'not_synced'})
        return result

    def unlink(self):
        business_rules = self.mapped('business_rule_id')
        result = super(UnifiedRule, self).unlink()
        # Marcar a regra de negócio como não sincronizada
        for rule in business_rules:
            rule.write({'sync_status': 'not_synced'})
        return result
