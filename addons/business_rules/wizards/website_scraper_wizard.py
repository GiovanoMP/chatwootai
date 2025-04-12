# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class WebsiteScraperWizard(models.TransientModel):
    _name = 'business.website.scraper.wizard'
    _description = 'Assistente de Extração de Website'

    business_rule_id = fields.Many2one('business.rules', string='Regra de Negócio', required=True)
    website = fields.Char(string='Website', required=True)

    scrape_about = fields.Boolean(string='Extrair Sobre a Empresa', default=True)
    scrape_contact = fields.Boolean(string='Extrair Informações de Contato', default=True)
    scrape_products = fields.Boolean(string='Extrair Informações de Produtos/Serviços', default=True)

    state = fields.Selection([
        ('extract', 'Extrair'),
        ('review', 'Revisar')
    ], default='extract', string='Estado')

    # Campos para revisão
    extracted_description = fields.Text(string='Descrição Extraída')
    extracted_values = fields.Text(string='Valores Extraídos')
    extracted_hours = fields.Text(string='Horário de Funcionamento Extraído')

    def action_extract_info(self):
        """Preparar para extração de informações do website via agentes de IA"""
        self.ensure_one()

        if not self.website:
            raise UserError(_("Por favor, informe o website da empresa."))

        try:
            # Normalizar URL
            url = self.website
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Simular a extração de informações
            # Na implementação real, aqui faríamos uma chamada para o sistema de agentes de IA
            # para extrair as informações do website

            # Dados simulados para demonstração
            description = f"Informações extraídas do website {url} via agentes de IA. " \
                          f"Aqui serão exibidas informações sobre a empresa, como descrição, "\
                          f"missão, visão e valores."

            values = "Missão: Oferecer produtos/serviços de qualidade.\n" \
                    "Visão: Ser referência no mercado.\n" \
                    "Valores: Ética, Respeito, Inovação."

            hours = "Segunda a Sexta: 08:00 às 18:00\n" \
                   "Sábado: 09:00 às 13:00\n" \
                   "Domingo: Fechado"

            # Atualizar campos para revisão
            self.write({
                'state': 'review',
                'extracted_description': description,
                'extracted_values': values,
                'extracted_hours': hours
            })

            # Exibir mensagem informativa no log
            _logger.info("Na versão final, esta funcionalidade usará agentes de IA para extrair informações do website.")

            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        except Exception as e:
            _logger.error("Erro ao preparar extração de informações do website: %s", str(e))
            raise UserError(_("Erro ao processar o website: %s") % str(e))

    def action_apply_extracted_info(self):
        """Aplicar informações extraídas à regra de negócio"""
        self.ensure_one()

        # Atualizar a regra de negócio com as informações extraídas
        vals = {}

        if self.extracted_description:
            vals['description'] = self.extracted_description

        if self.extracted_values:
            vals['company_values'] = self.extracted_values

        if self.extracted_hours:
            # Processar o texto de horário de funcionamento
            hours_text = self.extracted_hours.lower()

            # Definir valores padrão baseados no texto
            if 'segunda a sexta' in hours_text:
                vals['business_days'] = 'Segunda a Sexta'
            elif 'segunda a sábado' in hours_text:
                vals['business_days'] = 'Segunda a Sábado'

            # Extrair horários de forma simplificada
            # Na implementação real, isso seria feito pelo agente de IA
            if '08:00' in hours_text and '18:00' in hours_text:
                vals['business_hours_start'] = 8.0
                vals['business_hours_end'] = 18.0
            elif '09:00' in hours_text and '17:00' in hours_text:
                vals['business_hours_start'] = 9.0
                vals['business_hours_end'] = 17.0

        # Atualizar a regra de negócio
        if vals:
            self.business_rule_id.write(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Informações Aplicadas'),
                'message': _('As informações extraídas foram aplicadas com sucesso.'),
                'sticky': False,
                'type': 'success',
            }
        }
