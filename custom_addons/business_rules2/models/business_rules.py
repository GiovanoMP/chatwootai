# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import requests
from datetime import datetime

_logger = logging.getLogger(__name__)

class BusinessRules2(models.Model):
    _name = 'business.rules2'
    _description = 'Regras de Negócio 2.0'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nome da Regra', tracking=True, default='Regras de Negócio')

    # Regras e Sincronização
    rule_ids = fields.One2many('business.rule.item2', 'business_rule_id', string='Regras de Negócio')
    temporary_rule_ids = fields.One2many('business.temporary.rule2', 'business_rule_id', string='Regras Temporárias')
    scheduling_rule_ids = fields.One2many('business.scheduling.rule2', 'business_rule_id', string='Regras de Agendamento')

    # Documentos de suporte
    support_document_ids = fields.Many2many(
        'business.support.document2',
        'business_rule_support_doc_rel2',
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
    use_business_rules = fields.Boolean('Vendas de Produtos e Serviços', default=True, invisible=True)
    use_scheduling_rules = fields.Boolean('Agendamentos', default=True, invisible=True)
    use_delivery_rules = fields.Boolean('Delivery', default=True, invisible=True)
    use_support_documents = fields.Boolean('Suporte ao Cliente', default=True, invisible=True)

    # Contadores para dashboard
    active_permanent_rules_count = fields.Integer(compute='_compute_rule_counts', string='Regras Permanentes Ativas')
    active_temporary_rules_count = fields.Integer(compute='_compute_rule_counts', string='Regras Temporárias Ativas')
    active_scheduling_rules_count = fields.Integer(compute='_compute_rule_counts', string='Regras de Agendamento Ativas')
    support_documents_count = fields.Integer(compute='_compute_rule_counts', string='Documentos de Suporte')

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
            # Atualizar status para "Processando"
            self.write({
                'sync_status': 'syncing',
                'error_message': False
            })

            # Obter o controlador de sincronização
            controller = self.env['business.rules2.sync.controller'].sudo()

            # 1. Primeiro sincronizar os metadados da empresa
            _logger.info(f"Iniciando sincronização de metadados para a regra de negócio {self.id}")
            metadata_result = controller.sync_company_metadata(self.id, env=self.env)

            if not metadata_result or not metadata_result.get('success'):
                error_msg = metadata_result.get('error', 'Erro desconhecido') if metadata_result else 'Erro desconhecido'
                _logger.error(f"Falha na sincronização de metadados: {error_msg}")
                self.write({
                    'sync_status': 'error',
                    'error_message': f"Falha ao sincronizar metadados: {error_msg}"
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': _('Falha ao sincronizar metadados: %s') % error_msg,
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

            # 3. Sincronizar regras de agendamento
            _logger.info(f"Iniciando sincronização de regras de agendamento para a regra de negócio {self.id}")
            scheduling_result = controller.sync_scheduling_rules(self.id, env=self.env)

            if not scheduling_result or not scheduling_result.get('success'):
                _logger.warning(f"Falha na sincronização de regras de agendamento: {scheduling_result.get('error', 'Erro desconhecido')}")
                # Continuar mesmo se a sincronização de regras de agendamento falhar
            else:
                _logger.info("Regras de agendamento sincronizadas com sucesso")

            # 4. Sincronizar documentos de suporte
            _logger.info(f"Iniciando sincronização de documentos de suporte para a regra de negócio {self.id}")
            docs_result = controller.sync_support_documents(self.id, env=self.env)

            if not docs_result or not docs_result.get('success'):
                _logger.warning(f"Falha na sincronização de documentos de suporte: {docs_result.get('error', 'Erro desconhecido')}")
                # Continuar mesmo se a sincronização de documentos falhar
            else:
                _logger.info("Documentos de suporte sincronizados com sucesso")

            # Atualizar a data da última sincronização e status
            self.write({
                'last_sync_date': fields.Datetime.now(),
                'sync_status': 'synced'
            })

            # Retornar mensagem de sucesso
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sincronização Concluída'),
                    'message': _('Regras de negócio sincronizadas com sucesso com o sistema de IA.'),
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
