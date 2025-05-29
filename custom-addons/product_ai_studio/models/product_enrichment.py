# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
import json
import requests
import time
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class ProductEnrichment(models.Model):
    _name = 'product.enrichment'
    _description = 'Enriquecimento de Produto'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
        help='Nome do enriquecimento'
    )
    
    product_id = fields.Many2one(
        'product.template',
        string='Produto',
        required=True,
        ondelete='cascade',
        help='Produto a ser enriquecido'
    )
    
    enrichment_profile_id = fields.Many2one(
        'product.enrichment.profile',
        string='Perfil de Enriquecimento',
        required=True,
        help='Perfil de enriquecimento a ser utilizado'
    )
    
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        help='Marketplace específico para este enriquecimento'
    )
    
    # Campos de estado
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('done', 'Concluído'),
        ('error', 'Erro'),
        ('canceled', 'Cancelado')
    ], string='Estado', 
       default='draft',
       tracking=True,
       help='Estado atual do enriquecimento')
    
    # Campos de entrada
    original_title = fields.Char(
        string='Título Original',
        help='Título original do produto'
    )
    
    original_description = fields.Text(
        string='Descrição Original',
        help='Descrição original do produto'
    )
    
    # Campos de saída
    enriched_title = fields.Char(
        string='Título Enriquecido',
        help='Título enriquecido do produto'
    )
    
    enriched_description = fields.Html(
        string='Descrição Enriquecida',
        help='Descrição enriquecida do produto'
    )
    
    enriched_keywords = fields.Char(
        string='Palavras-chave',
        help='Palavras-chave sugeridas para o produto'
    )
    
    enriched_bullet_points = fields.Text(
        string='Pontos Principais',
        help='Pontos principais do produto (um por linha)'
    )
    
    # Campos de processamento
    prompt_used = fields.Text(
        string='Prompt Utilizado',
        help='Prompt enviado para a IA'
    )
    
    raw_response = fields.Text(
        string='Resposta Bruta',
        help='Resposta bruta da IA',
        groups='base.group_system'
    )
    
    processing_time = fields.Float(
        string='Tempo de Processamento (s)',
        help='Tempo de processamento em segundos'
    )
    
    error_message = fields.Text(
        string='Mensagem de Erro',
        help='Mensagem de erro em caso de falha'
    )
    
    # Campos de controle
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        help='Empresa à qual este enriquecimento pertence'
    )
    
    created_by = fields.Many2one(
        'res.users',
        string='Criado por',
        default=lambda self: self.env.user,
        help='Usuário que criou este enriquecimento'
    )
    
    scheduled_date = fields.Datetime(
        string='Data Agendada',
        help='Data e hora agendada para processamento'
    )
    
    processed_date = fields.Datetime(
        string='Data de Processamento',
        help='Data e hora do processamento'
    )
    
    approved = fields.Boolean(
        string='Aprovado',
        default=False,
        help='Indica se o enriquecimento foi aprovado'
    )
    
    approved_by = fields.Many2one(
        'res.users',
        string='Aprovado por',
        help='Usuário que aprovou este enriquecimento'
    )
    
    approval_date = fields.Datetime(
        string='Data de Aprovação',
        help='Data e hora da aprovação'
    )
    
    # Campos de análise competitiva
    competitive_analysis = fields.Html(
        string='Análise Competitiva',
        help='Análise competitiva do produto'
    )
    
    # Campos de vetorização
    vectorized = fields.Boolean(
        string='Vetorizado',
        default=False,
        help='Indica se o produto foi vetorizado'
    )
    
    vectorization_date = fields.Datetime(
        string='Data de Vetorização',
        help='Data e hora da vetorização'
    )
    
    vector_id = fields.Char(
        string='ID do Vetor',
        help='Identificador do vetor no banco de vetores'
    )
    
    # Campos de imagem
    image_preview = fields.Binary(
        string='Pré-visualização',
        related='product_id.image_1920',
        readonly=True,
        help='Pré-visualização da imagem do produto'
    )
    
    # Campos de imagens sugeridas
    suggested_image_ids = fields.One2many(
        'product.suggested.image',
        'enrichment_id',
        string='Imagens Sugeridas',
        help='Imagens sugeridas para o produto'
    )
    
    # Campos adicionais
    source = fields.Selection([
        ('manual', 'Manual'),
        ('auto', 'Automático'),
        ('scheduled', 'Agendado')
    ], string='Origem', 
       default='manual',
       help='Origem do enriquecimento')
    
    relevance = fields.Selection([
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta')
    ], string='Relevância', 
       default='medium',
       help='Relevância do enriquecimento')
    
    
    # Campos para sugestão de imagens
    suggested_image_ids = fields.One2many(
        'product.suggested.image',
        'enrichment_id',
        string='Imagens Sugeridas',
        help='Imagens sugeridas para o produto'
    )
    
    # Campos para marketplace
    marketplace_description_id = fields.Many2one(
        'product.marketplace.description',
        string='Descrição de Marketplace',
        help='Descrição de marketplace criada a partir deste enriquecimento'
    )
    
    # Métodos
    @api.depends('product_id', 'enrichment_profile_id', 'create_date')
    def _compute_name(self):
        for record in self:
            if record.product_id and record.enrichment_profile_id:
                record.name = f"{record.product_id.name} - {record.enrichment_profile_id.name}"
            elif record.product_id:
                record.name = record.product_id.name
            else:
                record.name = _("Novo Enriquecimento")
    
    @api.model
    def create(self, vals):
        """Sobrescreve o método create para capturar os dados originais do produto."""
        res = super(ProductEnrichment, self).create(vals)
        
        # Capturar dados originais do produto
        if res.product_id:
            res.write({
                'original_title': res.product_id.name,
                'original_description': res.product_id.description or res.product_id.description_sale or '',
            })
        
        return res
    
    def action_process(self):
        """Inicia o processamento do enriquecimento."""
        self.ensure_one()
        
        if self.state not in ['draft', 'error']:
            raise UserError(_("Apenas enriquecimentos em rascunho ou com erro podem ser processados"))
        
        self.write({
            'state': 'processing',
            'error_message': False
        })
        
        # Processar enriquecimento
        try:
            start_time = time.time()
            
            # Obter prompt formatado
            self.prompt_used = self.enrichment_profile_id.get_formatted_prompt(self.product_id)
            
            # Chamar serviço de IA
            result = self._call_ai_service()
            
            if not result:
                raise UserError(_("Falha ao chamar o serviço de IA"))
            
            # Processar resultado
            self._process_ai_result(result)
            
            # Calcular tempo de processamento
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Atualizar perfil de enriquecimento
            self.enrichment_profile_id.increment_usage(processing_time=processing_time)
            
            # Atualizar registro
            self.write({
                'state': 'done',
                'processing_time': processing_time,
                'processed_date': fields.Datetime.now()
            })
            
            # Se o perfil tiver análise competitiva habilitada
            if self.enrichment_profile_id.include_competitive_analysis:
                self._generate_competitive_analysis()
            
            # Se o perfil tiver sugestão de imagens habilitada
            if self.enrichment_profile_id.suggest_images:
                self._suggest_images()
            
            return True
            
        except Exception as e:
            self.write({
                'state': 'error',
                'error_message': str(e)
            })
            _logger.error(f"Erro ao processar enriquecimento {self.id}: {str(e)}")
            return False
    
    def _call_ai_service(self):
        """Chama o serviço de IA para enriquecimento."""
        # Implementação genérica. Em produção, use o cliente MCP-Odoo.
        try:
            # Obter configurações do MCP-Odoo
            mcp_url = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.url', 'http://localhost:8000')
            mcp_token = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.token', '')
            account_id = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.account_id', 'account_1')
            
            # Preparar a requisição
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
            }
            
            payload = {
                'account_id': account_id,
                'prompt': self.prompt_used,
                'max_tokens': self.enrichment_profile_id.max_tokens,
                'temperature': self.enrichment_profile_id.temperature,
                'enrichment_type': self.enrichment_profile_id.enrichment_type,
                'marketplace': self.marketplace_id.code if self.marketplace_id else None
            }
            
            # Fazer a requisição ao MCP-Odoo
            _logger.info(f"Chamando MCP-Odoo para enriquecimento do produto {self.product_id.id}")
            response = requests.post(
                f"{mcp_url}/tools/enrich_product",
                headers=headers,
                json=payload,
                timeout=120  # Timeout de 2 minutos (enriquecimento pode demorar)
            )
            
            # Verificar resposta
            if response.status_code == 200:
                result = response.json()
                self.raw_response = json.dumps(result)
                if result.get('success'):
                    return result
                else:
                    _logger.error(f"Erro do MCP-Odoo: {result.get('error')}")
                    raise UserError(result.get('error') or _("Erro desconhecido do serviço de IA"))
            else:
                _logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")
                raise UserError(_("Erro na chamada ao serviço de IA: %s") % response.text)
                
        except Exception as e:
            _logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
            raise UserError(_("Falha ao chamar o serviço de IA: %s") % str(e))
    
    def _process_ai_result(self, result):
        """Processa o resultado da IA."""
        data = result.get('data', {})
        
        # Extrair dados do resultado
        self.write({
            'enriched_title': data.get('title'),
            'enriched_description': data.get('description'),
            'enriched_keywords': data.get('keywords'),
            'enriched_bullet_points': data.get('bullet_points')
        })
    
    def _generate_competitive_analysis(self):
        """Gera análise competitiva para o produto."""
        # Implementação simplificada. Em produção, use um serviço dedicado.
        try:
            # Simulação de análise competitiva
            analysis = _("""
            ## Análise Competitiva
            
            ### Produtos Similares
            - 3 produtos similares encontrados no mercado
            - Preço médio: R$ %.2f
            - Características mais valorizadas: qualidade, durabilidade, design
            
            ### Diferenciais
            - Seu produto se destaca em: design, funcionalidade
            - Oportunidades de melhoria: preço, variedade de cores
            
            ### Sugestões
            - Destacar mais o design único na descrição
            - Considerar promoções para competir em preço
            - Adicionar mais detalhes técnicos na descrição
            """) % (self.product_id.list_price * 1.2)  # Simulação de preço médio
            
            self.write({
                'competitive_analysis': analysis
            })
            
        except Exception as e:
            _logger.error(f"Erro ao gerar análise competitiva: {str(e)}")
    
    def _suggest_images(self):
        """Sugere imagens complementares para o produto."""
        # Implementação simplificada. Em produção, use um serviço dedicado.
        try:
            # Simulação de sugestão de imagens
            # Em produção, integre com APIs de bancos de imagens ou DALL-E
            
            # Limpar sugestões anteriores
            self.suggested_image_ids.unlink()
            
            # Criar novas sugestões
            self.env['product.suggested.image'].create({
                'enrichment_id': self.id,
                'name': _("Imagem Principal"),
                'description': _("Sugestão para imagem principal do produto"),
                'source': 'ai',
                'relevance': 'high'
            })
            
            self.env['product.suggested.image'].create({
                'enrichment_id': self.id,
                'name': _("Detalhe do Produto"),
                'description': _("Imagem mostrando detalhes importantes"),
                'source': 'ai',
                'relevance': 'medium'
            })
            
        except Exception as e:
            _logger.error(f"Erro ao sugerir imagens: {str(e)}")
    
    def action_approve(self):
        """Aprova o enriquecimento e aplica ao produto."""
        self.ensure_one()
        
        if self.state != 'done':
            raise UserError(_("Apenas enriquecimentos concluídos podem ser aprovados"))
        
        # Marcar como aprovado
        self.write({
            'approved': True,
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })
        
        # Se tiver marketplace, criar ou atualizar descrição
        if self.marketplace_id:
            self._create_or_update_marketplace_description()
        
        # Vetorizar o produto
        self._vectorize_product()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sucesso'),
                'message': _('Enriquecimento aprovado e aplicado com sucesso'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def _create_or_update_marketplace_description(self):
        """Cria ou atualiza a descrição de marketplace."""
        # Buscar descrição existente
        description = self.env['product.marketplace.description'].search([
            ('product_id', '=', self.product_id.id),
            ('marketplace_id', '=', self.marketplace_id.id)
        ], limit=1)
        
        if description:
            # Atualizar descrição existente
            description.write({
                'title': self.enriched_title or self.original_title,
                'description': self.enriched_description,
                'keywords': self.enriched_keywords,
                'bullet_points': self.enriched_bullet_points,
                'enrichment_profile_id': self.enrichment_profile_id.id,
                'enrichment_date': fields.Datetime.now(),
                'verified': False,
                'verified_by': False,
                'verification_date': False,
                'validation_status': 'not_validated'
            })
            
            # Salvar versão
            description.save_version()
            
        else:
            # Criar nova descrição
            description = self.env['product.marketplace.description'].create({
                'product_id': self.product_id.id,
                'marketplace_id': self.marketplace_id.id,
                'title': self.enriched_title or self.original_title,
                'description': self.enriched_description,
                'keywords': self.enriched_keywords,
                'bullet_points': self.enriched_bullet_points,
                'enrichment_profile_id': self.enrichment_profile_id.id,
                'enrichment_date': fields.Datetime.now(),
                'publication_status': 'draft',
                'validation_status': 'not_validated'
            })
            
            # Salvar versão inicial
            description.save_version()
        
        # Atualizar referência
        self.marketplace_description_id = description.id
    
    def _vectorize_product(self):
        """Vetoriza o produto no Qdrant."""
        # Implementação genérica. Em produção, use o cliente MCP-Qdrant.
        try:
            # Obter configurações do MCP-Qdrant
            mcp_url = self.env['ir.config_parameter'].sudo().get_param('mcp_qdrant.url', 'http://localhost:8001')
            mcp_token = self.env['ir.config_parameter'].sudo().get_param('mcp_qdrant.token', '')
            account_id = self.env['ir.config_parameter'].sudo().get_param('mcp_qdrant.account_id', 'account_1')
            
            # Preparar a requisição
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
            }
            
            # Determinar o texto para vetorização
            if self.enrichment_profile_id.enrichment_type == 'basic':
                # Para enriquecimento básico, usar apenas título e descrição original
                text_for_vector = f"{self.original_title}\n{self.original_description}"
            else:
                # Para enriquecimento avançado, usar conteúdo enriquecido
                text_for_vector = f"{self.enriched_title or self.original_title}\n{self.enriched_description or self.original_description}"
                if self.enriched_keywords:
                    text_for_vector += f"\nPalavras-chave: {self.enriched_keywords}"
                if self.enriched_bullet_points:
                    text_for_vector += f"\nCaracterísticas: {self.enriched_bullet_points}"
            
            # Preparar payload
            payload = {
                'account_id': account_id,
                'collection_name': 'products',
                'document': {
                    'id': f"product_{self.product_id.id}",
                    'text': text_for_vector,
                    'metadata': {
                        'product_id': self.product_id.id,
                        'product_name': self.product_id.name,
                        'product_category': self.product_id.categ_id.name if self.product_id.categ_id else '',
                        'enrichment_type': self.enrichment_profile_id.enrichment_type,
                        'price': self.product_id.list_price,
                        'currency': self.env.company.currency_id.name,
                        'enrichment_date': fields.Datetime.now().isoformat(),
                    }
                }
            }
            
            # Fazer a requisição ao MCP-Qdrant
            _logger.info(f"Chamando MCP-Qdrant para vetorizar produto {self.product_id.id}")
            response = requests.post(
                f"{mcp_url}/store",
                headers=headers,
                json=payload,
                timeout=30  # Timeout de 30 segundos
            )
            
            # Verificar resposta
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Atualizar registro
                    self.write({
                        'vectorized': True,
                        'vectorization_date': fields.Datetime.now(),
                        'vector_id': result.get('id')
                    })
                    return True
                else:
                    _logger.error(f"Erro do MCP-Qdrant: {result.get('error')}")
            else:
                _logger.error(f"Erro na chamada ao MCP-Qdrant: {response.status_code} - {response.text}")
                
            return False
                
        except Exception as e:
            _logger.error(f"Exceção ao chamar MCP-Qdrant: {str(e)}")
            return False
    
    def action_cancel(self):
        """Cancela o enriquecimento."""
        self.ensure_one()
        
        if self.state in ['done', 'error', 'draft', 'pending']:
            self.write({
                'state': 'canceled'
            })
        else:
            raise UserError(_("Não é possível cancelar um enriquecimento em processamento"))
    
    def action_reset_to_draft(self):
        """Reseta o enriquecimento para rascunho."""
        self.ensure_one()
        
        if self.state in ['error', 'canceled']:
            self.write({
                'state': 'draft',
                'error_message': False
            })
        else:
            raise UserError(_("Apenas enriquecimentos com erro ou cancelados podem ser resetados"))
            
    def action_view_product(self):
        """Abre a vista do produto relacionado."""
        self.ensure_one()
        
        if not self.product_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aviso'),
                    'message': _('Este enriquecimento não está associado a nenhum produto.'),
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
    
    @api.model
    def process_scheduled_enrichments(self):
        """Processa enriquecimentos agendados."""
        enrichments = self.search([
            ('state', '=', 'pending'),
            ('scheduled_date', '<=', fields.Datetime.now())
        ])
        
        for enrichment in enrichments:
            try:
                enrichment.action_process()
            except Exception as e:
                _logger.error(f"Erro ao processar enriquecimento agendado {enrichment.id}: {str(e)}")
    
    @api.model
    def create_from_product(self, product_id, enrichment_profile_id, marketplace_id=False, schedule_date=False):
        """Cria um novo enriquecimento a partir de um produto."""
        # Verificar se o produto existe
        product = self.env['product.template'].browse(product_id)
        if not product.exists():
            raise UserError(_("Produto não encontrado"))
        
        # Verificar se o perfil existe
        profile = self.env['product.enrichment.profile'].browse(enrichment_profile_id)
        if not profile.exists():
            raise UserError(_("Perfil de enriquecimento não encontrado"))
        
        # Criar enriquecimento
        vals = {
            'product_id': product_id,
            'enrichment_profile_id': enrichment_profile_id,
            'created_by': self.env.user.id,
        }
        
        # Adicionar marketplace se fornecido
        if marketplace_id:
            marketplace = self.env['product.marketplace'].browse(marketplace_id)
            if marketplace.exists():
                vals['marketplace_id'] = marketplace_id
        
        # Adicionar data agendada se fornecida
        if schedule_date:
            vals['state'] = 'pending'
            vals['scheduled_date'] = schedule_date
        
        return self.create(vals)
