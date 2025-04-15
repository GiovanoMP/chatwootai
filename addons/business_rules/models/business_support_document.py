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
