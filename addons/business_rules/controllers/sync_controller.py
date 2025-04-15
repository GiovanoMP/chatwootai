# -*- coding: utf-8 -*-

from odoo import http, _, fields
from odoo.http import request
import json
import logging
import requests
from datetime import datetime

_logger = logging.getLogger(__name__)

class BusinessRulesSyncController(http.Controller):

    @http.route('/business_rules/sync', type='json', auth='user')
    def sync_business_rules(self, business_rule_id):
        """Endpoint para sincronizar regras de negócio com o sistema de IA"""
        try:
            business_rule = request.env['business.rules'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}

            # Coletar todas as regras ativas
            rules_data = self._prepare_rules_data(business_rule)

            # Chamar a API para sincronizar as regras
            api_url = self._get_api_url()
            sync_endpoint = f"{api_url}/api/v1/business-rules/sync"

            try:
                # Preparar os dados para a API
                account_id = f"account_{business_rule.id}"
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {self._get_api_token()}"
                }

                # Fazer a chamada para a API
                response = requests.post(
                    sync_endpoint,
                    params={'account_id': account_id},
                    headers=headers,
                    json=rules_data,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    # Atualizar o status de sincronização
                    business_rule.write({
                        'last_sync_date': fields.Datetime.now(),
                        'sync_status': 'synced'
                    })

                    return {
                        'success': True,
                        'message': _('Regras sincronizadas com sucesso'),
                        'rules_count': len(rules_data['permanent_rules']) + len(rules_data['temporary_rules']),
                        'vectorized_rules': result.get('data', {}).get('vectorized_rules', 0)
                    }
                else:
                    _logger.error("Erro na API ao sincronizar regras: %s", response.text)
                    business_rule.write({
                        'last_sync_date': fields.Datetime.now(),
                        'sync_status': 'error'
                    })
                    return {'success': False, 'error': f"Erro na API: {response.status_code} - {response.text}"}

            except requests.RequestException as req_err:
                _logger.error("Erro de conexão com a API: %s", str(req_err))
                business_rule.write({
                    'last_sync_date': fields.Datetime.now(),
                    'sync_status': 'error'
                })
                return {'success': False, 'error': f"Erro de conexão com a API: {str(req_err)}"}

        except Exception as e:
            _logger.error("Erro ao sincronizar regras de negócio: %s", str(e))
            return {'success': False, 'error': str(e)}

    def _get_api_token(self):
        """Obter token de API do módulo ai_credentials_manager"""
        # Verificar se o módulo ai_credentials_manager está instalado
        if not request.env['ir.module.module'].sudo().search([('name', '=', 'ai_credentials_manager'), ('state', '=', 'installed')]):
            # Fallback para o método antigo se o módulo não estiver instalado
            return request.env['ir.config_parameter'].sudo().get_param('business_rules.api_token', 'default_token')

        # Obter credenciais do módulo ai_credentials_manager
        try:
            # Obter o account_id baseado no ID da empresa atual
            company_id = request.env.company.id
            account_id = f"account_{company_id}"

            # Buscar credenciais para este account_id
            credentials = request.env['ai.system.credentials'].sudo().search([('account_id', '=', account_id)], limit=1)

            if credentials:
                # Registrar acesso às credenciais
                request.env['ai.credentials.access.log'].sudo().create({
                    'credential_id': credentials.id,
                    'access_time': fields.Datetime.now(),
                    'user_id': request.env.user.id,
                    'ip_address': request.httprequest.remote_addr,
                    'operation': 'get_token',
                    'success': True
                })

                return credentials.token
            else:
                _logger.warning(f"Credenciais não encontradas para account_id {account_id}")
                # Fallback para o método antigo
                return request.env['ir.config_parameter'].sudo().get_param('business_rules.api_token', 'default_token')
        except Exception as e:
            _logger.error(f"Erro ao obter token do ai_credentials_manager: {str(e)}")
            # Fallback para o método antigo em caso de erro
            return request.env['ir.config_parameter'].sudo().get_param('business_rules.api_token', 'default_token')

    def _get_api_url(self):
        """Obter URL da API do módulo ai_credentials_manager"""
        # Verificar se o módulo ai_credentials_manager está instalado
        if not request.env['ir.module.module'].sudo().search([('name', '=', 'ai_credentials_manager'), ('state', '=', 'installed')]):
            # Fallback para o método antigo se o módulo não estiver instalado
            return request.env['ir.config_parameter'].sudo().get_param('business_rules.api_url', 'http://localhost:8000')

        # Obter credenciais do módulo ai_credentials_manager
        try:
            # Obter o account_id baseado no ID da empresa atual
            company_id = request.env.company.id
            account_id = f"account_{company_id}"

            # Buscar credenciais para este account_id
            credentials = request.env['ai.system.credentials'].sudo().search([('account_id', '=', account_id)], limit=1)

            if credentials:
                # Obter URL do sistema de IA
                ai_system_url = credentials.get_ai_system_url()
                if ai_system_url:
                    return ai_system_url

            # Fallback para o método antigo
            return request.env['ir.config_parameter'].sudo().get_param('business_rules.api_url', 'http://localhost:8000')
        except Exception as e:
            _logger.error(f"Erro ao obter URL da API do ai_credentials_manager: {str(e)}")
            # Fallback para o método antigo em caso de erro
            return request.env['ir.config_parameter'].sudo().get_param('business_rules.api_url', 'http://localhost:8000')

    def _prepare_rules_data(self, business_rule):
        """Preparar dados das regras para envio ao sistema de IA"""
        # Informações básicas da empresa
        basic_info = {
            'company_name': business_rule.name,
            'website': business_rule.website,
            'description': business_rule.description,
            'company_values': business_rule.company_values,
            'business_model': business_rule.business_model,
            'greeting_message': business_rule.greeting_message,
            'communication_style': business_rule.communication_style,
            'emoji_usage': business_rule.emoji_usage,
            'business_hours': {
                'start': business_rule.business_hours_start,
                'end': business_rule.business_hours_end,
                'lunch_break': {
                    'enabled': business_rule.has_lunch_break,
                    'start': business_rule.lunch_break_start if business_rule.has_lunch_break else 0.0,
                    'end': business_rule.lunch_break_end if business_rule.has_lunch_break else 0.0
                },
                'days': {
                    'monday': business_rule.monday,
                    'tuesday': business_rule.tuesday,
                    'wednesday': business_rule.wednesday,
                    'thursday': business_rule.thursday,
                    'friday': business_rule.friday,
                    'saturday': business_rule.saturday,
                    'sunday': business_rule.sunday,
                    'saturday_hours': {
                        'start': business_rule.saturday_hours_start if business_rule.saturday else 0.0,
                        'end': business_rule.saturday_hours_end if business_rule.saturday else 0.0
                    }
                }
            }
        }

        # Regras permanentes ativas
        permanent_rules = []
        for rule in business_rule.rule_ids.filtered(lambda r: r.active):
            permanent_rules.append({
                'name': rule.name,
                'description': rule.description,
                'type': rule.rule_type
            })

        # Regras temporárias ativas e dentro do período de validade
        now = fields.Datetime.now()
        temporary_rules = []
        for rule in business_rule.temporary_rule_ids.filtered(
            lambda r: r.active and
            (not r.date_start or r.date_start <= now) and
            (not r.date_end or r.date_end >= now)
        ):
            temporary_rules.append({
                'name': rule.name,
                'description': rule.description,
                'type': rule.rule_type,
                'date_start': fields.Datetime.to_string(rule.date_start) if rule.date_start else False,
                'date_end': fields.Datetime.to_string(rule.date_end) if rule.date_end else False
            })

        return {
            'basic_info': basic_info,
            'permanent_rules': permanent_rules,
            'temporary_rules': temporary_rules
        }
