# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging
import requests
import json
from datetime import datetime

_logger = logging.getLogger(__name__)

class AIBusinessRulesSyncController(http.Controller):

    @http.route('/ai_business_rules/sync', type='json', auth='user')
    def sync_business_rules_http(self, business_rule_id):
        """Endpoint HTTP para sincronizar regras de negócio"""
        return self.sync_business_rules(business_rule_id)

    @http.route('/ai_business_rules/sync_metadata', type='json', auth='user')
    def sync_company_metadata_http(self, business_rule_id):
        """Endpoint HTTP para sincronizar metadados da empresa"""
        return self.sync_company_metadata(business_rule_id)

    @http.route('/ai_business_rules/sync_scheduling_rules', type='json', auth='user')
    def sync_scheduling_rules_http(self, business_rule_id):
        """Endpoint HTTP para sincronizar regras de agendamento"""
        return self.sync_scheduling_rules(business_rule_id)

    @http.route('/ai_business_rules/sync_support_documents', type='json', auth='user')
    def sync_support_documents_http(self, business_rule_id, document_ids=None):
        """Endpoint HTTP para sincronizar documentos de suporte"""
        return self.sync_support_documents(business_rule_id, document_ids=document_ids)

    def sync_business_rules(self, business_rule_id, env=None):
        """Endpoint para sincronizar regras de negócio com o sistema de IA"""
        try:
            # Obter o ambiente Odoo
            if env is None:
                env = request.env if hasattr(request, 'env') else None

            if env is None:
                raise ValueError("Ambiente Odoo não disponível")

            # Obter a regra de negócio
            business_rule = env['business.rules2'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}

            # Coletar todas as regras ativas
            rules_data = self._prepare_rules_data(business_rule)

            # Obter configurações do webhook
            webhook_url = self._get_webhook_url(env)
            api_token = self._get_api_token(env)
            account_id = self._get_account_id(env)

            # Construir URL completa
            url = f"{webhook_url}/api/v1/business-rules/sync"

            # Preparar headers
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': api_token
            }

            # Preparar payload
            payload = {
                'account_id': account_id,
                'business_rule_id': business_rule_id,
                'rules': rules_data
            }

            # Fazer a requisição
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # Atualizar a data da última sincronização
                business_rule.write({
                    'last_sync_date': fields.Datetime.now()
                })

                return {
                    'success': True,
                    'message': _('Regras sincronizadas com sucesso'),
                    'rules_count': len(rules_data['permanent_rules']) + len(rules_data['temporary_rules']),
                    'vectorized_rules': result.get('data', {}).get('vectorized_rules', 0)
                }
            else:
                _logger.error("Erro na API ao sincronizar regras: %s", response.text)
                return {'success': False, 'error': f"Erro na API: {response.status_code} - {response.text}"}

        except Exception as e:
            _logger.exception("Erro ao sincronizar regras de negócio")
            return {'success': False, 'error': str(e)}

    def sync_company_metadata(self, business_rule_id, env=None):
        """Endpoint para sincronizar metadados da empresa com o sistema de IA"""
        try:
            # Obter o ambiente Odoo
            if env is None:
                env = request.env if hasattr(request, 'env') else None

            if env is None:
                raise ValueError("Ambiente Odoo não disponível")

            # Obter a regra de negócio
            business_rule = env['business.rules2'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}

            # Como o serviço de vetorização não tem um endpoint específico para metadados,
            # vamos sincronizar as regras de negócio, que já incluem os metadados necessários
            return self.sync_business_rules(business_rule_id, env)

        except Exception as e:
            _logger.exception("Erro ao sincronizar metadados da empresa")
            return {'success': False, 'error': str(e)}

    def sync_scheduling_rules(self, business_rule_id, env=None):
        """Endpoint para sincronizar regras de agendamento com o sistema de IA"""
        try:
            # Obter o ambiente Odoo
            if env is None:
                env = request.env if hasattr(request, 'env') else None

            if env is None:
                raise ValueError("Ambiente Odoo não disponível")

            # Obter a regra de negócio
            business_rule = env['business.rules2'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}

            # Coletar todas as regras de agendamento ativas
            scheduling_rules = self._prepare_scheduling_rules_data(business_rule)

            # Obter configurações do webhook
            webhook_url = self._get_webhook_url(env)
            api_token = self._get_api_token(env)
            account_id = self._get_account_id(env)

            # Construir URL completa
            url = f"{webhook_url}/api/v1/scheduling-rules/sync"

            # Preparar headers
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': api_token
            }

            # Preparar payload
            payload = {
                'account_id': account_id,
                'business_rule_id': business_rule_id,
                'scheduling_rules': scheduling_rules
            }

            # Fazer a requisição
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # Atualizar a data da última sincronização
                business_rule.write({
                    'last_sync_date': fields.Datetime.now()
                })

                return {
                    'success': True,
                    'message': _('Regras de agendamento sincronizadas com sucesso'),
                    'rules_count': len(scheduling_rules),
                    'vectorized_rules': result.get('data', {}).get('vectorized_rules', 0)
                }
            else:
                _logger.error("Erro na API ao sincronizar regras de agendamento: %s", response.text)
                return {'success': False, 'error': f"Erro na API: {response.status_code} - {response.text}"}

        except Exception as e:
            _logger.exception("Erro ao sincronizar regras de agendamento")
            return {'success': False, 'error': str(e)}

    def sync_support_documents(self, business_rule_id, env=None, document_ids=None):
        """Endpoint para sincronizar documentos de suporte com o sistema de IA"""
        try:
            # Obter o ambiente Odoo
            if env is None:
                env = request.env if hasattr(request, 'env') else None

            if env is None:
                raise ValueError("Ambiente Odoo não disponível")

            # Obter a regra de negócio
            business_rule = env['business.rules2'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}

            # Coletar todos os documentos de suporte ativos
            documents = self._prepare_support_documents_data(business_rule, document_ids)

            # Obter configurações do webhook
            webhook_url = self._get_webhook_url(env)
            api_token = self._get_api_token(env)
            account_id = self._get_account_id(env)

            # Construir URL completa
            url = f"{webhook_url}/api/v1/support-documents/sync"

            # Preparar headers
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': api_token
            }

            # Preparar payload
            payload = {
                'account_id': account_id,
                'business_rule_id': business_rule_id,
                'documents': documents
            }

            # Fazer a requisição
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # Atualizar a data da última sincronização
                business_rule.write({
                    'last_sync_date': fields.Datetime.now()
                })

                # Se foram especificados IDs de documentos, atualizar a data de sincronização deles também
                if document_ids:
                    docs = env['business.support.document2'].browse(document_ids)
                    docs.write({
                        'last_sync_date': fields.Datetime.now()
                    })

                return {
                    'success': True,
                    'message': _('Documentos de suporte sincronizados com sucesso'),
                    'documents_count': len(documents),
                    'vectorized_documents': result.get('data', {}).get('vectorized_documents', 0)
                }
            else:
                _logger.error("Erro na API ao sincronizar documentos de suporte: %s", response.text)
                return {'success': False, 'error': f"Erro na API: {response.status_code} - {response.text}"}

        except Exception as e:
            _logger.exception("Erro ao sincronizar documentos de suporte")
            return {'success': False, 'error': str(e)}

    def _prepare_rules_data(self, business_rule):
        """Preparar dados das regras de negócio para envio ao sistema de IA"""
        permanent_rules = []
        temporary_rules = []

        # Regras permanentes
        for rule in business_rule.rule_ids.filtered(lambda r: r.active and r.visible_in_ai):
            permanent_rules.append({
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'type': rule.rule_type,
                'last_updated': fields.Datetime.to_string(rule.write_date) if rule.write_date else fields.Datetime.to_string(rule.create_date)
            })

        # Regras temporárias
        for rule in business_rule.temporary_rule_ids.filtered(lambda r: r.active and r.visible_in_ai and r.state == 'active'):
            temporary_rules.append({
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'type': rule.rule_type,
                'start_date': fields.Date.to_string(rule.date_start),
                'end_date': fields.Date.to_string(rule.date_end),
                'last_updated': fields.Datetime.to_string(rule.write_date) if rule.write_date else fields.Datetime.to_string(rule.create_date)
            })

        return {
            'permanent_rules': permanent_rules,
            'temporary_rules': temporary_rules
        }

    def _prepare_scheduling_rules_data(self, business_rule):
        """Preparar dados das regras de agendamento para envio ao sistema de IA"""
        scheduling_rules = []

        for rule in business_rule.scheduling_rule_ids.filtered(lambda r: r.active and r.visible_in_ai):
            scheduling_rules.append({
                'id': rule.id,
                'name': rule.name,
                'description': rule.description or '',
                'service_type': rule.service_type,
                'service_type_other': rule.service_type_other or '',
                'duration': rule.duration,
                'min_interval': rule.min_interval,
                'min_advance_time': rule.min_advance_time,
                'max_advance_time': rule.max_advance_time,
                'days_available': {
                    'monday': rule.monday_available,
                    'tuesday': rule.tuesday_available,
                    'wednesday': rule.wednesday_available,
                    'thursday': rule.thursday_available,
                    'friday': rule.friday_available,
                    'saturday': rule.saturday_available,
                    'sunday': rule.sunday_available
                },
                'hours': {
                    'morning_start': rule.morning_start,
                    'morning_end': rule.morning_end,
                    'afternoon_start': rule.afternoon_start,
                    'afternoon_end': rule.afternoon_end,
                    'has_lunch_break': rule.has_lunch_break
                },
                'special_hours': {
                    'saturday': {
                        'morning_start': rule.saturday_morning_start,
                        'morning_end': rule.saturday_morning_end,
                        'afternoon_start': rule.saturday_afternoon_start,
                        'afternoon_end': rule.saturday_afternoon_end,
                        'has_afternoon': rule.saturday_has_afternoon
                    },
                    'sunday': {
                        'morning_start': rule.sunday_morning_start,
                        'morning_end': rule.sunday_morning_end,
                        'afternoon_start': rule.sunday_afternoon_start,
                        'afternoon_end': rule.sunday_afternoon_end,
                        'has_afternoon': rule.sunday_has_afternoon
                    }
                },
                'policies': {
                    'cancellation': rule.cancellation_policy or '',
                    'rescheduling': rule.rescheduling_policy or '',
                    'required_information': rule.required_information or '',
                    'confirmation_instructions': rule.confirmation_instructions or ''
                },
                'last_updated': fields.Datetime.to_string(rule.write_date) if rule.write_date else fields.Datetime.to_string(rule.create_date)
            })

        return scheduling_rules

    def _prepare_support_documents_data(self, business_rule, document_ids=None):
        """Preparar dados dos documentos de suporte para envio ao sistema de IA"""
        documents = []

        # Filtrar documentos
        if document_ids:
            all_docs = business_rule.support_document_ids.filtered(lambda d: d.id in document_ids and d.active and d.visible_in_ai)
        else:
            all_docs = business_rule.support_document_ids.filtered(lambda d: d.active and d.visible_in_ai)

        for doc in all_docs:
            documents.append({
                'id': doc.id,
                'name': doc.name,
                'document_type': doc.document_type,
                'content': doc.content,
                'last_updated': fields.Datetime.to_string(doc.write_date) if doc.write_date else fields.Datetime.to_string(doc.create_date)
            })

        return documents

    def _prepare_company_metadata(self, business_rule):
        """Preparar metadados da empresa para envio ao sistema de IA"""
        # Coleções habilitadas
        enabled_collections = [
            collection for collection, enabled in [
                ('business_rules', business_rule.use_business_rules),
                ('scheduling_rules', business_rule.use_scheduling_rules),
                ('delivery_rules', business_rule.use_delivery_rules),
                ('support_documents', business_rule.use_support_documents)
            ] if enabled
        ]

        # Garantir que 'business_rules' sempre esteja presente
        if 'business_rules' not in enabled_collections:
            enabled_collections.append('business_rules')

        # Metadados da empresa
        metadata = {
            'name': business_rule.name,
            'description': business_rule.description or '',
            'last_updated': fields.Datetime.to_string(business_rule.write_date) if business_rule.write_date else fields.Datetime.to_string(business_rule.create_date)
        }

        return {
            'metadata': metadata,
            'enabled_collections': enabled_collections
        }

    def _get_webhook_url(self, env):
        """Obter URL do webhook das configurações"""
        return env['ir.config_parameter'].sudo().get_param('ai_business_rules.webhook_url', 'http://localhost:8004')

    def _get_api_token(self, env):
        """Obter token de API das configurações"""
        return env['ir.config_parameter'].sudo().get_param('ai_business_rules.api_token', 'development-api-key')

    def _get_account_id(self, env):
        """Obter account_id das configurações"""
        return env['ir.config_parameter'].sudo().get_param('ai_business_rules.account_id', 'account_1')
