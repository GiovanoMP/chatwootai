# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class BusinessRuleItem(models.Model):
    _name = 'business.rule.item'
    _description = 'Regra de Negócio'
    _order = 'id'

    name = fields.Char(string='Nome da Regra', required=True)
    description = fields.Text(string='Descrição', required=True)
    business_rule_id = fields.Many2one('business.rules', string='Regra de Negócio', required=True, ondelete='cascade')

    # Campo de prioridade removido conforme solicitado

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

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização da regra principal"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'description', 'rule_type', 'active'
        ]

        result = super(BusinessRuleItem, self).write(vals)

        # Verificar se algum campo relevante foi alterado
        if any(field in vals for field in sync_fields):
            # Atualizar o status de sincronização da regra principal
            for record in self:
                if record.business_rule_id and record.business_rule_id.sync_status == 'synced':
                    record.business_rule_id.write({'sync_status': 'not_synced'})

        return result

    def toggle_active(self):
        """Alternar o status ativo/inativo da regra"""
        for record in self:
            record.active = not record.active
