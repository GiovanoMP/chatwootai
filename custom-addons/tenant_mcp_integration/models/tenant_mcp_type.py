# -*- coding: utf-8 -*-
from odoo import models, fields

class TenantMCPType(models.Model):
    _name = 'tenant_mcp.type'
    _description = 'MCP Type'
    _order = 'sequence,name'

    name = fields.Char(string='Nome do Tipo de MCP', required=True, translate=True)
    code = fields.Char(string='Código', required=True, help="Código único para identificar o tipo de MCP.")
    description = fields.Text(string='Descrição', translate=True)
    sequence = fields.Integer(string='Sequência', default=10)
    icon = fields.Char(string='Ícone Web (Font Awesome)', help="Ex: fa-database, fa-brain, fa-comments")

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'O Código do Tipo de MCP deve ser único!')
    ]
