# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class TenantMcpTenantServiceAccess(models.Model):
    _name = 'tenant_mcp.tenant.service.access'
    _description = 'Acesso do Tenant a Serviços de IA do Catálogo MCP'
    _log_access = False
    _rec_name = 'display_name'

    tenant_id = fields.Many2one(
        'tenant_mcp.tenant', 
        string='Tenant', 
        required=True, 
        ondelete='cascade',
        index=True
    )
    ia_service_catalog_id = fields.Many2one(
        'tenant_mcp.ia.service.catalog', 
        string='Serviço de IA', 
        required=True, 
        ondelete='cascade',
        index=True,
        domain="[('is_ia_service_available', '=', True)]", # Só permite selecionar serviços disponíveis
        help="Serviço de IA do catálogo ao qual este tenant terá ou não acesso."
    )
    is_enabled_for_tenant = fields.Boolean(
        string='Acesso Habilitado para o Tenant?', 
        default=False, 
        tracking=True,
        help="Marque esta opção para permitir que este tenant utilize o serviço de IA selecionado."
    )
    notes = fields.Text(
        string='Notas Específicas da Permissão',
        help="Observações ou detalhes sobre a permissão deste serviço para este tenant."
    )
    
    # Campos relacionados para fácil visualização (opcional, mas útil em views)
    ia_service_name = fields.Char(related='ia_service_catalog_id.ia_service_name', readonly=True, string="Nome do Serviço", store=False)
    ia_service_description = fields.Text(related='ia_service_catalog_id.ia_service_description', readonly=True, string="Descrição do Serviço", store=False)

    display_name = fields.Char(string="Nome de Exibição", compute='_compute_display_name', store=False)

    _sql_constraints = [
        ('tenant_service_uniq', 'unique (tenant_id, ia_service_catalog_id)', 
         'Este serviço de IA já está configurado para este tenant. Edite o registro existente.')
    ]

    @api.depends('tenant_id.name', 'ia_service_catalog_id.display_name')
    def _compute_display_name(self):
        for record in self:
            tenant_name = record.tenant_id.name if record.tenant_id else 'N/A'
            service_name = record.ia_service_catalog_id.display_name if record.ia_service_catalog_id else 'N/A'
            record.display_name = f"{service_name} para {tenant_name}"
