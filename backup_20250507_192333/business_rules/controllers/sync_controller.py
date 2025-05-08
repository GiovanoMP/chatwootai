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

    @http.route('/business_rules/sync_scheduling_rules', type='json', auth='user')
    def sync_scheduling_rules_http(self, business_rule_id):
        """Endpoint HTTP para sincronizar regras de agendamento"""
        return self.sync_scheduling_rules(business_rule_id)

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
                # Tentar obter a URL diretamente das credenciais
                credentials = env['ai.system.credentials'].sudo().search([('account_id', '=', account_id), ('active', '=', True)], limit=1)
                if credentials and credentials.config_service_url:
                    api_url = credentials.config_service_url
                    if api_url.endswith('/odoo-webhook/'):
                        api_url = api_url[:-13]  # Remove '/odoo-webhook/'
                    elif api_url.endswith('/odoo-webhook'):
                        api_url = api_url[:-12]  # Remove '/odoo-webhook'
                    _logger.info(f"URL do serviço de configuração obtida diretamente: {api_url}")
                else:
                    raise ValueError("URL do serviço de configuração não encontrada. Configure o módulo ai_credentials_manager primeiro.")

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
            # Verificar se a URL é do config-service
            if api_url.endswith('/odoo-webhook'):
                api_url = api_url[:-13]  # Remove '/odoo-webhook'
            elif api_url.endswith('/odoo-webhook/'):
                api_url = api_url[:-14]  # Remove '/odoo-webhook/'

            # Definir o domínio padrão
            domain_name = "default"

            # Usar o endpoint correto do config-service
            sync_endpoint = f"{api_url}/configs/{account_id}/{domain_name}/config"
            _logger.info(f"Usando endpoint do config-service: {sync_endpoint}")

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

                # Obter a chave de API do serviço de configuração
                api_key = None
                credentials = env['ai.system.credentials'].sudo().search([('account_id', '=', account_id), ('active', '=', True)], limit=1)
                if credentials and credentials.config_service_api_key:
                    api_key = credentials.config_service_api_key
                    _logger.info(f"Chave de API obtida das credenciais: {api_key[:5]}...")
                else:
                    # Tentar obter a chave de API dos parâmetros do sistema
                    api_key = env['ir.config_parameter'].sudo().get_param('config_service.api_key', '')
                    if not api_key:
                        api_key = env['ir.config_parameter'].sudo().get_param('config_service_api_key', 'development-api-key')
                    _logger.info(f"Chave de API obtida dos parâmetros do sistema: {api_key[:5]}...")

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
                        'X-Webhook-Signature': signature,
                        'X-API-Key': api_key
                    }
                    _logger.info(f"Assinatura HMAC gerada para o webhook: {signature[:10]}...")
                else:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f"Bearer {token}",
                        'X-API-Key': api_key
                    }
                    _logger.warning("Nenhuma chave secreta configurada para assinatura de webhook")

                # Converter o payload para YAML
                import yaml
                yaml_content = yaml.dump(rules_data, default_flow_style=False)

                # Preparar o payload no formato esperado pelo config-service
                config_service_payload = {
                    "yaml_content": yaml_content
                }

                _logger.info(f"Enviando regras para o config-service: {sync_endpoint}")

                # Fazer a chamada para a API
                response = requests.post(
                    sync_endpoint,
                    headers=headers,
                    json=config_service_payload,
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
            env.cr.execute("""SELECT EXISTS (
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
                # Verificar se estamos sincronizando metadados (usar config_service_url)
                # ou regras de negócio (usar ai_system_url)

                # Primeiro, tentar obter a URL do serviço de configuração
                if hasattr(credentials, 'config_service_url') and credentials.config_service_url:
                    config_url = credentials.config_service_url
                    _logger.info(f"URL do serviço de configuração encontrada para account_id {account_id}: {config_url}")

                    # Remover '/odoo-webhook' do final da URL se existir
                    if config_url.endswith('/odoo-webhook/'):
                        config_url = config_url[:-13]  # Remove '/odoo-webhook/'
                    elif config_url.endswith('/odoo-webhook'):
                        config_url = config_url[:-12]  # Remove '/odoo-webhook'

                    return config_url

                # Se não encontrar URL do serviço de configuração, tentar URL do sistema de IA
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

                    _logger.info(f"URL do sistema de IA encontrada para account_id {account_id}: {ai_system_url}")
                    return ai_system_url
                else:
                    _logger.error(f"Nenhuma URL configurada para account_id {account_id}")
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

            # Obter o account_id correto do módulo ai_credentials_manager
            account_id = self._get_account_id(env)

            # Se não encontrar credenciais, falhar de forma segura
            if not account_id:
                raise ValueError("Nenhuma credencial válida encontrada. Configure o módulo ai_credentials_manager primeiro.")

            # Preparar os metadados da empresa e coleções habilitadas
            result = self._prepare_company_metadata(business_rule)
            metadata = result['metadata']
            enabled_collections = result['enabled_collections']

            # Criar payload completo com metadados e coleções habilitadas
            payload = {
                'company_metadata': metadata,
                'enabled_collections': enabled_collections
            }

            # Sincronizar com o serviço de configuração
            try:
                # Importar o adaptador do serviço de configuração
                from ..models.config_service_adapter import ConfigServiceAdapter

                # Criar uma instância do adaptador
                adapter = ConfigServiceAdapter(env)

                # Sincronizar configuração
                success = adapter.sync_business_rules(account_id, "retail", payload)

                if success:
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
                    _logger.error("Erro ao sincronizar metadados com o serviço de configuração")
            except ImportError as e:
                _logger.error(f"Erro ao importar adaptador do serviço de configuração: {str(e)}")

            # Método antigo de sincronização
            # Chamar a API para sincronizar os metadados
            api_url = self._get_api_url(env)

            # Se não encontrar URL válida, falhar de forma segura
            if not api_url:
                # Tentar obter a URL diretamente das credenciais
                credentials = env['ai.system.credentials'].sudo().search([('account_id', '=', account_id), ('active', '=', True)], limit=1)
                if credentials and credentials.config_service_url:
                    api_url = credentials.config_service_url
                    if api_url.endswith('/odoo-webhook/'):
                        api_url = api_url[:-13]  # Remove '/odoo-webhook/'
                    elif api_url.endswith('/odoo-webhook'):
                        api_url = api_url[:-12]  # Remove '/odoo-webhook'
                    _logger.info(f"URL do serviço de configuração obtida diretamente: {api_url}")
                else:
                    raise ValueError("URL do serviço de configuração não encontrada. Configure o módulo ai_credentials_manager primeiro.")

            # Obter o token de autenticação
            token = self._get_api_token(env)
            _logger.info(f"Token obtido para sincronização de metadados: {token if token else 'None'}")

            if not token:
                raise ValueError("Token de API não encontrado. Configure o módulo ai_credentials_manager primeiro.")

            # Construir o endpoint correto
            # Verificar se a URL é do config-service
            if api_url.endswith('/odoo-webhook'):
                api_url = api_url[:-13]  # Remove '/odoo-webhook'
            elif api_url.endswith('/odoo-webhook/'):
                api_url = api_url[:-14]  # Remove '/odoo-webhook/'

            # Definir o domínio padrão
            domain_name = "default"

            # Usar o endpoint correto do config-service
            sync_metadata_endpoint = f"{api_url}/configs/{account_id}/{domain_name}/metadata"
            _logger.info(f"Usando endpoint do config-service: {sync_metadata_endpoint}")

            # Obter a chave de API do serviço de configuração
            api_key = None
            credentials = env['ai.system.credentials'].sudo().search([('account_id', '=', account_id), ('active', '=', True)], limit=1)
            if credentials and credentials.config_service_api_key:
                api_key = credentials.config_service_api_key
                _logger.info(f"Chave de API obtida das credenciais: {api_key[:5]}...")
            else:
                # Tentar obter a chave de API dos parâmetros do sistema
                api_key = env['ir.config_parameter'].sudo().get_param('config_service.api_key', '')
                if not api_key:
                    api_key = env['ir.config_parameter'].sudo().get_param('config_service_api_key', 'development-api-key')
                _logger.info(f"Chave de API obtida dos parâmetros do sistema: {api_key[:5]}...")

            # Gerar assinatura HMAC para o payload
            webhook_secret = env['ir.config_parameter'].sudo().get_param('webhook_secret_key', '')

            if webhook_secret:
                import hmac
                import hashlib
                import json

                # Converter o payload para string ordenada
                payload_str = json.dumps(payload, sort_keys=True)

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
                    'X-Webhook-Signature': signature,
                    'X-API-Key': api_key
                }
                _logger.info(f"Assinatura HMAC gerada para o webhook: {signature[:10]}...")
            else:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {token}",
                    'X-API-Key': api_key
                }
                _logger.warning("Nenhuma chave secreta configurada para assinatura de webhook")

            # Converter o payload para YAML
            import yaml
            yaml_content = yaml.dump(payload, default_flow_style=False)

            # Preparar o payload no formato esperado pelo config-service
            config_service_payload = {
                "yaml_content": yaml_content
            }

            _logger.info(f"Enviando metadados para o config-service: {sync_metadata_endpoint}")

            # Fazer a chamada para a API
            response = requests.post(
                sync_metadata_endpoint,
                headers=headers,
                json=config_service_payload,
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

        except Exception as e:
            _logger.error("Erro ao sincronizar metadados da empresa: %s", str(e))
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
            business_rule = env['business.rules'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}

            # Chamar a API para sincronizar as regras de agendamento
            api_url = self._get_api_url(env)

            # Se não encontrar URL válida, falhar de forma segura
            if not api_url:
                # Tentar obter a URL diretamente das credenciais
                credentials = env['ai.system.credentials'].sudo().search([('account_id', '=', account_id), ('active', '=', True)], limit=1)
                if credentials and credentials.config_service_url:
                    api_url = credentials.config_service_url
                    if api_url.endswith('/odoo-webhook/'):
                        api_url = api_url[:-13]  # Remove '/odoo-webhook/'
                    elif api_url.endswith('/odoo-webhook'):
                        api_url = api_url[:-12]  # Remove '/odoo-webhook'
                    _logger.info(f"URL do serviço de configuração obtida diretamente: {api_url}")
                else:
                    raise ValueError("URL do serviço de configuração não encontrada. Configure o módulo ai_credentials_manager primeiro.")

            # Obter o token de autenticação
            token = self._get_api_token(env)
            _logger.info(f"Token obtido para sincronização de regras de agendamento: {token if token else 'None'}")

            if not token:
                raise ValueError("Token de API não encontrado. Configure o módulo ai_credentials_manager primeiro.")

            # Construir o endpoint correto
            # Verificar se a URL é do config-service
            if api_url.endswith('/odoo-webhook'):
                api_url = api_url[:-13]  # Remove '/odoo-webhook'
            elif api_url.endswith('/odoo-webhook/'):
                api_url = api_url[:-14]  # Remove '/odoo-webhook/'

            # Definir o domínio padrão
            domain_name = "default"

            # Usar o endpoint correto do config-service
            sync_scheduling_endpoint = f"{api_url}/configs/{account_id}/{domain_name}/scheduling"
            _logger.info(f"Usando endpoint do config-service: {sync_scheduling_endpoint}")

            try:
                # Obter o account_id correto do módulo ai_credentials_manager
                account_id = self._get_account_id(env)

                # Se não encontrar credenciais, falhar de forma segura
                if not account_id:
                    raise ValueError("Nenhuma credencial válida encontrada. Configure o módulo ai_credentials_manager primeiro.")

                # Preparar os dados das regras de agendamento
                scheduling_rules_data = self._prepare_scheduling_rules_data(business_rule)

                # Obter a chave de API do serviço de configuração
                api_key = None
                credentials = env['ai.system.credentials'].sudo().search([('account_id', '=', account_id), ('active', '=', True)], limit=1)
                if credentials and credentials.config_service_api_key:
                    api_key = credentials.config_service_api_key
                    _logger.info(f"Chave de API obtida das credenciais: {api_key[:5]}...")
                else:
                    # Tentar obter a chave de API dos parâmetros do sistema
                    api_key = env['ir.config_parameter'].sudo().get_param('config_service.api_key', '')
                    if not api_key:
                        api_key = env['ir.config_parameter'].sudo().get_param('config_service_api_key', 'development-api-key')
                    _logger.info(f"Chave de API obtida dos parâmetros do sistema: {api_key[:5]}...")

                # Gerar assinatura HMAC para o payload
                webhook_secret = env['ir.config_parameter'].sudo().get_param('webhook_secret_key', '')

                if webhook_secret:
                    import hmac
                    import hashlib
                    import json

                    # Converter o payload para string ordenada
                    payload_str = json.dumps(scheduling_rules_data, sort_keys=True)

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
                        'X-Webhook-Signature': signature,
                        'X-API-Key': api_key
                    }
                    _logger.info(f"Assinatura HMAC gerada para o webhook: {signature[:10]}...")
                else:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f"Bearer {token}",
                        'X-API-Key': api_key
                    }
                    _logger.warning("Nenhuma chave secreta configurada para assinatura de webhook")

                # Converter o payload para YAML
                import yaml
                yaml_content = yaml.dump(scheduling_rules_data, default_flow_style=False)

                # Preparar o payload no formato esperado pelo config-service
                config_service_payload = {
                    "yaml_content": yaml_content
                }

                _logger.info(f"Enviando regras de agendamento para o config-service: {sync_scheduling_endpoint}")

                # Fazer a chamada para a API
                response = requests.post(
                    sync_scheduling_endpoint,
                    headers=headers,
                    json=config_service_payload,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    # Atualizar o status de sincronização
                    business_rule.write({
                        'last_sync_date': fields.Datetime.now(),
                        'sync_status': 'synced'
                    })

                    # Atualizar o status de sincronização das regras de agendamento
                    for rule in business_rule.scheduling_rule_ids:
                        rule.write({'sync_status': 'synced'})

                    return {
                        'success': True,
                        'message': _('Regras de agendamento sincronizadas com sucesso'),
                        'rules_count': len(scheduling_rules_data.get('scheduling_rules', [])),
                        'vectorized_rules': result.get('data', {}).get('vectorized_rules', 0)
                    }
                else:
                    _logger.error("Erro na API ao sincronizar regras de agendamento: %s", response.text)
                    return {'success': False, 'error': f"Erro na API: {response.status_code} - {response.text}"}

            except requests.RequestException as req_err:
                _logger.error("Erro de conexão com a API: %s", str(req_err))
                return {'success': False, 'error': f"Erro de conexão com a API: {str(req_err)}"}

        except Exception as e:
            _logger.error("Erro ao sincronizar regras de agendamento: %s", str(e))
            return {'success': False, 'error': str(e)}

    def _prepare_scheduling_rules_data(self, business_rule):
        """Preparar dados das regras de agendamento para envio ao sistema de IA"""
        # Regras de agendamento ativas e disponíveis no Sistema de IA
        scheduling_rules = []
        for rule in business_rule.scheduling_rule_ids.filtered(lambda r: r.active and r.visible_in_ai):
            # Preparar dados dos dias disponíveis
            days_available = {
                'monday': rule.monday_available,
                'tuesday': rule.tuesday_available,
                'wednesday': rule.wednesday_available,
                'thursday': rule.thursday_available,
                'friday': rule.friday_available,
                'saturday': rule.saturday_available,
                'sunday': rule.sunday_available
            }

            # Preparar dados dos horários
            hours = {
                'weekdays': {
                    'morning_start': rule.morning_start,
                    'morning_end': rule.morning_end,
                    'afternoon_start': rule.afternoon_start,
                    'afternoon_end': rule.afternoon_end,
                    'has_lunch_break': rule.has_lunch_break
                },
                'saturday': {
                    'morning_start': rule.saturday_morning_start,
                    'morning_end': rule.saturday_morning_end,
                    'afternoon_start': rule.saturday_afternoon_start,
                    'afternoon_end': rule.saturday_afternoon_end
                },
                'sunday': {
                    'morning_start': rule.sunday_morning_start,
                    'morning_end': rule.sunday_morning_end,
                    'afternoon_start': rule.sunday_afternoon_start,
                    'afternoon_end': rule.sunday_afternoon_end
                }
            }

            # Preparar dados das políticas
            policies = {
                'cancellation': rule.cancellation_policy or '',
                'rescheduling': rule.rescheduling_policy or ''
            }

            # Preparar dados adicionais
            additional_info = {
                'required_information': rule.required_information or '',
                'confirmation_instructions': rule.confirmation_instructions or ''
            }

            # Adicionar regra à lista
            scheduling_rules.append({
                'rule_id': rule.id,
                'name': rule.name,
                'description': rule.description or '',
                'service_type': rule.service_type,
                'service_type_other': rule.service_type_other or '',
                'duration': rule.duration,
                'min_interval': rule.min_interval,
                'min_advance_time': rule.min_advance_time,
                'max_advance_time': rule.max_advance_time,
                'days_available': days_available,
                'hours': hours,
                'policies': policies,
                'additional_info': additional_info
            })

        return {
            'scheduling_rules': scheduling_rules
        }

    def _prepare_company_metadata(self, business_rule):
        """Preparar metadados da empresa para envio ao sistema de IA"""
        # Informações básicas da empresa
        # Coleções habilitadas (será adicionado ao nível raiz do YAML)
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

        # Garantir que 'products_informations' esteja presente se 'business_rules' estiver habilitado
        if business_rule.use_business_rules and 'products_informations' not in enabled_collections:
            enabled_collections.append('products_informations')

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

        # Retornar metadados e coleções habilitadas
        return {
            'metadata': metadata,
            'enabled_collections': enabled_collections
        }

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

        # Coleções habilitadas
        enabled_collections = [
            collection for collection, enabled in [
                ('business_rules', business_rule.use_business_rules),
                ('scheduling_rules', business_rule.use_scheduling_rules),
                ('delivery_rules', business_rule.use_delivery_rules),
                ('support_documents', business_rule.use_support_documents)
            ] if enabled
        ]

        return {
            'basic_info': basic_info,
            'permanent_rules': permanent_rules,
            'temporary_rules': temporary_rules,
            'enabled_collections': enabled_collections
        }
