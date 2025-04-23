# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import base64

_logger = logging.getLogger(__name__)

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
        'business_support_doc_attachment_rel',
        'document_id',
        'attachment_id',
        string='Anexos'
    )

    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Sincronizando...'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro na Sincronização')
    ], string='Status de Sincronização', default='not_synced', tracking=True)

    last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
    vector_id = fields.Char(string='ID do Vetor', readonly=True, help='ID do vetor no banco de dados vetorial')

    active = fields.Boolean(default=True, string='Ativo')

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'document_type', 'content', 'business_rule_ids', 'active'
        ]

        # SOLUÇÃO RADICAL: Se o documento está sendo desativado, remover das regras de negócio
        if 'active' in vals and vals['active'] is False:
            _logger.warning(f"SOLUÇÃO RADICAL: Documento {self.name} (ID: {self.id}) está sendo desativado")

            # Remover este documento de todas as regras de negócio associadas
            for record in self:
                if record.business_rule_ids:
                    _logger.warning(f"SOLUÇÃO RADICAL: Removendo documento {record.name} (ID: {record.id}) de {len(record.business_rule_ids)} regras de negócio")

                    # Para cada regra de negócio, remover este documento
                    for business_rule in record.business_rule_ids:
                        # Remover apenas este documento específico
                        business_rule.write({
                            'support_document_ids': [(3, record.id)]
                        })
                        _logger.warning(f"SOLUÇÃO RADICAL: Documento removido da regra de negócio {business_rule.name} (ID: {business_rule.id})")

                        # Atualizar status de sincronização da regra de negócio
                        business_rule.write({'sync_status': 'not_synced'})

            # Definir status de sincronização como 'not_synced'
            vals['sync_status'] = 'not_synced'

        # Verificar se algum campo relevante foi alterado
        elif any(field in vals for field in sync_fields):
            # Se o status atual é 'synced', mudar para 'not_synced'
            if self.sync_status == 'synced':
                vals['sync_status'] = 'not_synced'

            # Atualizar o status de sincronização das regras de negócio associadas
            for record in self:
                for business_rule in record.business_rule_ids:
                    if business_rule.sync_status == 'synced':
                        business_rule.write({'sync_status': 'not_synced'})

        return super(BusinessSupportDocument, self).write(vals)

    def unlink(self):
        """Sobrescrever método unlink para remover o documento das regras de negócio antes de excluí-lo"""
        for record in self:
            if record.business_rule_ids:
                _logger.warning(f"SOLUÇÃO RADICAL: Removendo documento {record.name} (ID: {record.id}) de {len(record.business_rule_ids)} regras de negócio antes da exclusão")

                # Para cada regra de negócio, remover este documento
                for business_rule in record.business_rule_ids:
                    # Remover apenas este documento específico
                    business_rule.write({
                        'support_document_ids': [(3, record.id)]
                    })
                    _logger.warning(f"SOLUÇÃO RADICAL: Documento removido da regra de negócio {business_rule.name} (ID: {business_rule.id})")

                    # Atualizar status de sincronização da regra de negócio
                    business_rule.write({'sync_status': 'not_synced'})

        return super(BusinessSupportDocument, self).unlink()

    def action_sync_document(self):
        """Sincronizar documento individual com o sistema de IA"""
        self.ensure_one()

        # Atualizar status para 'sincronizando'
        self.write({'sync_status': 'syncing'})
        self.env.cr.commit()  # Commit imediato para atualizar a UI

        try:
            # Obter a primeira regra de negócio associada
            business_rule = self.business_rule_ids[0] if self.business_rule_ids else False

            if not business_rule:
                raise UserError(_("Este documento não está associado a nenhuma regra de negócio."))

            # Chamar o método de sincronização da regra de negócio
            result = business_rule._call_mcp_sync_support_docs()

            if result and result.get('success'):
                self.write({
                    'sync_status': 'synced',
                    'last_sync_date': fields.Datetime.now()
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _('Documento sincronizado com sucesso.'),
                        'sticky': False,
                        'type': 'success'
                    }
                }
            else:
                error_msg = result.get('error') if result else "Erro desconhecido"
                self.write({
                    'sync_status': 'error',
                    'last_sync_date': fields.Datetime.now()
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Falha na Sincronização'),
                        'message': error_msg,
                        'sticky': False,
                        'type': 'danger'
                    }
                }
        except Exception as e:
            _logger.error("Erro ao sincronizar documento: %s", str(e))
            self.write({
                'sync_status': 'error',
                'last_sync_date': fields.Datetime.now()
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger'
                }
            }
