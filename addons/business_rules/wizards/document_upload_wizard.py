# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging
import io
import re
import PyPDF2
import docx

_logger = logging.getLogger(__name__)

class DocumentUploadWizard(models.TransientModel):
    _name = 'business.document.upload.wizard'
    _description = 'Assistente de Suporte ao Cliente'

    business_rule_id = fields.Many2one('business.rules', string='Regra de Negócio', required=True)
    document_type = fields.Selection([
        ('support', 'Suporte Técnico'),
        ('feedback', 'Feedback'),
        ('question', 'Dúvida'),
        ('suggestion', 'Sugestão'),
        ('other', 'Outro')
    ], string='Tipo de Documento', default='support', required=True)
    
    message = fields.Text(string='Descrição', help='Descrição ou contexto do documento')

    document_file = fields.Binary(string='Arquivo', required=True)
    document_filename = fields.Char(string='Nome do Arquivo')

    name = fields.Char(string='Nome do Documento', required=True)
    content = fields.Text(string='Conteúdo do Documento', help='Conteúdo do documento em texto')

    def action_extract_content(self):
        """Extrair conteúdo do documento para suporte ao cliente"""
        self.ensure_one()

        if not self.document_file:
            raise UserError(_("Por favor, selecione um arquivo para upload."))

        try:
            # Decodificar o arquivo
            file_data = base64.b64decode(self.document_file)
            content = ""

            # Extrair conteúdo com base no tipo de arquivo
            filename = self.document_filename or ""

            if filename.lower().endswith('.pdf'):
                # Extrair texto de PDF
                pdf_file = io.BytesIO(file_data)
                pdf_reader = PyPDF2.PdfFileReader(pdf_file)

                for page_num in range(pdf_reader.numPages):
                    page = pdf_reader.getPage(page_num)
                    content += page.extractText() + "\n"

            elif filename.lower().endswith(('.docx', '.doc')):
                # Extrair texto de Word
                docx_file = io.BytesIO(file_data)
                doc = docx.Document(docx_file)

                for para in doc.paragraphs:
                    content += para.text + "\n"

            elif filename.lower().endswith(('.txt', '.csv')):
                # Texto simples
                content = file_data.decode('utf-8', errors='ignore')

            else:
                raise UserError(_("Formato de arquivo não suportado. Por favor, use PDF, DOCX, DOC ou TXT."))

            # Adicionar a mensagem do usuário ao conteúdo, se fornecida
            if self.message:
                content = f"Descrição do documento:\n{self.message}\n\nConteúdo do documento:\n{content}"

            # Usar o nome do arquivo como nome do documento se não for fornecido
            if not self.name and self.document_filename:
                self.name = self.document_filename.split('.')[0]
            elif not self.name:
                self.name = "Documento de Suporte"

            # Atualizar conteúdo
            self.write({
                'content': content
            })

            return self.action_create_document()

        except Exception as e:
            _logger.error("Erro ao extrair conteúdo do documento: %s", str(e))
            raise UserError(_("Erro ao processar o documento: %s") % str(e))

    def action_create_document(self):
        """Criar documento de suporte a partir do conteúdo extraído"""
        self.ensure_one()

        if not self.content:
            raise UserError(_("O conteúdo do documento não pode estar vazio."))

        # Criar documento de suporte
        doc = self.env['business.support.document'].create({
            'name': self.name,
            'document_type': self.document_type,
            'content': self.content,
            'business_rule_ids': [(4, self.business_rule_id.id)],
            'sync_status': 'not_synced',
            'active': True
        })

        # Sincronizar documento com o sistema de IA
        self.business_rule_id.action_sync_support_documents()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Documento Criado'),
                'message': _('Documento "%s" foi criado e sincronizado com sucesso.') % self.name,
                'sticky': False,
                'type': 'success',
            }
        }
