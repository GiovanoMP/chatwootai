# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)

class MarketplaceDescription(models.Model):
    _name = 'product.marketplace.description'
    _description = 'Descrição de Produto para Marketplace'
    _rec_name = 'product_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    product_id = fields.Many2one(
        'product.template',
        string='Produto',
        required=True,
        ondelete='cascade',
        help='Produto relacionado'
    )
    
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        required=True,
        ondelete='cascade',
        help='Marketplace relacionado'
    )
    
    marketplace_category_id = fields.Many2one(
        'product.marketplace.category',
        string='Categoria do Marketplace',
        help='Categoria do produto no marketplace'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        help='Empresa à qual esta descrição pertence'
    )
    
    # Campos de conteúdo
    title = fields.Char(
        string='Título',
        help='Título do produto no marketplace'
    )
    
    description = fields.Html(
        string='Descrição',
        help='Descrição formatada do produto para o marketplace'
    )
    
    description_plain = fields.Text(
        string='Descrição Simples',
        help='Versão em texto simples da descrição'
    )
    
    keywords = fields.Char(
        string='Palavras-chave',
        help='Palavras-chave para otimização de busca'
    )
    
    bullet_points = fields.Text(
        string='Pontos Principais',
        help='Pontos principais do produto (um por linha)'
    )
    
    # Campos de controle
    enrichment_profile_id = fields.Many2one(
        'product.enrichment.profile',
        string='Perfil de Enriquecimento',
        help='Perfil de enriquecimento utilizado'
    )
    
    enrichment_date = fields.Datetime(
        string='Data de Enriquecimento',
        help='Data e hora do último enriquecimento'
    )
    
    verified = fields.Boolean(
        string='Verificado',
        default=False,
        help='Indica se a descrição foi verificada por um humano'
    )
    
    verified_by = fields.Many2one(
        'res.users',
        string='Verificado por',
        help='Usuário que verificou a descrição'
    )
    
    verification_date = fields.Datetime(
        string='Data de Verificação',
        help='Data e hora da verificação'
    )
    
    # Campos de publicação
    marketplace_product_id = fields.Char(
        string='ID do Produto no Marketplace',
        help='ID do produto no marketplace após publicação'
    )
    
    marketplace_url = fields.Char(
        string='URL no Marketplace',
        help='URL do produto no marketplace'
    )
    
    publication_status = fields.Selection([
        ('draft', 'Rascunho'),
        ('pending', 'Pendente'),
        ('published', 'Publicado'),
        ('error', 'Erro'),
        ('inactive', 'Inativo')
    ], string='Status de Publicação', 
       default='draft',
       help='Status atual da publicação no marketplace')
    
    publication_date = fields.Datetime(
        string='Data de Publicação',
        help='Data e hora da última publicação'
    )
    
    scheduled_publication = fields.Datetime(
        string='Publicação Agendada',
        help='Data e hora agendada para publicação'
    )
    
    error_message = fields.Text(
        string='Mensagem de Erro',
        help='Mensagem de erro em caso de falha na publicação'
    )
    
    # Campos de validação
    validation_status = fields.Selection([
        ('not_validated', 'Não Validado'),
        ('valid', 'Válido'),
        ('warnings', 'Avisos'),
        ('errors', 'Erros')
    ], string='Status de Validação', 
       default='not_validated',
       help='Status da validação da descrição')
    
    validation_date = fields.Datetime(
        string='Data de Validação',
        help='Data e hora da última validação'
    )
    
    validation_errors = fields.Text(
        string='Erros de Validação',
        help='Lista de erros encontrados na validação'
    )
    
    validation_warnings = fields.Text(
        string='Avisos de Validação',
        help='Lista de avisos encontrados na validação'
    )
    
    validated_by = fields.Many2one(
        'res.users',
        string='Validado por',
        help='Usuário que realizou a validação'
    )
    
    # Campos de performance
    views = fields.Integer(
        string='Visualizações',
        default=0,
        help='Número de visualizações no marketplace'
    )
    
    # Campos de preço e estoque
    price = fields.Float(
        string='Preço',
        help='Preço do produto no marketplace'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda',
        default=lambda self: self.env.company.currency_id,
        help='Moeda do preço'
    )
    
    list_price = fields.Float(
        string='Preço de Tabela',
        related='product_id.list_price',
        readonly=True,
        help='Preço de tabela do produto'
    )
    
    price_margin = fields.Float(
        string='Margem de Preço (%)',
        default=0.0,
        help='Margem de preço aplicada ao preço de tabela'
    )
    
    has_promotion = fields.Boolean(
        string='Tem Promoção',
        default=False,
        help='Indica se o produto está em promoção'
    )
    
    promotional_price = fields.Float(
        string='Preço Promocional',
        help='Preço promocional do produto'
    )
    
    promotion_start_date = fields.Datetime(
        string='Início da Promoção',
        help='Data e hora de início da promoção'
    )
    
    promotion_end_date = fields.Datetime(
        string='Fim da Promoção',
        help='Data e hora de fim da promoção'
    )
    
    # Campos de estoque
    qty_available = fields.Float(
        string='Quantidade Disponível',
        related='product_id.qty_available',
        readonly=True,
        help='Quantidade disponível em estoque'
    )
    
    marketplace_quantity = fields.Integer(
        string='Quantidade no Marketplace',
        help='Quantidade disponível no marketplace'
    )
    
    min_quantity = fields.Integer(
        string='Quantidade Mínima',
        default=1,
        help='Quantidade mínima para manter o produto ativo no marketplace'
    )
    
    sync_stock = fields.Boolean(
        string='Sincronizar Estoque',
        default=True,
        help='Sincronizar automaticamente o estoque com o marketplace'
    )
    
    stock_update_frequency = fields.Selection([
        ('realtime', 'Tempo Real'),
        ('daily', 'Diário'),
        ('weekly', 'Semanal')
    ], string='Frequência de Atualização', 
       default='daily',
       help='Frequência de atualização do estoque no marketplace')
    
    last_stock_update = fields.Datetime(
        string='Última Atualização de Estoque',
        help='Data e hora da última atualização de estoque'
    )
    
    # Campos de atributos
    attribute_ids = fields.One2many(
        'product.marketplace.description.attribute',
        'description_id',
        string='Atributos',
        help='Atributos específicos do produto para este marketplace'
    )
    
    # Campos de imagens
    image_ids = fields.One2many(
        'product.marketplace.description.image',
        'description_id',
        string='Imagens',
        help='Imagens do produto para este marketplace'
    )
    
    # Campos de histórico
    history_ids = fields.One2many(
        'product.marketplace.description.history',
        'description_id',
        string='Histórico',
        help='Histórico de alterações de estado'
    )
    
    # Campos de controle de estado
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('review', 'Em Revisão'),
        ('approved', 'Aprovado'),
        ('published', 'Publicado'),
        ('inactive', 'Inativo')
    ], string='Estado', 
       default='draft',
       help='Estado atual da descrição')
    
    user_id = fields.Many2one(
        'res.users',
        string='Responsável',
        default=lambda self: self.env.user,
        help='Usuário responsável por esta descrição'
    )
    
    active = fields.Boolean(
        string='Ativo',
        default=True,
        help='Se desativado, esta descrição não será considerada para publicação'
    )
    
    sequence = fields.Integer(
        string='Sequência',
        default=10,
        help='Determina a ordem de exibição das descrições'
    )
    
    last_update_date = fields.Datetime(
        string='Última Atualização',
        help='Data e hora da última atualização'
    )
    
    sales = fields.Integer(
        string='Vendas',
        default=0,
        help='Número de vendas no marketplace'
    )
    
    conversion_rate = fields.Float(
        string='Taxa de Conversão (%)',
        compute='_compute_conversion_rate',
        help='Taxa de conversão (vendas/visualizações)'
    )
    
    last_sync_date = fields.Datetime(
        string='Última Sincronização',
        help='Data e hora da última sincronização com o marketplace'
    )
    
    # Histórico de versões
    version_ids = fields.One2many(
        'product.marketplace.description.version',
        'description_id',
        string='Histórico de Versões',
        help='Histórico de versões desta descrição'
    )
    
    current_version = fields.Integer(
        string='Versão Atual',
        default=1,
        help='Número da versão atual'
    )
    
    # Campos para validação
    validation_errors = fields.Text(
        string='Erros de Validação',
        help='Erros de validação encontrados'
    )
    
    validation_status = fields.Selection([
        ('not_validated', 'Não Validado'),
        ('validating', 'Validando'),
        ('valid', 'Válido'),
        ('invalid', 'Inválido')
    ], string='Status de Validação', 
       default='not_validated',
       help='Status atual da validação')
    
    # Métodos
    @api.depends('views', 'sales')
    def _compute_conversion_rate(self):
        for record in self:
            record.conversion_rate = (record.sales / record.views * 100) if record.views else 0.0
    
    @api.constrains('product_id', 'marketplace_id')
    def _check_unique_product_marketplace(self):
        for record in self:
            if self.search_count([
                ('product_id', '=', record.product_id.id),
                ('marketplace_id', '=', record.marketplace_id.id),
                ('id', '!=', record.id)
            ]):
                raise ValidationError(_("Já existe uma descrição para este produto neste marketplace"))
    
    @api.onchange('description')
    def _onchange_description(self):
        """Atualiza a versão em texto simples da descrição."""
        if self.description:
            # Implementação simples para remover HTML. Em produção, use uma biblioteca HTML.
            self.description_plain = self.description.replace('<p>', '').replace('</p>', '\n').replace('<br>', '\n')
    
    def save_version(self):
        """Salva a versão atual como uma nova versão no histórico."""
        self.ensure_one()
        
        # Criar nova versão
        self.env['product.marketplace.description.version'].create({
            'description_id': self.id,
            'version_number': self.current_version,
            'title': self.title,
            'description': self.description,
            'keywords': self.keywords,
            'bullet_points': self.bullet_points,
            'created_by': self.env.user.id,
            'creation_date': fields.Datetime.now()
        })
        
        # Incrementar versão atual
        self.current_version += 1
    
    def validate(self):
        """Valida a descrição de acordo com as regras do marketplace."""
        self.ensure_one()
        
        self.validation_status = 'validating'
        errors = []
        
        # Validar título
        if not self.title:
            errors.append(_("O título é obrigatório"))
        elif self.marketplace_id.max_title_length and len(self.title) > self.marketplace_id.max_title_length:
            errors.append(_("O título excede o tamanho máximo permitido (%s caracteres)") % 
                         self.marketplace_id.max_title_length)
        
        # Validar descrição
        if not self.description:
            errors.append(_("A descrição é obrigatória"))
        elif self.marketplace_id.max_description_length and len(self.description_plain) > self.marketplace_id.max_description_length:
            errors.append(_("A descrição excede o tamanho máximo permitido (%s caracteres)") % 
                         self.marketplace_id.max_description_length)
        
        # Atualizar status de validação
        if errors:
            self.write({
                'validation_status': 'invalid',
                'validation_errors': '\n'.join(errors)
            })
            return False
        else:
            self.write({
                'validation_status': 'valid',
                'validation_errors': False
            })
            return True
    
    def mark_as_verified(self):
        """Marca a descrição como verificada pelo usuário atual."""
        self.ensure_one()
        
        self.write({
            'verified': True,
            'verified_by': self.env.user.id,
            'verification_date': fields.Datetime.now()
        })
    
    def publish(self):
        """Publica a descrição no marketplace."""
        self.ensure_one()
        
        # Validar antes de publicar
        if not self.validate():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro de Validação'),
                    'message': _('Corrija os erros de validação antes de publicar:\n%s') % self.validation_errors,
                    'sticky': True,
                    'type': 'danger',
                }
            }
        
        # Implementação genérica. Cada marketplace terá sua própria lógica.
        try:
            # Salvar versão atual
            self.save_version()
            
            # Atualizar status
            self.write({
                'publication_status': 'published',
                'publication_date': fields.Datetime.now(),
                'scheduled_publication': False,
                'error_message': False
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sucesso'),
                    'message': _('Produto publicado com sucesso no %s') % self.marketplace_id.name,
                    'sticky': False,
                    'type': 'success',
                }
            }
            
        except Exception as e:
            self.write({
                'publication_status': 'error',
                'error_message': str(e)
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro de Publicação'),
                    'message': _('Falha ao publicar: %s') % str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
    
    def schedule_publication(self, scheduled_date):
        """Agenda a publicação para uma data futura."""
        self.ensure_one()
        
        # Validar antes de agendar
        if not self.validate():
            return False
        
        self.write({
            'publication_status': 'pending',
            'scheduled_publication': scheduled_date,
            'error_message': False
        })
        
        return True
        
    def action_validate(self):
        """Ação para validar a descrição."""
        self.ensure_one()
        result = self.validate()
        
        if result:
            self.write({
                'state': 'validated',
                'validated_by': self.env.user.id,
                'validation_date': fields.Datetime.now()
            })
            
            # Registrar no histórico
            self.env['product.marketplace.description.history'].create({
                'description_id': self.id,
                'user_id': self.env.user.id,
                'old_state': 'draft',
                'new_state': 'validated',
                'action': 'validate',
                'notes': 'Validação realizada com sucesso'
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sucesso'),
                    'message': _('Descrição validada com sucesso'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Erro'),
                'message': _('A descrição contém erros de validação'),
                'sticky': True,
                'type': 'danger',
            }
        }
    
    def action_publish(self):
        """Ação para publicar a descrição."""
        self.ensure_one()
        result = self.publish()
        
        if isinstance(result, dict) and result.get('type') == 'ir.actions.client':
            return result
        
        # Registrar no histórico
        self.env['product.marketplace.description.history'].create({
            'description_id': self.id,
            'user_id': self.env.user.id,
            'old_state': 'validated',
            'new_state': 'published',
            'action': 'publish',
            'notes': 'Publicação realizada com sucesso'
        })
        
        self.write({'state': 'published'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sucesso'),
                'message': _('Descrição publicada com sucesso'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_unpublish(self):
        """Ação para despublicar a descrição."""
        self.ensure_one()
        
        try:
            # Lógica para despublicar no marketplace
            marketplace = self.marketplace_id
            
            if not marketplace:
                raise ValidationError(_('Marketplace não definido'))
            
            # Atualizar status
            self.write({
                'publication_status': 'inactive',
                'state': 'validated'
            })
            
            # Registrar no histórico
            self.env['product.marketplace.description.history'].create({
                'description_id': self.id,
                'user_id': self.env.user.id,
                'old_state': 'published',
                'new_state': 'validated',
                'action': 'unpublish',
                'notes': 'Despublicação realizada com sucesso'
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sucesso'),
                    'message': _('Produto despublicado com sucesso'),
                    'sticky': False,
                    'type': 'success',
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': _('Falha ao despublicar: %s') % str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
    
    def action_reset(self):
        """Ação para resetar a descrição para rascunho."""
        self.ensure_one()
        
        old_state = self.state
        
        # Não permitir resetar descrições publicadas
        if self.state == 'published':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': _('Descrições publicadas não podem ser resetadas. Despublique primeiro.'),
                    'sticky': True,
                    'type': 'danger',
                }
            }
        
        self.write({
            'state': 'draft',
            'validation_status': 'not_validated',
            'validation_errors': False,
            'validation_warnings': False,
            'validated_by': False,
            'validation_date': False
        })
        
        # Registrar no histórico
        self.env['product.marketplace.description.history'].create({
            'description_id': self.id,
            'user_id': self.env.user.id,
            'old_state': old_state,
            'new_state': 'draft',
            'action': 'reset',
            'notes': 'Descrição resetada para rascunho'
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sucesso'),
                'message': _('Descrição resetada para rascunho'),
                'sticky': False,
                'type': 'success',
            }
        }
        
    def action_view_marketplace(self):
        """Abre a vista do marketplace relacionado."""
        self.ensure_one()
        
        if not self.marketplace_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aviso'),
                    'message': _('Esta descrição não está associada a nenhum marketplace.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        return {
            'name': _('Marketplace'),
            'view_mode': 'form',
            'res_model': 'product.marketplace',
            'res_id': self.marketplace_id.id,
            'type': 'ir.actions.act_window',
            'context': {'create': False}
        }
        
    def action_view_product(self):
        """Abre a vista do produto relacionado."""
        self.ensure_one()
        
        if not self.product_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aviso'),
                    'message': _('Esta descrição não está associada a nenhum produto.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        return {
            'name': _('Produto'),
            'view_mode': 'form',
            'res_model': 'product.template',
            'res_id': self.product_id.id,
            'type': 'ir.actions.act_window',
            'context': {'create': False}
        }


class MarketplaceDescriptionVersion(models.Model):
    _name = 'product.marketplace.description.version'
    _description = 'Versão de Descrição de Marketplace'
    _order = 'version_number desc'
    
    description_id = fields.Many2one(
        'product.marketplace.description',
        string='Descrição',
        required=True,
        ondelete='cascade',
        help='Descrição relacionada'
    )
    
    version_number = fields.Integer(
        string='Número da Versão',
        required=True,
        help='Número sequencial da versão'
    )
    
    title = fields.Char(
        string='Título',
        help='Título do produto nesta versão'
    )
    
    description = fields.Html(
        string='Descrição',
        help='Descrição formatada do produto nesta versão'
    )
    
    keywords = fields.Char(
        string='Palavras-chave',
        help='Palavras-chave para otimização de busca nesta versão'
    )
    
    bullet_points = fields.Text(
        string='Pontos Principais',
        help='Pontos principais do produto nesta versão'
    )
    
    created_by = fields.Many2one(
        'res.users',
        string='Criado por',
        help='Usuário que criou esta versão'
    )
    
    creation_date = fields.Datetime(
        string='Data de Criação',
        help='Data e hora de criação desta versão'
    )
    
    notes = fields.Text(
        string='Observações',
        help='Observações sobre esta versão'
    )
    
    # Métodos
    def restore(self):
        """Restaura esta versão como a versão atual."""
        self.ensure_one()
        
        # Atualizar descrição principal
        self.description_id.write({
            'title': self.title,
            'description': self.description,
            'keywords': self.keywords,
            'bullet_points': self.bullet_points,
            'verified': False,
            'verified_by': False,
            'verification_date': False,
            'validation_status': 'not_validated',
            'validation_errors': False
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Versão Restaurada'),
                'message': _('Versão %s restaurada com sucesso') % self.version_number,
                'sticky': False,
                'type': 'success',
            }
        }
