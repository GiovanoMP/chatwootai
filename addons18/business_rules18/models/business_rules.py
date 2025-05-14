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

    name = fields.Char(string='Nome da Regra', tracking=True, default='Regras de Negócio')
    description = fields.Text(string='Descrição', tracking=True)

    # Removido o campo rule_type que estava causando problemas no Odoo 18

    # Regras e Sincronização
    rule_ids = fields.One2many('business.rule.item', 'business_rule_id', string='Regras de Negócio')
    temporary_rule_ids = fields.One2many('business.temporary.rule', 'business_rule_id', string='Regras Temporárias')
    scheduling_rule_ids = fields.One2many('business.scheduling.rule', 'business_rule_id', string='Regras de Agendamento')

    # Documentos de suporte
    support_document_ids = fields.Many2many(
        'business.support.document',
        'business_rule_support_doc_rel',
        'business_rule_id',
        'document_id',
        string='Documentos de Suporte'
    )

    # Status de sincronização
    last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Processando'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro')
    ], string='Status de Sincronização', default='not_synced', readonly=True, tracking=True)
    error_message = fields.Text('Mensagem de Erro', readonly=True)

    # Campos de controle
    active = fields.Boolean(default=True, string='Ativo')
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, esta regra será incluída no sistema de IA')
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)

    # Serviços de Atendimento Habilitados (definidos como True por padrão)
    use_business_rules = fields.Boolean('Vendas de Produtos e Serviços', default=True)
    use_scheduling_rules = fields.Boolean('Agendamentos', default=True)
    use_delivery_rules = fields.Boolean('Delivery', default=True)
    use_support_documents = fields.Boolean('Suporte ao Cliente', default=True)

    # Contadores para dashboard
    active_permanent_rules_count = fields.Integer(compute='_compute_rule_counts', string='Regras Permanentes Ativas')
    active_temporary_rules_count = fields.Integer(compute='_compute_rule_counts', string='Regras Temporárias Ativas')
    active_scheduling_rules_count = fields.Integer(compute='_compute_rule_counts', string='Regras de Agendamento Ativas')
    support_documents_count = fields.Integer(compute='_compute_rule_counts', string='Documentos de Suporte')

    # Campos dummy para compatibilidade com views embutidas
    # Estes campos são necessários porque o Odoo 18 é mais rigoroso na validação de campos em views embutidas

    # Campos do modelo business.temporary.rule
    date_start = fields.Date(string='Data de Início', compute='_compute_dummy_fields')
    date_end = fields.Date(string='Data de Término', compute='_compute_dummy_fields')
    rule_type = fields.Selection([
        ('promotion', 'Promoção'),
        ('discount', 'Desconto'),
        ('seasonal', 'Sazonal'),
        ('event', 'Evento'),
        ('holiday', 'Feriado'),
        ('other', 'Outro')
    ], string='Tipo de Regra', compute='_compute_dummy_fields')
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('active', 'Ativa'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada')
    ], string='Estado', compute='_compute_dummy_fields')

    # Campos do modelo business.scheduling.rule
    service_type = fields.Selection([
        ('consultation', 'Consulta'),
        ('service', 'Serviço'),
        ('class', 'Aula'),
        ('event', 'Evento'),
        ('other', 'Outro')
    ], string='Tipo de Serviço', compute='_compute_dummy_fields')
    service_type_other = fields.Char(string='Outro Tipo de Serviço', compute='_compute_dummy_fields')
    sequence = fields.Integer(string='Ordem de Exibição', compute='_compute_dummy_fields')
    duration = fields.Float(string='Duração (horas)', compute='_compute_dummy_fields')
    min_interval = fields.Float(string='Intervalo Mínimo (horas)', compute='_compute_dummy_fields')
    min_advance_time = fields.Integer(string='Antecedência Mínima (horas)', compute='_compute_dummy_fields')
    max_advance_time = fields.Integer(string='Antecedência Máxima (dias)', compute='_compute_dummy_fields')

    # Dias disponíveis
    monday_available = fields.Boolean(string='Segunda-feira', compute='_compute_dummy_fields')
    tuesday_available = fields.Boolean(string='Terça-feira', compute='_compute_dummy_fields')
    wednesday_available = fields.Boolean(string='Quarta-feira', compute='_compute_dummy_fields')
    thursday_available = fields.Boolean(string='Quinta-feira', compute='_compute_dummy_fields')
    friday_available = fields.Boolean(string='Sexta-feira', compute='_compute_dummy_fields')
    saturday_available = fields.Boolean(string='Sábado', compute='_compute_dummy_fields')
    sunday_available = fields.Boolean(string='Domingo', compute='_compute_dummy_fields')

    # Horários
    morning_start = fields.Float(string='Início da Manhã', compute='_compute_dummy_fields')
    morning_end = fields.Float(string='Fim da Manhã', compute='_compute_dummy_fields')
    has_lunch_break = fields.Boolean(string='Intervalo para Almoço', compute='_compute_dummy_fields')
    afternoon_start = fields.Float(string='Início da Tarde', compute='_compute_dummy_fields')
    afternoon_end = fields.Float(string='Fim da Tarde', compute='_compute_dummy_fields')

    # Campos do modelo business.support.document
    document_type = fields.Selection([
        ('support', 'Suporte Técnico'),
        ('feedback', 'Feedback'),
        ('question', 'Dúvida'),
        ('suggestion', 'Sugestão'),
        ('other', 'Outro')
    ], string='Tipo de Documento', compute='_compute_dummy_fields')
    content = fields.Text(string='Conteúdo', compute='_compute_dummy_fields')

    @api.depends('rule_ids', 'temporary_rule_ids', 'scheduling_rule_ids', 'support_document_ids')
    def _compute_rule_counts(self):
        """Calcular contadores para o dashboard"""
        for record in self:
            record.active_permanent_rules_count = len(record.rule_ids.filtered(lambda r: r.active and r.visible_in_ai))
            record.active_temporary_rules_count = len(record.temporary_rule_ids.filtered(lambda r: r.active and r.visible_in_ai and r.state == 'active'))
            record.active_scheduling_rules_count = len(record.scheduling_rule_ids.filtered(lambda r: r.active and r.visible_in_ai))
            record.support_documents_count = len(record.support_document_ids.filtered(lambda d: d.active and d.visible_in_ai))

    def action_sync_with_ai(self):
        """Sincronizar com o sistema de IA"""
        self.ensure_one()

        try:
            # Atualizar status
            self.write({
                'sync_status': 'syncing',
                'error_message': False
            })

            # Importar o controlador de sincronização
            from ..controllers.sync_controller import BusinessRulesSyncController
            controller = BusinessRulesSyncController()

            # 1. Primeiro sincronizar os documentos de suporte
            _logger.info(f"Iniciando sincronização de documentos para a regra de negócio {self.id}")
            docs_result = controller.sync_support_documents(self.id, env=self.env)

            if not docs_result or not docs_result.get('success'):
                error_msg = docs_result.get('error', 'Erro desconhecido') if docs_result else 'Erro desconhecido'
                _logger.error(f"Falha na sincronização de documentos: {error_msg}")
                self.write({
                    'sync_status': 'error',
                    'error_message': f"Falha ao sincronizar documentos de suporte: {error_msg}"
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': _('Falha ao sincronizar documentos de suporte: %s') % error_msg,
                        'sticky': True,
                        'type': 'danger',
                    }
                }

            # 2. Depois sincronizar as regras de negócio
            _logger.info(f"Iniciando sincronização de regras para a regra de negócio {self.id}")
            rules_result = controller.sync_business_rules(self.id, env=self.env)

            if not rules_result or not rules_result.get('success'):
                error_msg = rules_result.get('error', 'Erro desconhecido') if rules_result else 'Erro desconhecido'
                _logger.error(f"Falha na sincronização de regras: {error_msg}")
                self.write({
                    'sync_status': 'error',
                    'error_message': f"Falha ao sincronizar regras de negócio: {error_msg}"
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': _('Falha ao sincronizar regras de negócio: %s') % error_msg,
                        'sticky': True,
                        'type': 'danger',
                    }
                }

            # 3. Depois sincronizar as regras de agendamento
            _logger.info(f"Iniciando sincronização de regras de agendamento para a regra de negócio {self.id}")
            scheduling_result = controller.sync_scheduling_rules(self.id, env=self.env)

            if not scheduling_result or not scheduling_result.get('success'):
                error_msg = scheduling_result.get('error', 'Erro desconhecido') if scheduling_result else 'Erro desconhecido'
                _logger.error(f"Falha na sincronização de regras de agendamento: {error_msg}")
                self.write({
                    'sync_status': 'error',
                    'error_message': f"Falha ao sincronizar regras de agendamento: {error_msg}"
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': _('Falha ao sincronizar regras de agendamento: %s') % error_msg,
                        'sticky': True,
                        'type': 'danger',
                    }
                }

            # Atualizar status para sucesso
            self.write({
                'sync_status': 'synced',
                'last_sync_date': fields.Datetime.now(),
                'error_message': False
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sincronização Concluída'),
                    'message': _('Todos os dados foram sincronizados com sucesso.'),
                    'sticky': False,
                    'type': 'success',
                }
            }

        except Exception as e:
            _logger.exception("Erro ao sincronizar com o sistema de IA")
            self.write({
                'sync_status': 'error',
                'error_message': str(e)
            })

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

    def action_view_rule_items(self):
        """Ação para visualizar itens de regra"""
        self.ensure_one()
        return {
            'name': _('Regras de Negócio'),
            'view_mode': 'tree,form',
            'res_model': 'business.rule.item',
            'domain': [('business_rule_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_business_rule_id': self.id}
        }

    def action_view_temporary_rules(self):
        """Ação para visualizar regras temporárias"""
        self.ensure_one()
        return {
            'name': _('Regras Temporárias'),
            'view_mode': 'tree,form',
            'res_model': 'business.temporary.rule',
            'domain': [('business_rule_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_business_rule_id': self.id}
        }

    def action_view_scheduling_rules(self):
        """Ação para visualizar regras de agendamento"""
        self.ensure_one()
        return {
            'name': _('Regras de Agendamento'),
            'view_mode': 'tree,form',
            'res_model': 'business.scheduling.rule',
            'domain': [('business_rule_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_business_rule_id': self.id}
        }

    def action_view_support_documents(self):
        """Ação para visualizar documentos de suporte"""
        self.ensure_one()
        return {
            'name': _('Documentos de Suporte'),
            'view_mode': 'tree,form',
            'res_model': 'business.support.document',
            'domain': [('business_rule_ids', 'in', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_business_rule_ids': [(4, self.id)]}
        }

    def _compute_dummy_fields(self):
        """Método dummy para campos computados de compatibilidade com views embutidas

        Este método é necessário porque o Odoo 18 é mais rigoroso na validação de campos
        em views embutidas. Ele cria campos dummy que são referenciados nas views embutidas
        mas que na verdade pertencem aos modelos relacionados.
        """
        for record in self:
            # Valores padrão para campos do modelo business.temporary.rule
            record.date_start = fields.Date.today()
            record.date_end = fields.Date.today()
            record.rule_type = 'other'
            record.state = 'draft'

            # Valores padrão para campos do modelo business.scheduling.rule
            record.service_type = 'other'
            record.service_type_other = ''
            record.sequence = 10
            record.duration = 1.0
            record.min_interval = 0.0
            record.min_advance_time = 24
            record.max_advance_time = 30

            # Dias disponíveis
            record.monday_available = True
            record.tuesday_available = True
            record.wednesday_available = True
            record.thursday_available = True
            record.friday_available = True
            record.saturday_available = False
            record.sunday_available = False

            # Horários
            record.morning_start = 8.0
            record.morning_end = 12.0
            record.has_lunch_break = True
            record.afternoon_start = 14.0
            record.afternoon_end = 18.0

            # Valores padrão para campos do modelo business.support.document
            record.document_type = 'other'
            record.content = ''
