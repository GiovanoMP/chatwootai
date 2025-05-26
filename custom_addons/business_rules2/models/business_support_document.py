# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import base64

_logger = logging.getLogger(__name__)

class BusinessSupportDocument2(models.Model):
    _name = 'business.support.document2'
    _description = 'Documento de Suporte ao Cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Desativar o teste automático de 'active' para este modelo
    _active_name = None

    name = fields.Char(string='Nome', required=True, tracking=True)
    business_rule_ids = fields.Many2many(
        'business.rules2',
        'business_rule_support_doc_rel2',
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
        'business_support_doc_attachment_rel2',
        'document_id',
        'attachment_id',
        string='Anexos'
    )

    last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
    vector_id = fields.Char(string='ID do Vetor', readonly=True, help='ID do vetor no banco de dados vetorial')

    active = fields.Boolean(default=True, string='Ativo')
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, este documento será incluído no sistema de IA')

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'document_type', 'content', 'business_rule_ids', 'active', 'visible_in_ai'
        ]

        # Se o documento está sendo desativado ou marcado como não visível no IA, marcar para sincronização
        if ('active' in vals and vals['active'] is False) or ('visible_in_ai' in vals and vals['visible_in_ai'] is False):
            action_type = "desativado" if 'active' in vals and vals['active'] is False else "marcado como não visível no IA"
            _logger.info(f"Documento {self.name} (ID: {self.id}) está sendo {action_type}")

        result = super(BusinessSupportDocument2, self).write(vals)

        # Verificar se algum campo relevante foi alterado
        if any(field in vals for field in sync_fields):
            # Atualizar a data da última sincronização das regras de negócio associadas
            for record in self:
                for business_rule in record.business_rule_ids:
                    business_rule.write({'last_sync_date': False})

        return result

    def unlink(self):
        """Sobrescrever método unlink para remover o documento das regras de negócio antes de excluí-lo"""
        for record in self:
            try:
                # Registrar informações para depuração
                _logger.info(f"Iniciando exclusão permanente do documento {record.name} (ID: {record.id})")

                # 1. Remover das regras de negócio
                if record.business_rule_ids:
                    _logger.info(f"Removendo documento {record.name} (ID: {record.id}) de {len(record.business_rule_ids)} regras de negócio antes da exclusão")
                    
                    # Para cada regra de negócio, remover este documento
                    for business_rule in record.business_rule_ids:
                        try:
                            # Usar savepoint para evitar problemas de serialização
                            with self.env.cr.savepoint():
                                # Remover apenas este documento específico
                                business_rule.write({
                                    'support_document_ids': [(3, record.id)]
                                })
                            _logger.info(f"Documento removido da regra de negócio {business_rule.name} (ID: {business_rule.id})")

                            # Atualizar status de sincronização da regra de negócio
                            with self.env.cr.savepoint():
                                business_rule.write({'last_sync_date': False})
                        except Exception as e:
                            _logger.error(f"Erro ao remover documento da regra de negócio: {e}")
            except Exception as e:
                _logger.error(f"Erro ao preparar documento para exclusão: {e}")
                
        return super(BusinessSupportDocument2, self).unlink()

    def action_sync_document(self):
        """Sincronizar documento individual com o sistema de IA"""
        self.ensure_one()

        try:
            # Obter a primeira regra de negócio associada
            business_rule = self.business_rule_ids[0] if self.business_rule_ids else False

            if not business_rule:
                raise UserError(_("Este documento não está associado a nenhuma regra de negócio."))

            # Chamar o método de sincronização da regra de negócio
            controller = self.env['business.rules2.sync.controller'].sudo()
            result = controller.sync_support_documents(business_rule.id, env=self.env, document_ids=[self.id])

            if result and result.get('success'):
                self.write({
                    'last_sync_date': fields.Datetime.now()
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _('Documento sincronizado com sucesso com o sistema de IA.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                error_msg = result.get('error', 'Erro desconhecido') if result else 'Erro desconhecido'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': error_msg,
                        'sticky': True,
                        'type': 'danger',
                    }
                }
        except Exception as e:
            _logger.exception("Erro ao sincronizar documento")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro na Sincronização'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
