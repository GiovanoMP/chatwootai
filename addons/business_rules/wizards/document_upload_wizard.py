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
    ], string='Tipo de Mensagem', default='support', required=True)
    
    message = fields.Text(string='Mensagem', help='Digite sua mensagem ou dúvida')

    document_file = fields.Binary(string='Arquivo', required=True)
    document_filename = fields.Char(string='Nome do Arquivo')

    state = fields.Selection([
        ('upload', 'Upload'),
        ('review', 'Revisão'),
        ('done', 'Concluído')
    ], default='upload', string='Estado')

    # Campos para revisão
    extracted_content = fields.Text(string='Conteúdo Extraído')
    extracted_rules = fields.One2many('business.document.extracted.rule', 'wizard_id', string='Regras Extraídas')

    def action_extract_content(self):
        """Extrair conteúdo do documento e processar como FAQ para suporte ao cliente"""
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
                content = f"Mensagem do usuário:\n{self.message}\n\nConteúdo do documento:\n{content}"

            # Processar o conteúdo para extrair FAQs
            extracted_rules = self._extract_rules_from_content(content)

            # Limpar regras existentes
            self.extracted_rules.unlink()

            # Criar novas regras extraídas
            for rule in extracted_rules:
                self.env['business.document.extracted.rule'].create({
                    'wizard_id': self.id,
                    'name': rule['name'],
                    'description': rule['description'],
                    'selected': True
                })

            # Atualizar estado e conteúdo extraído
            self.write({
                'state': 'review',
                'extracted_content': content[:1000] + ('...' if len(content) > 1000 else '')
            })

            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        except Exception as e:
            _logger.error("Erro ao extrair conteúdo do documento: %s", str(e))
            raise UserError(_("Erro ao processar o documento: %s") % str(e))

    def _extract_rules_from_content(self, content):
        """Extrair FAQs e informações de suporte do conteúdo do documento"""
        rules = []

        # Implementação para processar diferentes tipos de mensagens
        
        # Para suporte técnico e dúvidas, procurar por padrões de pergunta e resposta
        if self.document_type in ['support', 'question']:
            # Dividir por linhas
            lines = content.split('\n')
            current_question = None
            current_answer = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Verificar se é uma pergunta
                if line.endswith('?') or re.match(r'^[0-9]+[\.\)]\s', line) or re.match(r'^P[0-9]*:', line) or re.match(r'^Pergunta[0-9]*:', line):
                    # Se já temos uma pergunta anterior, salvar
                    if current_question and current_answer:
                        rules.append({
                            'name': current_question[:100],
                            'description': '\n'.join(current_answer)
                        })

                    # Nova pergunta
                    current_question = line
                    current_answer = []
                else:
                    # Adicionar à resposta atual
                    if current_question:
                        current_answer.append(line)

            # Adicionar a última pergunta/resposta
            if current_question and current_answer:
                rules.append({
                    'name': current_question[:100],
                    'description': '\n'.join(current_answer)
                })
                
            # Se não encontrou perguntas e respostas, criar uma regra com o conteúdo completo
            if not rules and content.strip():
                title = "Dúvida de Suporte"
                if self.message:
                    # Usar as primeiras palavras da mensagem como título
                    words = self.message.split()
                    if len(words) > 3:
                        title = " ".join(words[:5]) + "..."
                    else:
                        title = self.message[:100]
                        
                rules.append({
                    'name': title,
                    'description': content.strip()
                })

        # Para feedback e sugestões, processar como seções
        elif self.document_type in ['feedback', 'suggestion']:
            sections = re.split(r'\n\s*\n', content)
            
            # Se há apenas uma seção, usar a mensagem como título
            if len(sections) == 1 and self.message:
                rules.append({
                    'name': self.message[:100],
                    'description': sections[0].strip()
                })
            else:
                for i, section in enumerate(sections):
                    if len(section.strip()) < 20:  # Ignorar seções muito curtas
                        continue

                    # Tentar extrair um título
                    lines = section.split('\n')
                    title = lines[0].strip()

                    if title and len(title) < 100:
                        description = '\n'.join(lines[1:]).strip()
                        if description:
                            rules.append({
                                'name': title,
                                'description': description
                            })
                    else:
                        # Se não conseguir extrair um título, usar um genérico
                        rules.append({
                            'name': f"{self.document_type.capitalize()} {i+1}",
                            'description': section.strip()
                        })

        # Para outros tipos, dividir em seções
        else:
            # Se tiver mensagem, usar como título principal
            if self.message:
                rules.append({
                    'name': self.message[:100],
                    'description': content.strip()
                })
            else:
                sections = re.split(r'\n\s*\n', content)

                for i, section in enumerate(sections):
                    if len(section.strip()) < 30:
                        continue

                    rules.append({
                        'name': f"Informação {i+1}",
                        'description': section.strip()
                    })

        return rules

    def action_create_rules(self):
        """Criar regras a partir do conteúdo extraído"""
        self.ensure_one()

        # Filtrar regras selecionadas
        selected_rules = self.extracted_rules.filtered(lambda r: r.selected)

        if not selected_rules:
            raise UserError(_("Por favor, selecione pelo menos uma regra para criar."))

        # Determinar o tipo de regra com base no tipo de documento
        rule_type_mapping = {
            'support': 'general',
            'feedback': 'general',
            'question': 'general',
            'suggestion': 'general',
            'other': 'other'
        }
        rule_type = rule_type_mapping.get(self.document_type, 'general')

        # Criar regras permanentes
        for rule in selected_rules:
            self.env['business.rule.item'].create({
                'business_rule_id': self.business_rule_id.id,
                'name': rule.name,
                'description': rule.description,
                'rule_type': rule_type,
                'priority': '0',
                'active': True
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Regras Criadas'),
                'message': _('%s regras foram criadas com sucesso.') % len(selected_rules),
                'sticky': False,
                'type': 'success',
            }
        }

class DocumentExtractedRule(models.TransientModel):
    _name = 'business.document.extracted.rule'
    _description = 'Regra Extraída de Documento'

    wizard_id = fields.Many2one('business.document.upload.wizard', string='Wizard', required=True, ondelete='cascade')
    name = fields.Char(string='Nome da Regra', required=True)
    description = fields.Text(string='Descrição', required=True)
    selected = fields.Boolean(string='Selecionada', default=True)
