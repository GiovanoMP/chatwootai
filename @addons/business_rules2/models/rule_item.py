# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class BusinessRuleItem2(models.Model):
    _name = 'business.rule.item2'
    _description = 'Regra de Negócio'
    _order = 'id'

    name = fields.Char(string='Nome da Regra', required=True)
    description = fields.Text(string='Descrição', required=True)
    business_rule_id = fields.Many2one('business.rules2', string='Regra de Negócio', required=True, ondelete='cascade')

    rule_type = fields.Selection([
        ('general', 'Geral'),
        ('product', 'Produto'),
        ('service', 'Serviço'),
        ('delivery', 'Entrega'),
        ('payment', 'Pagamento'),
        ('return', 'Devolução'),
        ('other', 'Outro')
    ], string='Tipo de Regra', default='general', required=True)

    active = fields.Boolean(default=True, string='Ativo')
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, esta regra será incluída no sistema de IA')

    # Campos para rastreamento
    create_date = fields.Datetime(string='Data de Criação', readonly=True)
    create_uid = fields.Many2one('res.users', string='Criado por', readonly=True)
    write_date = fields.Datetime(string='Última Atualização', readonly=True)
    write_uid = fields.Many2one('res.users', string='Atualizado por', readonly=True)

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização da regra principal"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'description', 'rule_type', 'active', 'visible_in_ai'
        ]

        result = super(BusinessRuleItem2, self).write(vals)

        # Verificar se algum campo relevante foi alterado
        if any(field in vals for field in sync_fields):
            # Atualizar a data da última sincronização da regra principal
            for record in self:
                if record.business_rule_id:
                    record.business_rule_id.write({'last_sync_date': False})

        return result

    def toggle_active(self):
        """Alternar o status ativo/inativo da regra"""
        for record in self:
            record.active = not record.active
