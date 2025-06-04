# -*- coding: utf-8 -*-
from odoo import models, fields

class TenantMCPConfiguration(models.Model):
    _name = 'tenant_mcp.mcp.configuration'
    _description = 'Tenant MCP Configuration'

    tenant_id = fields.Many2one('tenant_mcp.tenant', string='Tenant', required=True, ondelete='cascade')
    mcp_type_id = fields.Many2one('tenant_mcp.type', string='Tipo de MCP', required=True)
    name = fields.Char(related='mcp_type_id.name', store=True, readonly=True)
    is_active = fields.Boolean(string='Ativo para este Tenant', default=True,
                                help="Indica se este tipo de MCP está ativo e configurado para o tenant selecionado.")
    notes = fields.Text(string='Notas de Configuração Específicas',
                        help="Detalhes ou metadados de configuração que o MCP-CREW pode precisar. Não armazene credenciais aqui.")
    instance_identifier = fields.Char(
        string='Identificador da Instância/Recurso',
        help="Identificador específico para este MCP neste tenant (ex: prefixo de coleção Qdrant, nome da base MongoDB, ID da conta Chatwoot, etc.). Frequentemente derivado do Account ID do tenant."
    )

    # Poderíamos adicionar instance_identifier à unicidade se fizer sentido.
    # Por exemplo, se um mesmo tipo de MCP não pode ter o mesmo identificador para tenants diferentes (improvável)
    # ou se um tenant não pode ter dois MCPs do mesmo tipo com o mesmo identificador (mais provável, mas o identificador deve ser único por config).
    # Por enquanto, a unicidade de (tenant_id, mcp_type_id) já garante uma configuração única.
    _sql_constraints = [
        ('tenant_mcp_type_uniq', 'unique (tenant_id, mcp_type_id)', 
         'Este tipo de MCP já está configurado para este tenant.')
    ]
