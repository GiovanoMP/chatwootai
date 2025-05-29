# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
import json
import requests
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class ProductMarketplace(models.Model):
    _name = 'product.marketplace'
    _description = 'Marketplace'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Nome', 
        required=True,
        help='Nome do marketplace'
    )
    
    code = fields.Char(
        string='Código', 
        required=True,
        help='Código único do marketplace para referência no sistema'
    )
    
    marketplace_type = fields.Selection([
        ('mercadolivre', 'Mercado Livre'),
        ('amazon', 'Amazon'),
        ('shopee', 'Shopee'),
        ('magalu', 'Magalu'),
        ('outros', 'Outros')
    ], string='Tipo de Marketplace', required=True, default='outros',
       help='Tipo de marketplace para configurações específicas')
    
    sequence = fields.Integer(
        string='Sequência', 
        default=10,
        help='Determina a ordem de exibição dos marketplaces'
    )
    
    active = fields.Boolean(
        string='Ativo', 
        default=True,
        help='Se desativado, este marketplace não será disponível para seleção'
    )
    
    description = fields.Text(
        string='Descrição',
        help='Descrição detalhada do marketplace'
    )
    
    logo = fields.Binary(
        string='Logo',
        attachment=True,
        help='Logo do marketplace'
    )
    
    website = fields.Char(
        string='Website',
        help='URL do website do marketplace'
    )
    
    country_id = fields.Many2one(
        'res.country',
        string='País',
        help='País de origem do marketplace'
    )
    
    # Configurações de API
    api_base_url = fields.Char(
        string='URL Base da API',
        help='URL base para chamadas de API'
    )
    
    api_version = fields.Char(
        string='Versão da API',
        help='Versão da API do marketplace'
    )
    
    api_key = fields.Char(
        string='Chave de API',
        help='Chave de API para autenticação'
    )
    
    api_secret = fields.Char(
        string='Segredo da API',
        help='Segredo da API para autenticação',
        groups='base.group_system'
    )
    
    access_token = fields.Char(
        string='Token de Acesso',
        help='Token de acesso para a API',
        groups='base.group_system'
    )
    
    token = fields.Char(
        string='Token',
        help='Token alternativo para autenticação',
        groups='base.group_system'
    )
    
    token_expiry = fields.Datetime(
        string='Validade do Token',
        help='Data e hora de expiração do token de acesso'
    )
    
    # Configurações específicas do marketplace
    max_title_length = fields.Integer(
        string='Tamanho Máximo do Título',
        default=60,
        help='Número máximo de caracteres permitidos no título do produto'
    )
    
    max_description_length = fields.Integer(
        string='Tamanho Máximo da Descrição',
        default=5000,
        help='Número máximo de caracteres permitidos na descrição do produto'
    )
    
    max_images = fields.Integer(
        string='Máximo de Imagens',
        default=10,
        help='Número máximo de imagens permitidas por produto'
    )
    
    image_requirements = fields.Text(
        string='Requisitos de Imagem',
        help='Requisitos específicos para imagens neste marketplace'
    )
    
    category_mapping_ids = fields.One2many(
        'product.marketplace.category.mapping',
        'marketplace_id',
        string='Mapeamento de Categorias',
        help='Mapeamento entre categorias do Odoo e categorias do marketplace'
    )
    
    # Multi-empresa
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        help='Empresa à qual este marketplace pertence'
    )
    
    # Configurações MCP
    mcp_server_url = fields.Char(
        string='URL do Servidor MCP',
        help='URL base do servidor MCP para este marketplace'
    )
    
    mcp_account_id = fields.Char(
        string='ID da Conta MCP',
        help='ID da conta no MCP para este marketplace'
    )
    
    # Estatísticas e contadores
    product_count = fields.Integer(
        string='Total de Produtos',
        compute='_compute_product_count',
        help='Número total de produtos neste marketplace'
    )
    
    description_count = fields.Integer(
        string='Total de Descrições',
        compute='_compute_description_count',
        help='Número total de descrições de marketplace'
    )
    
    published_product_count = fields.Integer(
        string='Produtos Publicados',
        default=0,
        help='Número de produtos publicados neste marketplace'
    )
    
    pending_product_count = fields.Integer(
        string='Produtos Pendentes',
        default=0,
        help='Número de produtos pendentes de publicação'
    )
    
    error_product_count = fields.Integer(
        string='Produtos com Erro',
        default=0,
        help='Número de produtos com erro de publicação'
    )
    
    # Configurações de sincronização
    auto_sync = fields.Boolean(
        string='Sincronização Automática',
        default=False,
        help='Ativar sincronização automática com este marketplace'
    )
    
    auto_publish = fields.Boolean(
        string='Publicação Automática',
        default=False,
        help='Publicar automaticamente produtos elegíveis'
    )
    
    sync_stock = fields.Boolean(
        string='Sincronizar Estoque',
        default=True,
        help='Sincronizar informações de estoque com o marketplace'
    )
    
    sync_price = fields.Boolean(
        string='Sincronizar Preço',
        default=True,
        help='Sincronizar informações de preço com o marketplace'
    )
    
    sync_interval = fields.Integer(
        string='Intervalo de Sincronização (min)',
        default=60,
        help='Intervalo em minutos entre sincronizações automáticas'
    )
    
    last_sync = fields.Datetime(
        string='Última Sincronização',
        help='Data e hora da última sincronização'
    )
    
    # Métricas de desempenho
    avg_sync_time = fields.Float(
        string='Tempo Médio de Sincronização',
        default=0.0,
        help='Tempo médio em segundos para sincronizar um produto'
    )
    
    success_rate = fields.Float(
        string='Taxa de Sucesso',
        default=0.0,
        help='Porcentagem de sincronizações bem-sucedidas'
    )
    
    last_error = fields.Text(
        string='Último Erro',
        help='Mensagem do último erro ocorrido'
    )
    
    last_error_date = fields.Datetime(
        string='Data do Último Erro',
        help='Data e hora do último erro ocorrido'
    )
    
    # Logs de sincronização
    sync_log_ids = fields.One2many(
        'product.marketplace.sync.log',
        'marketplace_id',
        string='Logs de Sincronização',
        help='Histórico de sincronizações com este marketplace'
    )
    
    # Atributos requeridos
    required_attribute_ids = fields.One2many(
        'product.marketplace.attribute',
        'marketplace_id',
        string='Atributos Requeridos',
        help='Atributos requeridos para publicação neste marketplace'
    )
    
    mcp_account_id = fields.Char(
        string='ID da Conta MCP',
        help='Identificador da conta no servidor MCP'
    )
    
    # Estatísticas
    product_count = fields.Integer(
        string='Número de Produtos',
        compute='_compute_product_count',
        help='Número de produtos publicados neste marketplace'
    )
    
    description_count = fields.Integer(
        string='Número de Descrições',
        compute='_compute_description_count',
        help='Número de descrições de produtos para este marketplace'
    )
    
    last_sync = fields.Datetime(
        string='Última Sincronização',
        help='Data e hora da última sincronização com este marketplace'
    )
    
    # Perfis de enriquecimento relacionados
    enrichment_profile_ids = fields.One2many(
        'product.enrichment.profile',
        'marketplace_id',
        string='Perfis de Enriquecimento',
        help='Perfis de enriquecimento específicos para este marketplace'
    )
    
    # Métodos
    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError(_("O código do marketplace deve ser único"))
    
    def _compute_product_count(self):
        for record in self:
            record.product_count = self.env['product.marketplace.description'].search_count([
                ('marketplace_id', '=', record.id)
            ])
    
    def _compute_description_count(self):
        for record in self:
            record.description_count = self.env['product.marketplace.description'].search_count([
                ('marketplace_id', '=', record.id)
            ])
    
    def action_view_products(self):
        """Abre a vista de produtos publicados neste marketplace."""
        self.ensure_one()
        return {
            'name': _('Produtos em %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.marketplace.description',
            'view_mode': 'tree,form',
            'domain': [('marketplace_id', '=', self.id)],
            'context': {'default_marketplace_id': self.id},
        }
    
    def action_view_descriptions(self):
        """Abre a vista de descrições de marketplace."""
        self.ensure_one()
        return {
            'name': _('Descrições em %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.marketplace.description',
            'view_mode': 'tree,form',
            'domain': [('marketplace_id', '=', self.id)],
            'context': {'default_marketplace_id': self.id},
        }
    
    def refresh_token(self):
        """Atualiza o token de acesso para o marketplace."""
        self.ensure_one()
        
        if not self.api_base_url or not self.api_key or not self.api_secret:
            raise ValidationError(_("Configurações de API incompletas"))
        
        try:
            # Esta é uma implementação genérica. Cada marketplace terá sua própria lógica.
            response = requests.post(
                f"{self.api_base_url}/oauth/token",
                data={
                    'client_id': self.api_key,
                    'client_secret': self.api_secret,
                    'grant_type': 'client_credentials'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.write({
                    'access_token': data.get('access_token'),
                    'token_expiry': datetime.now().replace(second=0, microsecond=0) + 
                                   timedelta(seconds=data.get('expires_in', 3600)),
                    'last_sync': fields.Datetime.now()
                })
                return True
            else:
                _logger.error(f"Erro ao atualizar token: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            _logger.error(f"Exceção ao atualizar token: {str(e)}")
            return False
    
    def test_connection(self):
        """Testa a conexão com o marketplace."""
        self.ensure_one()
        
        if not self.api_base_url:
            raise ValidationError(_("URL base da API não configurada"))
        
        try:
            # Verificar se o token está válido
            if not self.access_token or (self.token_expiry and self.token_expiry < fields.Datetime.now()):
                self.refresh_token()
            
            # Esta é uma implementação genérica. Cada marketplace terá sua própria lógica.
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f"{self.api_base_url}/test",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.write({'last_sync': fields.Datetime.now()})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sucesso'),
                        'message': _('Conexão com %s estabelecida com sucesso') % self.name,
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro'),
                        'message': _('Falha na conexão: %s - %s') % (response.status_code, response.text),
                        'sticky': True,
                        'type': 'danger',
                    }
                }
                
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': _('Exceção: %s') % str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
    
    def sync_categories(self):
        """Sincroniza as categorias do marketplace."""
        self.ensure_one()
        
        if not self.api_base_url or not self.access_token:
            raise ValidationError(_('Configurações de API incompletas ou token de acesso inválido'))
        
        try:
            # Verificar se o token está válido
            if not self.access_token or (self.token_expiry and self.token_expiry < fields.Datetime.now()):
                self.refresh_token()
            
            # Esta é uma implementação genérica. Cada marketplace terá sua própria lógica.
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f"{self.api_base_url}/categories",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                categories = response.json()
                # Aqui seria implementada a lógica para processar as categorias recebidas
                # e atualizar os mapeamentos de categoria
                
                self.write({'last_sync': fields.Datetime.now()})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sucesso'),
                        'message': _('Categorias de %s sincronizadas com sucesso') % self.name,
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro'),
                        'message': _('Falha na sincronização: %s - %s') % (response.status_code, response.text),
                        'sticky': True,
                        'type': 'danger',
                    }
                }
                
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': _('Exceção: %s') % str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }


class ProductMarketplaceCategory(models.Model):
    _name = 'product.marketplace.category'
    _description = 'Categoria de Marketplace'
    _rec_name = 'name'
    
    name = fields.Char(
        string='Nome',
        required=True,
        help='Nome da categoria no marketplace'
    )
    
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        required=True,
        ondelete='cascade',
        help='Marketplace relacionado'
    )
    
    parent_id = fields.Many2one(
        'product.marketplace.category',
        string='Categoria Pai',
        ondelete='cascade',
        help='Categoria pai no marketplace'
    )
    
    child_ids = fields.One2many(
        'product.marketplace.category',
        'parent_id',
        string='Subcategorias',
        help='Subcategorias no marketplace'
    )
    
    marketplace_category_code = fields.Char(
        string='Código da Categoria',
        help='Código único da categoria no marketplace'
    )
    
    is_leaf_category = fields.Boolean(
        string='Categoria Folha',
        default=False,
        help='Indica se esta é uma categoria folha (sem subcategorias)'
    )
    
    active = fields.Boolean(
        string='Ativo',
        default=True,
        help='Indica se esta categoria está ativa'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        help='Empresa à qual esta categoria pertence'
    )
    
    description = fields.Text(
        string='Descrição',
        help='Descrição da categoria'
    )
    
    # Métodos
    @api.constrains('marketplace_id', 'marketplace_category_code')
    def _check_unique_category_code(self):
        for record in self:
            if record.marketplace_category_code and self.search_count([
                ('marketplace_id', '=', record.marketplace_id.id),
                ('marketplace_category_code', '=', record.marketplace_category_code),
                ('id', '!=', record.id)
            ]):
                raise ValidationError(_("Já existe uma categoria com este código neste marketplace"))


class ProductMarketplaceCategoryMapping(models.Model):
    _name = 'product.marketplace.category.mapping'
    _description = 'Mapeamento de Categoria de Marketplace'
    
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        required=True,
        ondelete='cascade',
        help='Marketplace relacionado'
    )
    
    odoo_category_id = fields.Many2one(
        'product.category',
        string='Categoria Odoo',
        required=True,
        help='Categoria do produto no Odoo'
    )
    
    marketplace_category_id = fields.Char(
        string='ID da Categoria no Marketplace',
        required=True,
        help='ID da categoria correspondente no marketplace'
    )
    
    marketplace_category_name = fields.Char(
        string='Nome da Categoria no Marketplace',
        help='Nome da categoria correspondente no marketplace'
    )
    
    marketplace_category_code = fields.Char(
        string='Código da Categoria',
        help='Código da categoria no marketplace'
    )
    
    is_leaf_category = fields.Boolean(
        string='Categoria Folha',
        default=False,
        help='Indica se esta categoria é uma categoria folha (sem subcategorias)'
    )
    
    notes = fields.Text(
        string='Observações',
        help='Observações sobre este mapeamento'
    )
    
    # Métodos
    @api.constrains('odoo_category_id', 'marketplace_id')
    def _check_unique_mapping(self):
        for record in self:
            if self.search_count([
                ('odoo_category_id', '=', record.odoo_category_id.id),
                ('marketplace_id', '=', record.marketplace_id.id),
                ('id', '!=', record.id)
            ]):
                raise ValidationError(_("Já existe um mapeamento para esta categoria neste marketplace"))
