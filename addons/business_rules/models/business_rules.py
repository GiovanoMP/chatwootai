# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import requests
from datetime import datetime

_logger = logging.getLogger(__name__)

class BusinessRules(models.Model):
    _name = 'business.rules'
    _description = 'Regras de Negócio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nome da Empresa', required=True, tracking=True)
    website = fields.Char(string='Site da Empresa', tracking=True)
    description = fields.Text(string='Descrição Curta', tracking=True)
    company_values = fields.Text(string='Valores da Marca', tracking=True,
                                help='Descreva os principais valores que sua marca representa')

    # Configurações de Atendimento
    greeting_message = fields.Text(string='Saudação Inicial', tracking=True,
                                  help='Como o agente deve cumprimentar os clientes')
    communication_style = fields.Selection([
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('friendly', 'Amigável'),
        ('technical', 'Técnico')
    ], string='Estilo de Comunicação', default='friendly', tracking=True)

    emoji_usage = fields.Selection([
        ('none', 'Não Usar'),
        ('moderate', 'Uso Moderado'),
        ('frequent', 'Uso Frequente')
    ], string='Uso de Emojis', default='moderate', tracking=True)

    # Horário de funcionamento
    business_hours_start = fields.Float(string='Horário de Início', default=8.0, tracking=True)
    business_hours_end = fields.Float(string='Horário de Término', default=18.0, tracking=True)

    # Intervalo de almoço
    lunch_break_start = fields.Float(string='Início do Intervalo', default=12.0, tracking=True)
    lunch_break_end = fields.Float(string='Fim do Intervalo', default=13.0, tracking=True)
    has_lunch_break = fields.Boolean(string='Possui Intervalo', default=True, tracking=True)

    # Dias de funcionamento
    monday = fields.Boolean(string='Segunda-feira', default=True, tracking=True)
    tuesday = fields.Boolean(string='Terça-feira', default=True, tracking=True)
    wednesday = fields.Boolean(string='Quarta-feira', default=True, tracking=True)
    thursday = fields.Boolean(string='Quinta-feira', default=True, tracking=True)
    friday = fields.Boolean(string='Sexta-feira', default=True, tracking=True)
    saturday = fields.Boolean(string='Sábado', default=False, tracking=True)
    sunday = fields.Boolean(string='Domingo', default=False, tracking=True)

    # Horários especiais para sábado
    saturday_hours_start = fields.Float(string='Início Sábado', default=8.0, tracking=True)
    saturday_hours_end = fields.Float(string='Término Sábado', default=12.0, tracking=True)

    # Área de Negócio
    business_area = fields.Selection([
        ('retail', 'Varejo/Loja Física'),
        ('ecommerce', 'E-commerce/Loja Virtual'),
        ('healthcare', 'Saúde/Clínica/Consultório'),
        ('education', 'Educação'),
        ('manufacturing', 'Indústria'),
        ('services', 'Prestador de Serviços'),
        ('restaurant', 'Restaurante/Pizzaria'),
        ('financial', 'Serviços Financeiros'),
        ('technology', 'Tecnologia'),
        ('hospitality', 'Hotelaria'),
        ('real_estate', 'Imobiliário'),
        ('other', 'Outro')
    ], string='Área de Negócio', required=True, tracking=True)

    business_area_other = fields.Char(string='Outra Área de Negócio', tracking=True)

    # Regras e Sincronização
    rule_ids = fields.One2many('business.rule.item', 'business_rule_id', string='Regras Permanentes')
    temporary_rule_ids = fields.One2many('business.temporary.rule', 'business_rule_id', string='Regras Temporárias')

    # Documentos de Suporte ao Cliente
    support_document_ids = fields.Many2many(
        'business.support.document',
        'business_rule_support_doc_rel',
        'business_rule_id',
        'document_id',
        string='Documentos de Suporte',
        help='Documentos relacionados ao suporte ao cliente'
    )

    last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Sincronizando...'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro na Sincronização')
    ], string='Status de Sincronização', default='not_synced', readonly=True)

    active = fields.Boolean(default=True, string='Ativo')
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)

    # Contagem de regras ativas
    active_permanent_rules_count = fields.Integer(compute='_compute_active_rules_count', string='Regras Permanentes Ativas')
    active_temporary_rules_count = fields.Integer(compute='_compute_active_rules_count', string='Regras Temporárias Ativas')

    @api.depends('rule_ids', 'temporary_rule_ids')
    def _compute_active_rules_count(self):
        for record in self:
            record.active_permanent_rules_count = len(record.rule_ids.filtered(lambda r: r.active))

            # Contar apenas regras temporárias ativas e dentro do período de validade
            now = fields.Datetime.now()
            active_temp_rules = record.temporary_rule_ids.filtered(
                lambda r: r.active and
                (not r.date_start or r.date_start <= now) and
                (not r.date_end or r.date_end >= now)
            )
            record.active_temporary_rules_count = len(active_temp_rules)

    @api.onchange('business_area')
    def _onchange_business_area(self):
        """Carregar regras padrão com base na área de negócio selecionada"""
        if self.business_area:
            # Aqui carregaríamos regras padrão da área selecionada
            # Implementação completa será feita posteriormente
            template = self.env['business.template'].search([('model_type', '=', self.business_area)], limit=1)
            if template:
                self.greeting_message = template.default_greeting
                # Outras configurações padrão podem ser carregadas aqui

    def action_sync_with_ai(self):
        """Sincronizar regras com o sistema de IA"""
        self.ensure_one()

        # Atualizar status para 'sincronizando'
        self.write({'sync_status': 'syncing'})
        self.env.cr.commit()  # Commit imediato para atualizar a UI

        try:
            # Chamar diretamente o método do controlador
            # Importar o controlador
            from ..controllers.sync_controller import BusinessRulesSyncController

            # Criar uma instância do controlador
            controller = BusinessRulesSyncController()

            # Chamar o método diretamente, passando o ambiente
            result = controller.sync_business_rules(self.id, env=self.env)

            # Verificar resultado da sincronização
            if result and result.get('success'):
                self.write({
                    'last_sync_date': fields.Datetime.now(),
                    'sync_status': 'synced'
                })

                # Mensagem de sucesso com detalhes
                rules_count = result.get('rules_count', 0)
                vectorized_count = result.get('vectorized_rules', 0)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _(f'Sincronizadas {rules_count} regras, {vectorized_count} vetorizadas.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                # Atualizar status para erro
                self.write({
                    'last_sync_date': fields.Datetime.now(),
                    'sync_status': 'error'
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': _(f'Erro ao sincronizar: {result.get("error", "Erro desconhecido")}'),
                        'sticky': True,
                        'type': 'danger',
                    }
                }

        except Exception as e:
            # Em caso de erro, atualizar status
            self.write({
                'last_sync_date': fields.Datetime.now(),
                'sync_status': 'error'
            })

            _logger.error("Erro ao sincronizar regras: %s", str(e))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro na Sincronização'),
                    'message': _(f'Erro ao sincronizar: {str(e)}'),
                    'sticky': True,
                    'type': 'danger',
                }
            }

    def action_view_active_rules(self):
        """Abrir dashboard de regras ativas"""
        self.ensure_one()
        return {
            'name': _('Regras Ativas'),
            'type': 'ir.actions.act_window',
            'res_model': 'business.rules.dashboard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_business_rule_id': self.id}
        }

    def action_scrape_website(self):
        """Abrir wizard para fazer scraping do website"""
        self.ensure_one()
        if not self.website:
            raise UserError(_("Por favor, informe o site da empresa antes de usar esta função."))

        return {
            'name': _('Extrair Informações do Website'),
            'type': 'ir.actions.act_window',
            'res_model': 'business.website.scraper.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_business_rule_id': self.id, 'default_website': self.website}
        }

    def action_view_customer_support(self):
        """Abre a visualização de suporte ao cliente."""
        self.ensure_one()
        return {
            'name': _('Suporte ao Cliente'),
            'type': 'ir.actions.act_window',
            'res_model': 'business.support.document',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.support_document_ids.ids)],
            'context': {'default_business_rule_id': self.id}
        }

    def action_upload_documents(self):
        """Abrir wizard para upload de documentos"""
        self.ensure_one()
        return {
            'name': _('Adicionar Documento de Suporte'),
            'type': 'ir.actions.act_window',
            'res_model': 'business.document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_business_rule_id': self.id}
        }

    def action_sync_support_documents(self):
        """Sincroniza os documentos de suporte com o sistema de IA."""
        self.ensure_one()
        try:
            # Chamar o MCP-Odoo para sincronizar documentos
            result = self._call_mcp_sync_support_docs()

            if result and result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _('Documentos sincronizados com sucesso.'),
                        'sticky': False,
                        'type': 'success'
                    }
                }
            else:
                error_msg = result.get('error') if result else "Erro desconhecido"
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
            _logger.error("Erro ao sincronizar documentos de suporte: %s", str(e))
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

    def _call_mcp_sync_support_docs(self):
        """Chama o MCP-Odoo para sincronizar documentos de suporte."""
        try:
            import requests

            # Obter configurações do MCP-Odoo
            IrConfigParam = self.env['ir.config_parameter'].sudo()
            mcp_url = IrConfigParam.get_param('business_rules.mcp_url', 'http://localhost:8000')
            mcp_token = IrConfigParam.get_param('business_rules.mcp_token', '')
            account_id = IrConfigParam.get_param('business_rules.account_id', 'account_1')

            # Preparar a requisição
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
            }

            # Obter informações dos documentos
            docs_data = []
            for doc in self.support_document_ids:
                docs_data.append({
                    'id': doc.id,
                    'name': doc.name,
                    'document_type': doc.document_type,
                    'content': doc.content,
                    'create_date': fields.Datetime.to_string(doc.create_date) if doc.create_date else '',
                })

            payload = {
                'account_id': account_id,
                'business_rule_id': self.id,
                'documents': docs_data
            }

            # Fazer a requisição ao MCP-Odoo
            _logger.info(f"Chamando MCP-Odoo para sincronizar documentos de suporte para a regra de negócio {self.id}")
            response = requests.post(
                f"{mcp_url}/tools/sync_support_documents",
                headers=headers,
                json=payload,
                timeout=30  # Timeout de 30 segundos
            )

            # Verificar resposta
            if response.status_code == 200:
                result = response.json()

                # Atualizar status de sincronização dos documentos
                if result.get('synced_docs'):
                    for doc_id in result['synced_docs']:
                        doc = self.env['business.support.document'].browse(int(doc_id))
                        if doc:
                            doc.write({'sync_status': 'synced'})

                return result
            else:
                _logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")
                return {'success': False, 'error': f"Erro {response.status_code}: {response.text}"}
        except Exception as e:
            _logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
            return {'success': False, 'error': str(e)}
