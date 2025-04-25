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
    def sync_business_rules_http(self, business_rule_id):
        """Endpoint HTTP para sincronizar regras de negócio"""
        return self.sync_business_rules(business_rule_id)

    @http.route('/business_rules/sync_metadata', type='json', auth='user')
    def sync_company_metadata_http(self, business_rule_id):
        """Endpoint HTTP para sincronizar metadados da empresa"""
        return self.sync_company_metadata(business_rule_id)

    def sync_business_rules(self, business_rule_id, env=None):
        """Endpoint para sincronizar regras de negócio com o sistema de IA"""
        try:
            # Obter o ambiente Odoo
            if env is None:
                env = request.env if hasattr(request, 'env') else None

            if env is None:
                raise ValueError("Ambiente Odoo não disponível")

            # Obter a regra de negócio
            business_rule = env['business.rules'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}

            # Coletar todas as regras ativas
            rules_data = self._prepare_rules_data(business_rule)

            # Chamar a API para sincronizar as regras
            api_url = self._get_api_url(env)

            # Se não encontrar URL válida, falhar de forma segura
            if not api_url:
                raise ValueError("URL do sistema de IA não encontrada. Configure o módulo ai_credentials_manager primeiro.")

            # Obter o token de autenticação (que é o token de referência do módulo ai_credentials_manager)
            token = self._get_api_token(env)
            _logger.info(f"Token obtido: {token if token else 'None'}")

            if not token:
                # Verificar se há credenciais configuradas
                credentials_count = env['ai.system.credentials'].sudo().search_count([('active', '=', True)])
                _logger.error(f"Número de credenciais ativas encontradas: {credentials_count}")

                if credentials_count > 0:
                    # Verificar se há credenciais com token configurado
                    credentials_with_token = env['ai.system.credentials'].sudo().search_count([('active', '=', True), ('token', '!=', False)])
                    _logger.error(f"Número de credenciais com token configurado: {credentials_with_token}")

                    # Obter detalhes da primeira credencial
                    cred = env['ai.system.credentials'].sudo().search([('active', '=', True)], limit=1)
                    if cred:
                        _logger.error(f"Detalhes da credencial: ID={cred.id}, account_id={cred.account_id}, token={cred.token or 'None'}")

                raise ValueError("Token de API não encontrado. Configure o módulo ai_credentials_manager primeiro.")

            # Construir o endpoint correto
            # A URL base já deve incluir o protocolo e o domínio (ex: http://localhost:8001)
            # O router já está registrado com o prefixo /api/v1 no main.py
            # Não adicionar /webhook para o endpoint de sincronização
            sync_endpoint = f"{api_url}/api/v1/business-rules/sync"

            try:
                # Preparar os dados para a API
                # Obter o account_id correto do módulo ai_credentials_manager
                account_id = self._get_account_id(env)

                # Se não encontrar credenciais, falhar de forma segura
                if not account_id:
                    raise ValueError("Nenhuma credencial válida encontrada. Configure o módulo ai_credentials_manager primeiro.")

                # Obter o token de API
                token = self._get_api_token(env)
                if not token:
                    raise ValueError("Token de API não encontrado. Configure o módulo ai_credentials_manager primeiro.")

                # Coletar todas as regras ativas
                rules_data = self._prepare_rules_data(business_rule)

                # Gerar assinatura HMAC para o payload
                webhook_secret = env['ir.config_parameter'].sudo().get_param('webhook_secret_key', '')

                if webhook_secret:
                    import hmac
                    import hashlib
                    import json

                    # Converter o payload para string ordenada
                    payload_str = json.dumps(rules_data, sort_keys=True)

                    # Gerar a assinatura HMAC
                    signature = hmac.new(
                        webhook_secret.encode(),
                        payload_str.encode(),
                        hashlib.sha256
                    ).hexdigest()

                    # Adicionar a assinatura ao header
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f"Bearer {token}",
                        'X-Webhook-Signature': signature
                    }
                    _logger.info(f"Assinatura HMAC gerada para o webhook: {signature[:10]}...")
                else:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f"Bearer {token}"
                    }
                    _logger.warning("Nenhuma chave secreta configurada para assinatura de webhook")

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

    def _get_account_id(self, env=None):
        """Obter account_id do módulo ai_credentials_manager"""
        # Usar o ambiente fornecido ou o ambiente da requisição
        env = env or request.env

        _logger.info("Iniciando busca por account_id")

        # Verificar se o módulo ai_credentials_manager está instalado
        ai_module = env['ir.module.module'].sudo().search([('name', '=', 'ai_credentials_manager'), ('state', '=', 'installed')])
        if not ai_module:
            # Não usar fallback - exigir que o módulo esteja instalado
            _logger.error("Módulo ai_credentials_manager não está instalado")
            return None

        _logger.info("Módulo ai_credentials_manager está instalado")

        # Obter credenciais do módulo ai_credentials_manager
        try:
            # Verificar se a tabela existe
            table_exists = env.cr.execute("""SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'ai_system_credentials'
            )""")
            exists = env.cr.fetchone()[0]
            _logger.info(f"Tabela ai_system_credentials existe: {exists}")

            if not exists:
                _logger.error("Tabela ai_system_credentials não existe")
                return None

            # Contar credenciais ativas
            credentials_count = env['ai.system.credentials'].sudo().search_count([('active', '=', True)])
            _logger.info(f"Número de credenciais ativas: {credentials_count}")

            # Buscar todas as credenciais ativas
            # Nota: Idealmente, deveríamos filtrar por empresa atual, mas como estamos
            # usando um sistema de tenant único por banco de dados, podemos pegar a primeira
            credentials = env['ai.system.credentials'].sudo().search([('active', '=', True)], limit=1)

            if credentials:
                _logger.info(f"Credencial encontrada: ID={credentials.id}, account_id={credentials.account_id}")
                return credentials.account_id
            else:
                _logger.error("Nenhuma credencial encontrada no módulo ai_credentials_manager")

                # Verificar se há credenciais inativas
                inactive_count = env['ai.system.credentials'].sudo().search_count([('active', '=', False)])
                _logger.info(f"Número de credenciais inativas: {inactive_count}")

                if inactive_count > 0:
                    inactive_cred = env['ai.system.credentials'].sudo().search([('active', '=', False)], limit=1)
                    _logger.info(f"Credencial inativa encontrada: ID={inactive_cred.id}, account_id={inactive_cred.account_id}")

                return None  # Não usar fallback - exigir que existam credenciais
        except Exception as e:
            _logger.error(f"Erro ao obter account_id do ai_credentials_manager: {str(e)}")
            _logger.exception("Traceback completo:")
            return None  # Não usar fallback - falhar de forma segura

    def _get_api_token(self, env=None):
        """Obter token de API do módulo ai_credentials_manager"""
        # Usar o ambiente fornecido ou o ambiente da requisição
        env = env or request.env

        _logger.info("Iniciando busca por token de API")

        # Verificar se o módulo ai_credentials_manager está instalado
        ai_module = env['ir.module.module'].sudo().search([('name', '=', 'ai_credentials_manager'), ('state', '=', 'installed')])
        if not ai_module:
            # Não usar fallback - exigir que o módulo esteja instalado
            _logger.error("Módulo ai_credentials_manager não está instalado")
            return None

        _logger.info("Módulo ai_credentials_manager está instalado")

        # Obter credenciais do módulo ai_credentials_manager
        try:
            # Obter o account_id
            _logger.info("Obtendo account_id")
            account_id = self._get_account_id(env)
            _logger.info(f"Account ID obtido: {account_id if account_id else 'None'}")

            if not account_id:
                _logger.error("Nenhum account_id encontrado para buscar token")
                return None

            # Buscar credenciais para este account_id
            _logger.info(f"Buscando credenciais para account_id: {account_id}")
            credentials = env['ai.system.credentials'].sudo().search([('account_id', '=', account_id), ('active', '=', True)], limit=1)
            _logger.info(f"Credenciais encontradas: {bool(credentials)}")

            if credentials:
                _logger.info(f"Detalhes da credencial: ID={credentials.id}, account_id={credentials.account_id}")

                # Verificar se o token de referência existe
                # Este token é usado tanto para identificar as credenciais nos arquivos YAML
                # quanto para autenticação com o sistema de IA
                _logger.info(f"Token na credencial: {credentials.token or 'None'}")

                if not credentials.token:
                    _logger.error(f"Token de referência não configurado para account_id {account_id}")
                    return None

                # Registrar acesso às credenciais
                _logger.info("Registrando acesso às credenciais")
                try:
                    env['ai.credentials.access.log'].sudo().create({
                        'credential_id': credentials.id,
                        'access_time': fields.Datetime.now(),
                        'user_id': env.user.id,
                        'ip_address': request.httprequest.remote_addr if hasattr(request, 'httprequest') else '0.0.0.0',
                        'operation': 'get_token',
                        'success': True
                    })
                    _logger.info("Acesso registrado com sucesso")
                except Exception as log_error:
                    _logger.error(f"Erro ao registrar acesso: {str(log_error)}")

                _logger.info(f"Token encontrado para account_id {account_id}: {credentials.token}")
                return credentials.token
            else:
                _logger.warning(f"Credenciais não encontradas para account_id {account_id}")
                return None  # Não usar fallback - exigir que existam credenciais
        except Exception as e:
            _logger.error(f"Erro ao obter token do ai_credentials_manager: {str(e)}")
            _logger.exception("Traceback completo:")
            return None  # Não usar fallback - falhar de forma segura

    def _get_api_url(self, env=None):
        """Obter URL da API do módulo ai_credentials_manager"""
        # Usar o ambiente fornecido ou o ambiente da requisição
        env = env or request.env

        # Verificar se o módulo ai_credentials_manager está instalado
        if not env['ir.module.module'].sudo().search([('name', '=', 'ai_credentials_manager'), ('state', '=', 'installed')]):
            # Não usar fallback - exigir que o módulo esteja instalado
            _logger.error("Módulo ai_credentials_manager não está instalado")
            return None

        # Obter credenciais do módulo ai_credentials_manager
        try:
            # Obter o account_id
            account_id = self._get_account_id(env)
            if not account_id:
                _logger.error("Nenhum account_id encontrado para buscar URL")
                return None

            # Buscar credenciais para este account_id
            credentials = env['ai.system.credentials'].sudo().search([('account_id', '=', account_id), ('active', '=', True)], limit=1)

            if credentials:
                # Obter URL do sistema de IA
                # Verificar se o campo webhook_url existe
                if hasattr(credentials, 'webhook_url'):
                    ai_system_url = credentials.webhook_url
                # Se não existir, tentar get_ai_system_url
                elif hasattr(credentials, 'get_ai_system_url'):
                    ai_system_url = credentials.get_ai_system_url()
                # Se não existir, tentar ngrok_url ou ai_system_url
                elif hasattr(credentials, 'use_ngrok') and credentials.use_ngrok and credentials.ngrok_url:
                    ai_system_url = credentials.ngrok_url
                elif hasattr(credentials, 'ai_system_url') and credentials.ai_system_url:
                    ai_system_url = credentials.ai_system_url
                else:
                    ai_system_url = None

                if ai_system_url:
                    # Remover '/webhook' do final da URL se existir
                    if ai_system_url.endswith('/webhook'):
                        ai_system_url = ai_system_url[:-8]  # Remove '/webhook'

                    _logger.info(f"URL encontrada para account_id {account_id}: {ai_system_url}")
                    return ai_system_url
                else:
                    _logger.error(f"URL não configurada para account_id {account_id}")
                    return None

            # Não usar fallback - exigir que existam credenciais com URL válida
            _logger.error(f"Credenciais não encontradas para account_id {account_id}")
            return None
        except Exception as e:
            _logger.error(f"Erro ao obter URL da API do ai_credentials_manager: {str(e)}")
            # Não usar fallback - falhar de forma segura
            return None

    def sync_company_metadata(self, business_rule_id, env=None):
        """Endpoint para sincronizar metadados da empresa com o sistema de IA"""
        try:
            # Obter o ambiente Odoo
            if env is None:
                env = request.env if hasattr(request, 'env') else None

            if env is None:
                raise ValueError("Ambiente Odoo não disponível")

            # Obter a regra de negócio
            business_rule = env['business.rules'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}

            # Chamar a API para sincronizar os metadados
            api_url = self._get_api_url(env)

            # Se não encontrar URL válida, falhar de forma segura
            if not api_url:
                raise ValueError("URL do sistema de IA não encontrada. Configure o módulo ai_credentials_manager primeiro.")

            # Obter o token de autenticação
            token = self._get_api_token(env)
            _logger.info(f"Token obtido para sincronização de metadados: {token if token else 'None'}")

            if not token:
                raise ValueError("Token de API não encontrado. Configure o módulo ai_credentials_manager primeiro.")

            # Construir o endpoint correto
            sync_metadata_endpoint = f"{api_url}/api/v1/business-rules/sync-company-metadata"

            try:
                # Obter o account_id correto do módulo ai_credentials_manager
                account_id = self._get_account_id(env)

                # Se não encontrar credenciais, falhar de forma segura
                if not account_id:
                    raise ValueError("Nenhuma credencial válida encontrada. Configure o módulo ai_credentials_manager primeiro.")

                # Preparar os metadados da empresa
                metadata = self._prepare_company_metadata(business_rule)

                # Gerar assinatura HMAC para o payload
                webhook_secret = env['ir.config_parameter'].sudo().get_param('webhook_secret_key', '')

                if webhook_secret:
                    import hmac
                    import hashlib
                    import json

                    # Converter o payload para string ordenada
                    payload_str = json.dumps(metadata, sort_keys=True)

                    # Gerar a assinatura HMAC
                    signature = hmac.new(
                        webhook_secret.encode(),
                        payload_str.encode(),
                        hashlib.sha256
                    ).hexdigest()

                    # Adicionar a assinatura ao header
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f"Bearer {token}",
                        'X-Webhook-Signature': signature
                    }
                    _logger.info(f"Assinatura HMAC gerada para o webhook: {signature[:10]}...")
                else:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f"Bearer {token}"
                    }
                    _logger.warning("Nenhuma chave secreta configurada para assinatura de webhook")

                # Fazer a chamada para a API
                response = requests.post(
                    sync_metadata_endpoint,
                    params={'account_id': account_id},
                    headers=headers,
                    json=metadata,
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
                        'message': _('Metadados da empresa sincronizados com sucesso'),
                    }
                else:
                    _logger.error("Erro na API ao sincronizar metadados: %s", response.text)
                    return {'success': False, 'error': f"Erro na API: {response.status_code} - {response.text}"}

            except requests.RequestException as req_err:
                _logger.error("Erro de conexão com a API: %s", str(req_err))
                return {'success': False, 'error': f"Erro de conexão com a API: {str(req_err)}"}

        except Exception as e:
            _logger.error("Erro ao sincronizar metadados da empresa: %s", str(e))
            return {'success': False, 'error': str(e)}

    def _prepare_company_metadata(self, business_rule):
        """Preparar metadados da empresa para envio ao sistema de IA"""
        # Informações básicas da empresa
        metadata = {
            'company_info': {
                'company_name': business_rule.name,
                'website': business_rule.website,
                'description': business_rule.description,
                'company_values': business_rule.company_values,
                'business_area': business_rule.business_area,
                'business_area_other': business_rule.business_area_other,
            },
            'customer_service': {
                'greeting_message': business_rule.greeting_message,
                'communication_style': business_rule.communication_style,
                'emoji_usage': business_rule.emoji_usage,
                'inform_promotions_at_start': business_rule.inform_promotions_at_start,
            },
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
            },
            'social_media': {
                'show_website': business_rule.show_website,
                'show_instagram': business_rule.show_instagram,
                'show_facebook': business_rule.show_facebook,
                'instagram_url': business_rule.instagram_url,
                'facebook_url': business_rule.facebook_url,
            }
        }

        return metadata

    def _prepare_rules_data(self, business_rule):
        """Preparar dados das regras para envio ao sistema de IA"""
        # Informações básicas da empresa
        basic_info = {
            'company_name': business_rule.name,
            'website': business_rule.website,
            'description': business_rule.description,
            'company_values': business_rule.company_values,
            'business_area': business_rule.business_area,
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

        # Regras permanentes ativas e disponíveis no Sistema de IA
        permanent_rules = []
        for rule in business_rule.rule_ids.filtered(lambda r: r.active and r.visible_in_ai):
            permanent_rules.append({
                'name': rule.name,
                'description': rule.description,
                'type': rule.rule_type
            })

        # Regras temporárias ativas, dentro do período de validade e disponíveis no Sistema de IA
        now = fields.Datetime.now()
        temporary_rules = []
        for rule in business_rule.temporary_rule_ids.filtered(
            lambda r: r.active and r.visible_in_ai and
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
