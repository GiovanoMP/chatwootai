# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # Configurações MCP-Qdrant
    mcp_qdrant_url = fields.Char(
        string='URL do MCP-Qdrant',
        config_parameter='product_ai_studio.mcp_qdrant_url',
        help='URL base do servidor MCP-Qdrant (ex: http://mcp-qdrant:8000)'
    )
    
    mcp_qdrant_token = fields.Char(
        string='Token do MCP-Qdrant',
        config_parameter='product_ai_studio.mcp_qdrant_token',
        help='Token de autenticação para o MCP-Qdrant'
    )
    
    mcp_qdrant_account_id = fields.Char(
        string='ID da Conta no MCP-Qdrant',
        config_parameter='product_ai_studio.mcp_qdrant_account_id',
        default='account_1',
        help='Identificador da conta no MCP-Qdrant (ex: account_1)'
    )
    
    # Configurações MCP-Odoo
    mcp_odoo_url = fields.Char(
        string='URL do MCP-Odoo',
        config_parameter='product_ai_studio.mcp_odoo_url',
        help='URL base do servidor MCP-Odoo (ex: http://mcp-odoo:8000)'
    )
    
    mcp_odoo_token = fields.Char(
        string='Token do MCP-Odoo',
        config_parameter='product_ai_studio.mcp_odoo_token',
        help='Token de autenticação para o MCP-Odoo'
    )
    
    mcp_odoo_account_id = fields.Char(
        string='ID da Conta no MCP-Odoo',
        config_parameter='product_ai_studio.mcp_odoo_account_id',
        default='account_1',
        help='Identificador da conta no MCP-Odoo (ex: account_1)'
    )
    
    # Configurações gerais
    enable_auto_vectorization = fields.Boolean(
        string='Habilitar Vetorização Automática',
        config_parameter='product_ai_studio.enable_auto_vectorization',
        default=True,
        help='Habilita a vetorização automática de produtos enriquecidos'
    )
    
    max_concurrent_enrichments = fields.Integer(
        string='Máximo de Enriquecimentos Concorrentes',
        config_parameter='product_ai_studio.max_concurrent_enrichments',
        default=5,
        help='Número máximo de enriquecimentos que podem ser processados simultaneamente'
    )
    
    default_enrichment_profile_id = fields.Many2one(
        'product.enrichment.profile',
        string='Perfil de Enriquecimento Padrão',
        config_parameter='product_ai_studio.default_enrichment_profile_id',
        help='Perfil de enriquecimento usado por padrão'
    )
