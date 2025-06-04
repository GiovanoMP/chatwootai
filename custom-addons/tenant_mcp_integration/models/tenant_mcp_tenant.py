# -*- coding: utf-8 -*-
import secrets
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TenantMCPTenant(models.Model):
    _name = 'tenant_mcp.tenant'
    _description = 'Tenant Configuration for MCP Integration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nome da Empresa', required=True, tracking=True)
    account_id = fields.Char(string='Account ID (Tenant)', required=True, copy=False, tracking=True,
                             help="Identificador único do tenant usado pelo MCP-CREW.")
    active = fields.Boolean(string='Ativo', default=True, tracking=True)

    # API Odoo (para MCP-CREW acessar este Odoo)
    odoo_api_key = fields.Char(string='API Key do Odoo', readonly=True, copy=False, groups='base.group_system', help="Chave API gerada pelo Odoo para este tenant. O MCP-CREW usará esta chave para se autenticar.")
    odoo_base_url = fields.Char(string='URL Base do Odoo', readonly=True, compute='_compute_odoo_base_url', help="URL base desta instância Odoo para acesso via API.")

    # Conexão MCP-CREW (para este Odoo acessar o MCP-CREW)
    mcp_crew_url = fields.Char(string='URL do MCP-CREW', tracking=True,
                               help="URL base do serviço MCP-CREW.")
    mcp_crew_api_key = fields.Char(string='API Key do MCP-CREW', copy=False, tracking=True,
                                   help="Chave de API para o Odoo acessar o MCP-CREW em nome deste tenant.")

    mcp_configuration_ids = fields.One2many('tenant_mcp.mcp.configuration', 'tenant_id',
                                             string='MCPs Configurados')
    tenant_service_access_ids = fields.One2many(
        'tenant_mcp.tenant.service.access',
        'tenant_id',
        string='Acessos a Serviços de IA',
        help="Define quais serviços de IA do catálogo este tenant pode acessar."
    )

    _sql_constraints = [
        ('account_id_uniq', 'unique (account_id)', 'O Account ID (Tenant) deve ser único!')
    ]

    def _compute_odoo_base_url(self):
        for tenant in self:
            tenant.odoo_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

    def generate_odoo_api_key(self):
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise UserError(_('Apenas administradores podem gerar chaves de API.'))
        new_key = secrets.token_urlsafe(32)
        self.write({'odoo_api_key': new_key})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sucesso'),
                'message': _('Nova API Key do Odoo gerada com sucesso.'),
                'sticky': False,
                'type': 'success',
            }
        }

    @api.model
    def create(self, vals):
        tenant = super(TenantMcpTenant, self).create(vals)
        if tenant.account_id:
            default_mcp_codes = ['odoo_erp', 'qdrant', 'mongodb', 'chatwoot']
            mcp_type_env = self.env['tenant_mcp.type']
            mcp_config_env = self.env['tenant_mcp.mcp.configuration']

            default_mcps_to_create = []
            for code in default_mcp_codes:
                mcp_type = mcp_type_env.search([('code', '=', code)], limit=1)
                if mcp_type:
                    # Verificar se já não existe uma configuração para este tenant e tipo de MCP
                    existing_config = mcp_config_env.search([
                        ('tenant_id', '=', tenant.id),
                        ('mcp_type_id', '=', mcp_type.id)
                    ], limit=1)
                    if not existing_config:
                        default_mcps_to_create.append({
                            'tenant_id': tenant.id,
                            'mcp_type_id': mcp_type.id,
                            'name': f"{mcp_type.name} para {tenant.name}", # Nome descritivo
                            'instance_identifier': tenant.account_id,
                            'is_active': True, # Ativar por padrão
                            'notes': 'Criado automaticamente durante a criação do tenant.'
                        })
            if default_mcps_to_create:
                mcp_config_env.create(default_mcps_to_create)
        return tenant

    def test_mcp_crew_connection(self):
        self.ensure_one()
        # Lógica para testar a conexão com o MCP-CREW será implementada aqui
        # Por agora, apenas uma notificação de placeholder
        if not self.mcp_crew_url or not self.mcp_crew_api_key:
            raise UserError(_('URL do MCP-CREW e API Key do MCP-CREW devem ser preenchidas.'))
        
        # Simulação de teste (substituir por chamada HTTP real)
        # import requests
        # try:
        #     headers = {'Authorization': f'Bearer {self.mcp_crew_api_key}'}
        #     response = requests.get(f'{self.mcp_crew_url}/health', headers=headers, timeout=10)
        #     if response.status_code == 200:
        #         message = _('Conexão com MCP-CREW bem-sucedida!')
        #         msg_type = 'success'
        #     else:
        #         message = _('Falha na conexão com MCP-CREW. Status: %s') % response.status_code
        #         msg_type = 'danger'
        # except requests.exceptions.RequestException as e:
        #     message = _('Erro ao conectar com MCP-CREW: %s') % e
        #     msg_type = 'danger'

        message = _('Funcionalidade de teste de conexão ainda não implementada.')
        msg_type = 'info'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Teste de Conexão'),
                'message': message,
                'sticky': False,
                'type': msg_type,
            }
        }
