# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class EnrichmentProfile(models.Model):
    _name = 'product.enrichment.profile'
    _description = 'Perfil de Enriquecimento de Produto'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Nome', 
        required=True,
        help='Nome do perfil de enriquecimento'
    )
    
    active = fields.Boolean(
        string='Ativo', 
        default=True,
        help='Se desativado, este perfil não será disponível para seleção'
    )
    
    sequence = fields.Integer(
        string='Sequência', 
        default=10,
        help='Determina a ordem de exibição dos perfis'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        help='Empresa à qual este perfil pertence'
    )
    
    description = fields.Text(
        string='Descrição',
        help='Descrição detalhada do perfil e seu propósito'
    )
    
    # Tipo de enriquecimento
    enrichment_type = fields.Selection([
        ('basic', 'Básico'),
        ('advanced', 'Avançado'),
        ('premium', 'Premium')
    ], string='Tipo de Enriquecimento', 
       default='basic', 
       required=True,
       help='Determina o nível de detalhamento do enriquecimento')
    
    # Configurações de IA
    prompt_template = fields.Text(
        string='Template de Prompt',
        required=True,
        default="""
Enriqueça a descrição do seguinte produto:

Nome: {{product_name}}
Categoria: {{product_category}}
Descrição atual: {{product_description}}

Forneça uma descrição mais detalhada, destacando:
1. Principais características
2. Benefícios para o cliente
3. Diferenciais do produto
        """,
        help='Template de prompt para a IA. Use {{variáveis}} para substituição dinâmica'
    )
    
    max_tokens = fields.Integer(
        string='Máximo de Tokens',
        default=500,
        help='Limite máximo de tokens para a resposta da IA'
    )
    
    temperature = fields.Float(
        string='Temperatura',
        default=0.7,
        help='Controla a criatividade da IA (0.0 a 1.0)'
    )
    
    # Marketplace relacionado
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        help='Marketplace específico para este perfil'
    )
    
    # Opções avançadas
    include_competitive_analysis = fields.Boolean(
        string='Incluir Análise Competitiva',
        default=False,
        help='Incluir análise de produtos similares no mercado'
    )
    
    suggest_images = fields.Boolean(
        string='Sugerir Imagens',
        default=False,
        help='Sugerir imagens complementares para o produto'
    )
    
    auto_publish = fields.Boolean(
        string='Publicação Automática',
        default=False,
        help='Publicar automaticamente após enriquecimento'
    )
    
    # Campos para controle de uso
    usage_count = fields.Integer(
        string='Contagem de Uso',
        default=0,
        readonly=True,
        help='Número de vezes que este perfil foi utilizado'
    )
    
    last_used = fields.Datetime(
        string='Último Uso',
        readonly=True,
        help='Data e hora do último uso deste perfil'
    )
    
    # Campos para estatísticas
    avg_processing_time = fields.Float(
        string='Tempo Médio de Processamento (s)',
        readonly=True,
        help='Tempo médio de processamento em segundos'
    )
    
    success_rate = fields.Float(
        string='Taxa de Sucesso (%)',
        readonly=True,
        help='Percentual de enriquecimentos bem-sucedidos'
    )
    
    # Relações
    product_category_ids = fields.Many2many(
        'product.category',
        string='Categorias de Produto',
        help='Categorias de produto para as quais este perfil é recomendado'
    )
    
    # Métodos
    @api.constrains('temperature')
    def _check_temperature(self):
        for record in self:
            if record.temperature < 0.0 or record.temperature > 1.0:
                raise ValidationError(_("A temperatura deve estar entre 0.0 e 1.0"))
    
    @api.constrains('max_tokens')
    def _check_max_tokens(self):
        for record in self:
            if record.max_tokens < 100:
                raise ValidationError(_("O máximo de tokens deve ser pelo menos 100"))
            if record.max_tokens > 4000:
                raise ValidationError(_("O máximo de tokens não deve exceder 4000"))
    
    def increment_usage(self, processing_time=None, success=True):
        """Incrementa o contador de uso e atualiza estatísticas."""
        self.ensure_one()
        self.usage_count += 1
        self.last_used = fields.Datetime.now()
        
        if processing_time:
            # Atualizar tempo médio de processamento
            current_total = self.avg_processing_time * (self.usage_count - 1)
            new_avg = (current_total + processing_time) / self.usage_count
            self.avg_processing_time = new_avg
        
        if not success:
            # Atualizar taxa de sucesso
            current_successes = self.success_rate * (self.usage_count - 1) / 100
            new_rate = (current_successes) / self.usage_count * 100
            self.success_rate = new_rate
        elif self.usage_count == 1:
            self.success_rate = 100.0
        else:
            current_successes = self.success_rate * (self.usage_count - 1) / 100
            new_rate = (current_successes + 1) / self.usage_count * 100
            self.success_rate = new_rate
    
    def get_formatted_prompt(self, product):
        """Retorna o prompt formatado com os dados do produto."""
        self.ensure_one()
        
        # Obter dados básicos do produto
        product_data = {
            'product_name': product.name,
            'product_category': product.categ_id.name if product.categ_id else '',
            'product_description': product.description or product.description_sale or '',
            'product_list_price': product.list_price,
            'product_default_code': product.default_code or '',
            'product_barcode': product.barcode or '',
        }
        
        # Substituir variáveis no template
        prompt = self.prompt_template
        for key, value in product_data.items():
            prompt = prompt.replace('{{' + key + '}}', str(value))
        
        return prompt
