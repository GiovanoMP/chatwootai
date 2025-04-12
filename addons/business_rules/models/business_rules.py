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
    
    business_hours_start = fields.Float(string='Horário de Início', default=8.0, tracking=True)
    business_hours_end = fields.Float(string='Horário de Término', default=18.0, tracking=True)
    business_days = fields.Char(string='Dias de Funcionamento', default='Segunda a Sexta', tracking=True)
    
    response_time = fields.Selection([
        ('immediate', 'Imediato (segundos)'),
        ('quick', 'Rápido (minutos)'),
        ('standard', 'Padrão (horas)'),
        ('extended', 'Estendido (dias)')
    ], string='Tempo de Resposta Esperado', default='quick', tracking=True)
    
    # Modelo de Negócio
    business_model = fields.Selection([
        ('restaurant', 'Restaurante/Pizzaria'),
        ('ecommerce', 'E-commerce/Loja Virtual'),
        ('clinic', 'Clínica/Consultório'),
        ('retail', 'Loja Física'),
        ('service', 'Prestador de Serviços'),
        ('other', 'Outro')
    ], string='Modelo de Negócio', required=True, tracking=True)
    
    business_model_other = fields.Char(string='Outro Modelo de Negócio', tracking=True)
    
    # Regras e Sincronização
    rule_ids = fields.One2many('business.rule.item', 'business_rule_id', string='Regras Permanentes')
    temporary_rule_ids = fields.One2many('business.temporary.rule', 'business_rule_id', string='Regras Temporárias')
    
    last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
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
    
    @api.onchange('business_model')
    def _onchange_business_model(self):
        """Carregar regras padrão com base no modelo de negócio selecionado"""
        if self.business_model:
            # Aqui carregaríamos regras padrão do modelo selecionado
            # Implementação completa será feita posteriormente
            template = self.env['business.template'].search([('model_type', '=', self.business_model)], limit=1)
            if template:
                self.greeting_message = template.default_greeting
                # Outras configurações padrão podem ser carregadas aqui
    
    def action_sync_with_ai(self):
        """Sincronizar regras com o sistema de IA"""
        self.ensure_one()
        try:
            # Aqui implementaríamos a chamada para o sistema de IA
            # Por enquanto, apenas simulamos a sincronização
            self.last_sync_date = fields.Datetime.now()
            self.sync_status = 'synced'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sincronização Concluída'),
                    'message': _('As regras foram sincronizadas com o sistema de IA.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            self.sync_status = 'error'
            _logger.error("Erro ao sincronizar com o sistema de IA: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro de Sincronização'),
                    'message': _('Ocorreu um erro ao sincronizar com o sistema de IA: %s') % str(e),
                    'sticky': False,
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
    
    def action_upload_documents(self):
        """Abrir wizard para upload de documentos"""
        self.ensure_one()
        return {
            'name': _('Upload de Documentos'),
            'type': 'ir.actions.act_window',
            'res_model': 'business.document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_business_rule_id': self.id}
        }
