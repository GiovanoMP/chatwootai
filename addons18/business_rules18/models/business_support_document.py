# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class BusinessSupportDocument(models.Model):
    _name = 'business.support.document'
    _description = 'Documento de Suporte ao Cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Nome', required=True, tracking=True)
    business_rule_ids = fields.Many2many(
        'business.rules',
        'business_rule_support_doc_rel',
        'document_id',
        'business_rule_id',
        string='Regras de Negócio'
    )

    document_type = fields.Selection([
        ('support', 'Suporte Técnico'),
        ('feedback', 'Feedback'),
        ('question', 'Dúvida'),
        ('suggestion', 'Sugestão'),
        ('other', 'Outro')
    ], string='Tipo de Documento', default='support', required=True, tracking=True)

    content = fields.Text(string='Conteúdo', required=True, tracking=True)
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'business_support_document_attachment_rel',
        'document_id',
        'attachment_id',
        string='Anexos'
    )
    
    # Status de sincronização
    last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
    
    active = fields.Boolean(default=True, string='Ativo', tracking=True)
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, este documento será incluído no sistema de IA',
                                  tracking=True)

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização das regras relacionadas"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'document_type', 'content', 'active', 'visible_in_ai'
        ]

        result = super(BusinessSupportDocument, self).write(vals)

        # Verificar se algum campo relevante foi alterado
        if any(field in vals for field in sync_fields):
            # Atualizar a data da última sincronização das regras relacionadas
            for record in self:
                for rule in record.business_rule_ids:
                    rule.write({
                        'last_sync_date': False,
                        'sync_status': 'not_synced'
                    })

        return result

    def toggle_active(self):
        """Alternar o status ativo/inativo do documento"""
        for record in self:
            record.active = not record.active
