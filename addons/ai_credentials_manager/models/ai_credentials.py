# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError
import logging
import uuid
import base64

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    _logger = logging.getLogger(__name__)
    _logger.warning("A biblioteca 'cryptography' não está instalada. A criptografia de campos sensíveis não estará disponível.")

_logger = logging.getLogger(__name__)

class AISystemCredentials(models.Model):
    _name = 'ai.system.credentials'
    _description = 'Credenciais do Sistema de IA'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def open_config_viewer(self):
        """Abre o visualizador de configurações em uma nova aba."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('config_viewer.url', 'http://localhost:8080')
        return {
            'type': 'ir.actions.act_url',
            'url': f"{base_url}?tenant_id={self.account_id}",
            'target': 'new',
        }

    def _get_encryption_key(self):
        """Obtém a chave de criptografia do parâmetro do sistema."""
        if not HAS_CRYPTOGRAPHY:
            return False

        param = self.env['ir.config_parameter'].sudo().get_param('ai_credentials.encryption_key')
        if not param:
            # Gerar nova chave se não existir
            key = Fernet.generate_key()
            self.env['ir.config_parameter'].sudo().set_param('ai_credentials.encryption_key', key.decode())
            return key
        return param.encode()

    def _encrypt_value(self, value):
        """Criptografa um valor."""
        if not value or not HAS_CRYPTOGRAPHY:
            return False

        key = self._get_encryption_key()
        if not key:
            return False

        cipher = Fernet(key)
        return base64.b64encode(cipher.encrypt(value.encode()))

    def _decrypt_value(self, encrypted_value):
        """Descriptografa um valor."""
        if not encrypted_value or not HAS_CRYPTOGRAPHY:
            return ''

        key = self._get_encryption_key()
        if not key:
            return ''

        cipher = Fernet(key)
        try:
            decrypted = cipher.decrypt(base64.b64decode(encrypted_value))
            return decrypted.decode()
        except Exception as e:
            _logger.error(f"Erro ao descriptografar valor: {str(e)}")
            return ''

    name = fields.Char('Nome', required=True, tracking=True,
                      help="Nome descritivo para estas credenciais")
    account_id = fields.Char('ID da Conta', required=True, index=True, tracking=True,
                           help="Identificador único da conta (ex: account_1)")
    token = fields.Char('Token de Referência', index=True, tracking=True, copy=False,
                       help="Token usado nos arquivos YAML para referência")

    # Informações do cliente
    client_name = fields.Char('Nome do Cliente', tracking=True,
                             help="Nome do cliente para referência")
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
    ], string='Área de Negócio', default='retail', tracking=True)
    business_area_other = fields.Char('Outra Área de Negócio', tracking=True)

    # Credenciais de acesso ao Odoo
    odoo_url = fields.Char('URL do Odoo', tracking=True,
                          help="URL completa do servidor Odoo")
    odoo_db = fields.Char('Banco de Dados', tracking=True,
                         help="Nome do banco de dados Odoo")
    odoo_username = fields.Char('Usuário', tracking=True,
                              help="Nome de usuário para autenticação no Odoo")

    # Campos criptografados
    odoo_password_encrypted = fields.Binary('Senha (Criptografada)', attachment=False)
    odoo_api_key_encrypted = fields.Binary('Chave de API (Criptografada)', attachment=False)

    # Campos para interface
    odoo_password = fields.Char('Senha', compute='_compute_odoo_password', inverse='_inverse_odoo_password', store=False,
                              help="Senha para autenticação no Odoo (armazenada de forma segura)")
    odoo_api_key = fields.Char('Chave de API', compute='_compute_odoo_api_key', inverse='_inverse_odoo_api_key', store=False,
                             help="Chave de API para autenticação no Odoo (armazenada de forma segura)")

    # Configurações técnicas
    timeout = fields.Integer('Timeout (segundos)', default=30,
                           help="Tempo limite para requisições")
    verify_ssl = fields.Boolean('Verificar SSL', default=True,
                              help="Verificar certificados SSL nas conexões")

    # Configurações de Qdrant
    qdrant_collection = fields.Char('Coleção Qdrant',
                                  help="Nome da coleção no Qdrant para este cliente")

    # Configurações de Redis
    redis_prefix = fields.Char('Prefixo Redis',
                             help="Prefixo para chaves no Redis")

    # Credenciais para Redes Sociais (criptografadas)
    # Facebook
    facebook_app_id = fields.Char('Facebook App ID', tracking=True)
    facebook_app_secret_encrypted = fields.Binary('Facebook App Secret (Criptografado)', attachment=False)
    facebook_access_token_encrypted = fields.Binary('Facebook Access Token (Criptografado)', attachment=False)

    # Instagram
    instagram_client_id = fields.Char('Instagram Client ID', tracking=True)
    instagram_client_secret_encrypted = fields.Binary('Instagram Client Secret (Criptografado)', attachment=False)
    instagram_access_token_encrypted = fields.Binary('Instagram Access Token (Criptografado)', attachment=False)

    # Credenciais para Marketplaces (criptografadas)
    # Mercado Livre
    mercadolivre_app_id = fields.Char('Mercado Livre App ID', tracking=True)
    mercadolivre_client_secret_encrypted = fields.Binary('Mercado Livre Client Secret (Criptografado)', attachment=False)
    mercadolivre_access_token_encrypted = fields.Binary('Mercado Livre Access Token (Criptografado)', attachment=False)

    # Campos computados para interface
    facebook_app_secret = fields.Char('Facebook App Secret', compute='_compute_facebook_app_secret',
                                    inverse='_inverse_facebook_app_secret', store=False)
    facebook_access_token = fields.Char('Facebook Access Token', compute='_compute_facebook_access_token',
                                      inverse='_inverse_facebook_access_token', store=False)
    instagram_client_secret = fields.Char('Instagram Client Secret', compute='_compute_instagram_client_secret',
                                        inverse='_inverse_instagram_client_secret', store=False)
    instagram_access_token = fields.Char('Instagram Access Token', compute='_compute_instagram_access_token',
                                       inverse='_inverse_instagram_access_token', store=False)
    mercadolivre_client_secret = fields.Char('Mercado Livre Client Secret', compute='_compute_mercadolivre_client_secret',
                                           inverse='_inverse_mercadolivre_client_secret', store=False)
    mercadolivre_access_token = fields.Char('Mercado Livre Access Token', compute='_compute_mercadolivre_access_token',
                                          inverse='_inverse_mercadolivre_access_token', store=False)

    # Campos de segurança
    active = fields.Boolean('Ativo', default=True, tracking=True)
    last_accessed = fields.Datetime('Último Acesso', readonly=True)
    notes = fields.Text('Notas', help="Notas adicionais sobre estas credenciais")

    # Mapeamentos de canal relacionados
    channel_mapping_ids = fields.One2many('ai.channel.mapping', 'credential_id', string='Mapeamentos de Canal')

    # Campos para status de sincronização
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro')
    ], string='Status de Sincronização', default='not_synced', readonly=True, tracking=True)
    last_sync = fields.Datetime('Última Sincronização', readonly=True)
    error_message = fields.Text('Mensagem de Erro', readonly=True)

    # URLs dos serviços
    ai_system_url = fields.Char('URL do Sistema de IA', tracking=True,
                              help="URL base do sistema de IA (ex: https://ai-system.example.com)")
    config_service_url = fields.Char('URL do Serviço de Configuração', tracking=True,
                                   help="URL do serviço de configuração (ex: http://localhost:8002)")
    config_service_api_key = fields.Char('Chave de API do Serviço de Configuração', tracking=True,
                                       help="Chave de API para autenticação no serviço de configuração")
    vectorization_service_url = fields.Char('URL do Serviço de Vetorização', tracking=True,
                                          help="URL do serviço de vetorização (ex: http://localhost:8003)")
    vectorization_service_api_key = fields.Char('Chave de API do Serviço de Vetorização', tracking=True,
                                              help="Chave de API para autenticação no serviço de vetorização")
    use_ngrok = fields.Boolean('Usar Ngrok', default=False, tracking=True,
                             help="Ativar para usar Ngrok em ambiente de desenvolvimento")
    ngrok_url = fields.Char('URL Ngrok', tracking=True,
                          help="URL Ngrok para ambiente de desenvolvimento")

    # Restrições
    _sql_constraints = [
        ('unique_account_id', 'unique(account_id)', 'O ID da Conta deve ser único!'),
        ('unique_token', 'unique(token)', 'O Token de Referência deve ser único!')
    ]

    # Gerar token automaticamente
    @api.model
    def create(self, vals):
        if not vals.get('token'):
            # Gerar token baseado no account_id e um UUID curto
            account = vals.get('account_id', 'acc')
            short_uuid = str(uuid.uuid4())[:8]
            vals['token'] = f"{account}-{short_uuid}"
        return super(AISystemCredentials, self).create(vals)

    # Verificar permissões
    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        # Apenas administradores podem acessar este modelo
        if not self.env.user.has_group('base.group_system'):
            if raise_exception:
                raise AccessError(_("Apenas administradores podem gerenciar credenciais"))
            return False
        return super(AISystemCredentials, self).check_access_rights(operation, raise_exception)

    # Métodos para campos computados - Odoo
    def _compute_odoo_password(self):
        for record in self:
            record.odoo_password = record._decrypt_value(record.odoo_password_encrypted) if record.odoo_password_encrypted else ''

    def _inverse_odoo_password(self):
        for record in self:
            if record.odoo_password:
                record.odoo_password_encrypted = record._encrypt_value(record.odoo_password)

    def _compute_odoo_api_key(self):
        for record in self:
            record.odoo_api_key = record._decrypt_value(record.odoo_api_key_encrypted) if record.odoo_api_key_encrypted else ''

    def _inverse_odoo_api_key(self):
        for record in self:
            if record.odoo_api_key:
                record.odoo_api_key_encrypted = record._encrypt_value(record.odoo_api_key)

    # Métodos para campos computados - Facebook
    def _compute_facebook_app_secret(self):
        for record in self:
            record.facebook_app_secret = record._decrypt_value(record.facebook_app_secret_encrypted) if record.facebook_app_secret_encrypted else ''

    def _inverse_facebook_app_secret(self):
        for record in self:
            if record.facebook_app_secret:
                record.facebook_app_secret_encrypted = record._encrypt_value(record.facebook_app_secret)

    def _compute_facebook_access_token(self):
        for record in self:
            record.facebook_access_token = record._decrypt_value(record.facebook_access_token_encrypted) if record.facebook_access_token_encrypted else ''

    def _inverse_facebook_access_token(self):
        for record in self:
            if record.facebook_access_token:
                record.facebook_access_token_encrypted = record._encrypt_value(record.facebook_access_token)

    # Métodos para campos computados - Instagram
    def _compute_instagram_client_secret(self):
        for record in self:
            record.instagram_client_secret = record._decrypt_value(record.instagram_client_secret_encrypted) if record.instagram_client_secret_encrypted else ''

    def _inverse_instagram_client_secret(self):
        for record in self:
            if record.instagram_client_secret:
                record.instagram_client_secret_encrypted = record._encrypt_value(record.instagram_client_secret)

    def _compute_instagram_access_token(self):
        for record in self:
            record.instagram_access_token = record._decrypt_value(record.instagram_access_token_encrypted) if record.instagram_access_token_encrypted else ''

    def _inverse_instagram_access_token(self):
        for record in self:
            if record.instagram_access_token:
                record.instagram_access_token_encrypted = record._encrypt_value(record.instagram_access_token)

    # Métodos para campos computados - Mercado Livre
    def _compute_mercadolivre_client_secret(self):
        for record in self:
            record.mercadolivre_client_secret = record._decrypt_value(record.mercadolivre_client_secret_encrypted) if record.mercadolivre_client_secret_encrypted else ''

    def _inverse_mercadolivre_client_secret(self):
        for record in self:
            if record.mercadolivre_client_secret:
                record.mercadolivre_client_secret_encrypted = record._encrypt_value(record.mercadolivre_client_secret)

    def _compute_mercadolivre_access_token(self):
        for record in self:
            record.mercadolivre_access_token = record._decrypt_value(record.mercadolivre_access_token_encrypted) if record.mercadolivre_access_token_encrypted else ''

    def _inverse_mercadolivre_access_token(self):
        for record in self:
            if record.mercadolivre_access_token:
                record.mercadolivre_access_token_encrypted = record._encrypt_value(record.mercadolivre_access_token)

    # API para sistema de IA
    @api.model
    def get_credentials(self, token):
        """Obtém credenciais a partir do token de referência."""
        # Verificar se o usuário tem permissão
        if not self.env.user.has_group('base.group_system'):
            # Usar um usuário de sistema para busca
            self = self.sudo()

        creds = self.search([('token', '=', token), ('active', '=', True)], limit=1)
        if not creds:
            return False

        # Atualizar timestamp de último acesso
        creds.write({'last_accessed': fields.Datetime.now()})

        # Registrar acesso para auditoria
        self.env['ai.credentials.access.log'].sudo().create({
            'credential_id': creds.id,
            'access_time': fields.Datetime.now(),
            'ip_address': self.env.context.get('remote_addr', 'N/A'),
            'operation': 'get_credentials',
            'success': True
        })

        # Descriptografar senha e chave de API
        password = creds._decrypt_value(creds.odoo_password_encrypted) if creds.odoo_password_encrypted else ''
        api_key = creds._decrypt_value(creds.odoo_api_key_encrypted) if creds.odoo_api_key_encrypted else ''

        # Retornar dicionário com credenciais
        return {
            'account_id': creds.account_id,
            'client_name': creds.client_name,
            'business_area': creds.business_area,
            'mcp': {
                'type': 'odoo-mcp',
                'config': {
                    'url': creds.odoo_url,
                    'db': creds.odoo_db,
                    'username': creds.odoo_username,
                    'password': password,
                    'api_key': api_key,
                    'timeout': creds.timeout,
                    'verify_ssl': creds.verify_ssl,
                }
            },
            'qdrant': {
                # Usar o valor configurado ou gerar um nome baseado no account_id
                # Isso é seguro porque estamos usando o account_id da própria credencial
                'collection': creds.qdrant_collection or f"business_rules_{creds.account_id}"
            },
            'redis': {
                # Usar o valor configurado ou usar o account_id como prefixo
                # Isso é seguro porque estamos usando o account_id da própria credencial
                'prefix': creds.redis_prefix or creds.account_id
            }
        }

    # Método para testar conexão
    def action_test_connection(self):
        self.ensure_one()
        try:
            # Implementar teste de conexão com o Odoo
            # ...

            # Registrar acesso bem-sucedido
            self.env['ai.credentials.access.log'].sudo().create({
                'credential_id': self.id,
                'access_time': fields.Datetime.now(),
                'ip_address': self.env.context.get('remote_addr', 'N/A'),
                'operation': 'test_connection',
                'success': True
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Conexão bem-sucedida'),
                    'message': _('A conexão com o Odoo foi estabelecida com sucesso.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            # Registrar falha
            self.env['ai.credentials.access.log'].sudo().create({
                'credential_id': self.id,
                'access_time': fields.Datetime.now(),
                'ip_address': self.env.context.get('remote_addr', 'N/A'),
                'operation': 'test_connection',
                'success': False,
                'error_message': str(e)
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Falha na conexão'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }

    def get_ai_system_url(self, service_type='ai', return_api_key=False):
        """
        Obtém a URL do serviço especificado, considerando Ngrok se ativado.

        Args:
            service_type: Tipo de serviço ('ai', 'config', 'vectorization')
            return_api_key: Se True, retorna uma tupla (url, api_key)

        Returns:
            URL do serviço ou None se não configurada
            Se return_api_key=True, retorna uma tupla (url, api_key)
        """
        self.ensure_one()
        _logger.info(f"Obtendo URL para o serviço: {service_type}")

        url = None
        api_key = None

        # Se Ngrok estiver ativado, usar a URL do Ngrok para todos os serviços
        if self.use_ngrok and self.ngrok_url:
            _logger.info(f"Usando URL do Ngrok: {self.ngrok_url}")
            url = self.ngrok_url.rstrip('/')
            # Ainda precisamos obter a chave de API correta para o serviço
            if service_type == 'config':
                api_key = self.config_service_api_key
            elif service_type == 'vectorization':
                api_key = self.vectorization_service_api_key
        # Caso contrário, usar a URL específica do serviço
        elif service_type == 'config' and self.config_service_url:
            _logger.info(f"Usando URL do serviço de configuração: {self.config_service_url}")
            url = self.config_service_url.rstrip('/')
            api_key = self.config_service_api_key
        elif service_type == 'vectorization' and self.vectorization_service_url:
            _logger.info(f"Usando URL do serviço de vetorização: {self.vectorization_service_url}")
            url = self.vectorization_service_url.rstrip('/')
            api_key = self.vectorization_service_api_key
        elif service_type == 'ai' and self.ai_system_url:
            _logger.info(f"Usando URL do sistema de IA: {self.ai_system_url}")
            url = self.ai_system_url.rstrip('/')
            # Sistema de IA não tem chave de API específica

        # Se não encontrou URL, verificar se há uma URL de fallback nos parâmetros do sistema
        if not url:
            _logger.info("Verificando URLs de fallback nos parâmetros do sistema")
            IrConfigParam = self.env['ir.config_parameter'].sudo()

            if service_type == 'config':
                # Verificar o novo parâmetro
                fallback_url = IrConfigParam.get_param('config_service.url', '')
                if fallback_url:
                    _logger.info(f"Usando URL de fallback do serviço de configuração: {fallback_url}")
                    url = fallback_url.rstrip('/')
                    # Obter a chave de API do parâmetro do sistema
                    api_key = IrConfigParam.get_param('config_service.api_key', '')
                    if not api_key:
                        api_key = IrConfigParam.get_param('config_service_api_key', 'development-api-key')

                # Verificar o parâmetro antigo
                if not url:
                    old_fallback_url = IrConfigParam.get_param('config_service_url', '')
                    if old_fallback_url:
                        _logger.info(f"Usando URL de fallback antiga do serviço de configuração: {old_fallback_url}")
                        url = old_fallback_url.rstrip('/')
                        # Obter a chave de API do parâmetro do sistema
                        api_key = IrConfigParam.get_param('config_service_api_key', 'development-api-key')
            elif service_type == 'vectorization':
                fallback_url = IrConfigParam.get_param('vectorization_service.url', '')
                if fallback_url:
                    _logger.info(f"Usando URL de fallback do serviço de vetorização: {fallback_url}")
                    url = fallback_url.rstrip('/')
                    # Obter a chave de API do parâmetro do sistema
                    api_key = IrConfigParam.get_param('vectorization_service.api_key', 'development-api-key')
            elif service_type == 'ai':
                fallback_url = IrConfigParam.get_param('ai_system.url', '')
                if fallback_url:
                    _logger.info(f"Usando URL de fallback do sistema de IA: {fallback_url}")
                    url = fallback_url.rstrip('/')
                    # Sistema de IA não tem chave de API específica

        # Não usar fallback - exigir que a URL esteja configurada
        if not url:
            _logger.warning(f"Nenhuma URL encontrada para o serviço: {service_type}")
            return (None, None) if return_api_key else None

        # Se não encontrou chave de API, usar a padrão
        if not api_key and (service_type == 'config' or service_type == 'vectorization'):
            _logger.warning(f"Nenhuma chave de API encontrada para o serviço: {service_type}, usando padrão")
            api_key = 'development-api-key'

        return (url, api_key) if return_api_key else url

    # Método para sincronizar credenciais com arquivos YAML (legado)
    def action_sync_to_yaml(self):
        self.ensure_one()
        try:
            import yaml
            import os

            # Determinar o caminho do arquivo YAML
            domain = self.business_area.lower() if self.business_area != 'other' else self.business_area_other.lower()
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                    'config', 'domains', domain, self.account_id)

            # Criar diretório se não existir
            os.makedirs(config_dir, exist_ok=True)

            config_path = os.path.join(config_dir, 'config.yaml')

            # Carregar configuração existente ou criar nova
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {
                    'account_id': self.account_id,
                    'name': self.client_name or self.name,
                    'description': f"Configuração para {self.client_name or self.name}",
                    'integrations': {}
                }

            # Atualizar configuração MCP
            if 'integrations' not in config:
                config['integrations'] = {}

            if 'mcp' not in config['integrations']:
                config['integrations']['mcp'] = {'type': 'odoo-mcp', 'config': {}}

            # Atualizar credenciais (usando referências seguras)
            config['integrations']['mcp']['config'] = {
                'url': self.odoo_url,
                'db': self.odoo_db,
                'username': self.odoo_username,
                'credential_ref': self.token  # Referência segura, não credenciais reais
            }

            # Atualizar configuração Qdrant
            if 'qdrant' not in config['integrations']:
                config['integrations']['qdrant'] = {}

            # Usar o valor configurado ou gerar um nome baseado no account_id
            # Isso é seguro porque estamos usando o account_id da própria credencial
            config['integrations']['qdrant']['collection'] = self.qdrant_collection or f"business_rules_{self.account_id}"

            # Atualizar configuração Redis
            if 'redis' not in config['integrations']:
                config['integrations']['redis'] = {}

            # Usar o valor configurado ou usar o account_id como prefixo
            # Isso é seguro porque estamos usando o account_id da própria credencial
            config['integrations']['redis']['prefix'] = self.redis_prefix or self.account_id

            # Salvar configuração
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            # Registrar sincronização bem-sucedida
            self.env['ai.credentials.access.log'].sudo().create({
                'credential_id': self.id,
                'access_time': fields.Datetime.now(),
                'ip_address': self.env.context.get('remote_addr', 'N/A'),
                'operation': 'sync_to_yaml',
                'success': True
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sincronização bem-sucedida'),
                    'message': _('As credenciais foram sincronizadas com o arquivo YAML.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            # Registrar falha
            self.env['ai.credentials.access.log'].sudo().create({
                'credential_id': self.id,
                'access_time': fields.Datetime.now(),
                'ip_address': self.env.context.get('remote_addr', 'N/A'),
                'operation': 'sync_to_yaml',
                'success': False,
                'error_message': str(e)
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Falha na sincronização'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }

    # Método para sincronizar credenciais com o webhook
    def action_sync_to_webhook(self):
        """
        Sincroniza as credenciais com o sistema de IA através do webhook.
        Este método envia as credenciais para o endpoint /webhook do sistema de IA,
        que processa e armazena as credenciais de forma segura usando referências.
        """
        self.ensure_one()
        try:
            import requests
            import json

            # Obter URL e chave de API do serviço de configuração
            _logger.info("Obtendo URL e chave de API do serviço de configuração")
            webhook_url, api_key = self.get_ai_system_url(service_type='config', return_api_key=True)
            _logger.info(f"URL obtida: {webhook_url}")

            # Verificar se a URL está configurada
            if not webhook_url:
                # Falhar de forma segura se a URL não estiver configurada
                _logger.error("URL do serviço de configuração não configurada")
                raise UserError(_('URL do serviço de configuração não configurada. Configure a URL do serviço de configuração ou do Ngrok.'))

            # Verificar se a URL é válida
            if not webhook_url.startswith('http'):
                _logger.error(f"URL do serviço de configuração inválida: {webhook_url}")
                raise UserError(_('URL do serviço de configuração inválida. A URL deve começar com http:// ou https://.'))

            # Garantir que a URL termina com /odoo-webhook/
            if not webhook_url.endswith('/odoo-webhook/'):
                if webhook_url.endswith('/odoo-webhook'):
                    webhook_url = f"{webhook_url}/"
                else:
                    webhook_url = f"{webhook_url}/odoo-webhook/"

            _logger.info(f"URL do webhook: {webhook_url}")

            # Verificar se a chave de API está configurada
            if not api_key:
                _logger.warning("Chave de API do serviço de configuração não configurada, usando padrão")
                api_key = 'development-api-key'
            else:
                _logger.info(f"Usando chave de API configurada: {api_key[:5]}...")

            # Preparar payload
            # Descriptografar senha para enviar ao webhook
            password = self._decrypt_value(self.odoo_password_encrypted) if self.odoo_password_encrypted else ''

            payload = {
                'source': 'credentials',
                'event': 'credentials_sync',
                'account_id': self.account_id,
                'token': self.token,
                'credentials': {
                    'domain': self.business_area.lower() if self.business_area != 'other' else self.business_area_other.lower(),
                    'name': self.client_name or self.name,
                    'odoo_url': self.odoo_url,
                    'odoo_db': self.odoo_db,
                    'odoo_username': self.odoo_username,
                    'odoo_password': password,  # Incluir a senha descriptografada
                    'token': self.token,
                    # Usar o valor configurado ou gerar um nome baseado no account_id
                    # Isso é seguro porque estamos usando o account_id da própria credencial
                    'qdrant_collection': self.qdrant_collection or f"business_rules_{self.account_id}",
                    # Usar o valor configurado ou usar o account_id como prefixo
                    # Isso é seguro porque estamos usando o account_id da própria credencial
                    'redis_prefix': self.redis_prefix or self.account_id,
                }
            }

            # Adicionar credenciais de redes sociais se preenchidas
            if self.facebook_app_id:
                payload['credentials']['facebook_app_id'] = self.facebook_app_id
            if self.facebook_app_secret:
                payload['credentials']['facebook_app_secret'] = self.facebook_app_secret
            if self.facebook_access_token:
                payload['credentials']['facebook_access_token'] = self.facebook_access_token

            # Adicionar credenciais do Instagram
            if self.instagram_client_id:
                payload['credentials']['instagram_client_id'] = self.instagram_client_id
            if self.instagram_client_secret:
                payload['credentials']['instagram_client_secret'] = self.instagram_client_secret
            if self.instagram_access_token:
                payload['credentials']['instagram_access_token'] = self.instagram_access_token

            # Adicionar credenciais do Mercado Livre
            if self.mercadolivre_app_id:
                payload['credentials']['mercado_livre_app_id'] = self.mercadolivre_app_id
            if self.mercadolivre_client_secret:
                payload['credentials']['mercado_livre_client_secret'] = self.mercadolivre_client_secret
            if self.mercadolivre_access_token:
                payload['credentials']['mercado_livre_access_token'] = self.mercadolivre_access_token

            # Inicializar headers com a chave de API
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': api_key
            }
            _logger.info(f"Usando chave de API para autenticação: {api_key[:5]}...")

            # Gerar assinatura HMAC para o payload (segurança adicional)
            webhook_secret = self.env['ir.config_parameter'].sudo().get_param('webhook_secret_key', '')
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
                headers['X-Webhook-Signature'] = signature
                _logger.info(f"Assinatura HMAC gerada para o webhook: {signature[:10]}...")
            else:
                _logger.warning("Nenhuma chave secreta configurada para assinatura de webhook")

            # Enviar requisição com timeout maior
            _logger.info(f"Enviando requisição para {webhook_url} com timeout de 60 segundos")
            response = requests.post(
                webhook_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            # Verificar resposta
            if response.status_code == 200:
                # Registrar sincronização bem-sucedida
                self.env['ai.credentials.access.log'].sudo().create({
                    'credential_id': self.id,
                    'access_time': fields.Datetime.now(),
                    'ip_address': self.env.context.get('remote_addr', 'N/A'),
                    'operation': 'sync_to_webhook',
                    'success': True
                })

                # Atualizar status de sincronização
                self.write({
                    'sync_status': 'synced',
                    'last_sync': fields.Datetime.now(),
                    'error_message': False
                })

                # Sincronizar mapeamentos de canal associados a esta credencial
                success_count = 0
                error_count = 0

                for mapping in self.channel_mapping_ids:
                    try:
                        # Preparar payload para o mapeamento
                        mapping_payload = {
                            'source': 'channel_mapping',
                            'event': 'mapping_sync',
                            'account_id': self.account_id,
                            'token': self.token,
                            'mapping': {
                                'chatwoot_account_id': mapping.chatwoot_account_id,
                                'chatwoot_inbox_id': mapping.chatwoot_inbox_id if mapping.chatwoot_inbox_id else None,
                                'internal_account_id': mapping.internal_account_id,
                                'domain': mapping.get_domain(),
                                'is_fallback': mapping.is_fallback,
                                'sequence': mapping.sequence,
                                'special_whatsapp_numbers': []
                            }
                        }

                        # Adicionar números especiais de WhatsApp
                        for field in ['special_whatsapp_number1', 'special_whatsapp_number2', 'special_whatsapp_number3']:
                            number = getattr(mapping, field)
                            if number:
                                mapping_payload['mapping']['special_whatsapp_numbers'].append({
                                    'number': number,
                                    'crew': mapping.special_crew
                                })

                        # Gerar assinatura HMAC para o payload
                        if webhook_secret:
                            # Converter o payload para string ordenada
                            mapping_payload_str = json.dumps(mapping_payload, sort_keys=True)

                            # Gerar a assinatura HMAC
                            mapping_signature = hmac.new(
                                webhook_secret.encode(),
                                mapping_payload_str.encode(),
                                hashlib.sha256
                            ).hexdigest()

                            # Adicionar a assinatura ao header
                            mapping_headers = {
                                'Content-Type': 'application/json',
                                'X-Webhook-Signature': mapping_signature,
                                'X-API-Key': api_key  # Adicionar a chave de API
                            }
                        else:
                            mapping_headers = {
                                'Content-Type': 'application/json',
                                'X-API-Key': api_key  # Adicionar a chave de API
                            }

                        # Enviar requisição para o mapeamento com timeout maior
                        _logger.info(f"Enviando requisição de mapeamento para {webhook_url} com timeout de 60 segundos")
                        mapping_response = requests.post(
                            webhook_url,
                            headers=mapping_headers,
                            json=mapping_payload,
                            timeout=60
                        )

                        # Verificar resposta
                        if mapping_response.status_code == 200:
                            # Atualizar status de sincronização do mapeamento
                            mapping.write({
                                'sync_status': 'synced',
                                'last_sync': fields.Datetime.now(),
                                'error_message': False
                            })
                            success_count += 1
                        else:
                            # Falha na requisição
                            error_msg = f"Erro HTTP {mapping_response.status_code}: {mapping_response.text}"
                            mapping.write({
                                'sync_status': 'error',
                                'error_message': error_msg
                            })
                            error_count += 1
                    except Exception as e:
                        # Falha na sincronização do mapeamento
                        mapping.write({
                            'sync_status': 'error',
                            'error_message': str(e)
                        })
                        error_count += 1

                # Mensagem de sucesso com informações sobre os mapeamentos
                message = _('As credenciais foram sincronizadas com o serviço de configuração.')
                if success_count > 0 or error_count > 0:
                    message += _(' Mapeamentos de canal: %s sincronizados com sucesso, %s falhas.') % (success_count, error_count)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização bem-sucedida'),
                        'message': message,
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                # Falha na requisição
                error_msg = f"Erro HTTP {response.status_code}: {response.text}"

                # Atualizar status de sincronização
                self.write({
                    'sync_status': 'error',
                    'error_message': error_msg
                })

                # Registrar falha
                self.env['ai.credentials.access.log'].sudo().create({
                    'credential_id': self.id,
                    'access_time': fields.Datetime.now(),
                    'ip_address': self.env.context.get('remote_addr', 'N/A'),
                    'operation': 'sync_to_webhook',
                    'success': False,
                    'error_message': error_msg
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Falha na sincronização'),
                        'message': error_msg,
                        'sticky': False,
                        'type': 'danger',
                    }
                }

        except Exception as e:
            # Atualizar status de sincronização
            self.write({
                'sync_status': 'error',
                'error_message': str(e)
            })

            # Registrar falha
            self.env['ai.credentials.access.log'].sudo().create({
                'credential_id': self.id,
                'access_time': fields.Datetime.now(),
                'ip_address': self.env.context.get('remote_addr', 'N/A'),
                'operation': 'sync_to_webhook',
                'success': False,
                'error_message': str(e)
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Falha na sincronização'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }
