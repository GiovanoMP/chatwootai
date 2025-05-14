# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class DocumentUploadWizard(models.TransientModel):
    _name = 'business.document.upload.wizard'
    _description = 'Assistente de Upload de Documentos'
    
    name = fields.Char(string='Nome do Documento', required=True)
    document_type = fields.Selection([
        ('support', 'Suporte Técnico'),
        ('feedback', 'Feedback'),
        ('question', 'Dúvida'),
        ('suggestion', 'Sugestão'),
        ('other', 'Outro')
    ], string='Tipo de Documento', default='support', required=True)
    
    file = fields.Binary(string='Arquivo', required=True)
    file_name = fields.Char(string='Nome do Arquivo')
    
    content = fields.Text(string='Conteúdo', required=True)
    
    business_rule_id = fields.Many2one('business.rules', string='Regra de Negócio', required=True)
    
    def action_upload(self):
        """Criar documento de suporte a partir do upload"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_("Por favor, selecione um arquivo para upload."))
        
        if not self.content:
            raise UserError(_("O conteúdo do documento não pode estar vazio."))
        
        # Criar anexo
        attachment = self.env['ir.attachment'].create({
            'name': self.file_name,
            'datas': self.file,
            'res_model': 'business.support.document',
            'res_id': 0,  # Será atualizado após a criação do documento
        })
        
        # Criar documento de suporte
        document = self.env['business.support.document'].create({
            'name': self.name,
            'document_type': self.document_type,
            'content': self.content,
            'business_rule_ids': [(4, self.business_rule_id.id)],
            'attachment_ids': [(4, attachment.id)],
            'active': True,
            'visible_in_ai': True
        })
        
        # Atualizar o res_id do anexo
        attachment.write({
            'res_id': document.id
        })
        
        # Retornar ação para visualizar o documento criado
        return {
            'name': _('Documento de Suporte'),
            'view_mode': 'form',
            'res_model': 'business.support.document',
            'res_id': document.id,
            'type': 'ir.actions.act_window',
        }
