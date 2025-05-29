# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
import base64
import requests
from io import BytesIO
from PIL import Image

_logger = logging.getLogger(__name__)

class ProductSuggestedImage(models.Model):
    _name = 'product.suggested.image'
    _description = 'Imagem Sugerida para Produto'
    _order = 'sequence, id'
    
    name = fields.Char(
        string='Nome',
        required=True,
        help='Nome da imagem sugerida'
    )
    
    sequence = fields.Integer(
        string='Sequência',
        default=10,
        help='Determina a ordem de exibição das imagens'
    )
    
    description = fields.Text(
        string='Descrição',
        help='Descrição da imagem sugerida'
    )
    
    # Relações
    enrichment_id = fields.Many2one(
        'product.enrichment',
        string='Enriquecimento',
        ondelete='cascade',
        help='Enriquecimento relacionado'
    )
    
    product_id = fields.Many2one(
        related='enrichment_id.product_id',
        string='Produto',
        store=True,
        readonly=True,
        help='Produto relacionado'
    )
    
    marketplace_id = fields.Many2one(
        'product.marketplace',
        string='Marketplace',
        store=True,
        readonly=True,
        help='Marketplace relacionado'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Empresa',
        related='enrichment_id.company_id',
        store=True,
        readonly=True,
        help='Empresa à qual esta imagem pertence'
    )
    
    # Campos de imagem
    image = fields.Binary(
        string='Imagem',
        attachment=True,
        help='Imagem sugerida'
    )
    
    image_url = fields.Char(
        string='URL da Imagem',
        help='URL da imagem sugerida'
    )
    
    image_preview = fields.Binary(
        string='Prévia da Imagem',
        attachment=True,
        help='Prévia da imagem sugerida'
    )
    
    # Campos de metadados
    source = fields.Selection([
        ('ai', 'Inteligência Artificial'),
        ('search', 'Busca na Web'),
        ('stock', 'Banco de Imagens'),
        ('generated', 'Gerada por IA')
    ], string='Fonte', 
       default='ai',
       help='Fonte da imagem sugerida')
       
    source_url = fields.Char(
        string='URL da Fonte',
        help='URL da fonte da imagem'
    )
    
    image_type = fields.Selection([
        ('main', 'Principal'),
        ('gallery', 'Galeria'),
        ('variant', 'Variante')
    ], string='Tipo de Imagem',
       default='gallery',
       help='Tipo de imagem sugerida')
       
    width = fields.Integer(
        string='Largura',
        readonly=True,
        help='Largura da imagem em pixels'
    )
    
    height = fields.Integer(
        string='Altura',
        readonly=True,
        help='Altura da imagem em pixels'
    )
    
    relevance = fields.Selection([
        ('high', 'Alta'),
        ('medium', 'Média'),
        ('low', 'Baixa')
    ], string='Relevância', 
       default='medium',
       help='Relevância da imagem para o produto')
    
    # Campos de controle
    state = fields.Selection([
        ('pending', 'Pendente'),
        ('approved', 'Aprovada'),
        ('rejected', 'Rejeitada')
    ], string='Estado', 
       default='pending',
       tracking=True,
       help='Estado atual da imagem sugerida')
    
    approved = fields.Boolean(
        string='Aprovada',
        default=False,
        help='Indica se a imagem foi aprovada'
    )
    
    approved_by = fields.Many2one(
        'res.users',
        string='Aprovada por',
        help='Usuário que aprovou esta imagem'
    )
    
    approval_date = fields.Datetime(
        string='Data de Aprovação',
        help='Data e hora da aprovação'
    )
    
    rejected_by = fields.Many2one(
        'res.users',
        string='Rejeitada por',
        help='Usuário que rejeitou esta imagem'
    )
    
    rejection_date = fields.Datetime(
        string='Data de Rejeição',
        help='Data e hora da rejeição'
    )
    
    rejection_reason = fields.Text(
        string='Motivo da Rejeição',
        help='Motivo pelo qual a imagem foi rejeitada'
    )
    
    # Campos para geração
    prompt_used = fields.Text(
        string='Prompt Utilizado',
        help='Prompt utilizado para gerar a imagem'
    )
    
    generation_params = fields.Text(
        string='Parâmetros de Geração',
        help='Parâmetros utilizados para gerar a imagem'
    )
    
    # Métodos
    @api.model
    def create(self, vals):
        """Sobrescreve o método create para processar a URL da imagem."""
        res = super(ProductSuggestedImage, self).create(vals)
        
        # Se tiver URL da imagem, baixar e processar
        if res.image_url and not res.image:
            res._fetch_image_from_url()
        
        return res
    
    def write(self, vals):
        """Sobrescreve o método write para processar a URL da imagem."""
        res = super(ProductSuggestedImage, self).write(vals)
        
        # Se a URL da imagem foi atualizada, baixar e processar
        if 'image_url' in vals and not vals.get('image'):
            for record in self:
                if record.image_url:
                    record._fetch_image_from_url()
        
        return res
    
    def _fetch_image_from_url(self):
        """Baixa a imagem da URL e a processa."""
        self.ensure_one()
        
        if not self.image_url:
            return False
        
        try:
            # Baixar imagem
            response = requests.get(self.image_url, timeout=10)
            if response.status_code != 200:
                _logger.error(f"Erro ao baixar imagem: {response.status_code} - {response.text}")
                return False
            
            # Processar imagem
            image_data = BytesIO(response.content)
            img = Image.open(image_data)
            
            # Converter para formato web-friendly
            output = BytesIO()
            if img.format == 'PNG':
                img.save(output, format='PNG')
            else:
                img.convert('RGB').save(output, format='JPEG', quality=85)
            
            # Criar prévia
            preview = BytesIO()
            img.thumbnail((200, 200))
            if img.format == 'PNG':
                img.save(preview, format='PNG')
            else:
                img.convert('RGB').save(preview, format='JPEG', quality=85)
            
            # Atualizar campos
            self.write({
                'image': base64.b64encode(output.getvalue()),
                'image_preview': base64.b64encode(preview.getvalue())
            })
            
            return True
            
        except Exception as e:
            _logger.error(f"Erro ao processar imagem da URL {self.image_url}: {str(e)}")
            return False
    
    def action_approve(self):
        """Aprova a imagem sugerida."""
        self.ensure_one()
        
        if not self.image:
            raise UserError(_("Não é possível aprovar uma imagem vazia"))
        
        # Marcar como aprovada
        self.write({
            'state': 'approved',
            'approved': True,
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'rejected_by': False,
            'rejection_date': False,
            'rejection_reason': False
        })
        
        # Adicionar à galeria do produto
        self._add_to_product_gallery()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sucesso'),
                'message': _('Imagem aprovada e adicionada à galeria do produto'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_reject(self):
        """Rejeita a imagem sugerida."""
        self.ensure_one()
        
        if self.state == 'rejected':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aviso'),
                    'message': _('Esta imagem já foi rejeitada'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Atualizar campos
        self.write({
            'state': 'rejected',
            'approved': False,
            'rejected_by': self.env.user.id,
            'rejection_date': fields.Datetime.now()
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sucesso'),
                'message': _('Imagem rejeitada com sucesso'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_reset(self):
        """Reseta a imagem para o estado pendente."""
        self.ensure_one()
        
        if self.state == 'pending':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aviso'),
                    'message': _('Esta imagem já está pendente'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Atualizar campos
        self.write({
            'state': 'pending',
            'approved': False,
            'approved_by': False,
            'approval_date': False,
            'rejected_by': False,
            'rejection_date': False,
            'rejection_reason': False
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sucesso'),
                'message': _('Imagem resetada com sucesso'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def _add_to_product_gallery(self):
        """Adiciona a imagem à galeria do produto."""
        self.ensure_one()
        
        if not self.product_id or not self.image:
            return False
        
        try:
            # Criar imagem de produto
            self.env['product.image'].create({
                'name': self.name,
                'product_tmpl_id': self.product_id.id,
                'image_1920': self.image
            })
            
            return True
        except Exception as e:
            _logger.error(f"Erro ao adicionar imagem à galeria: {str(e)}")
            return False
    
    def action_generate_with_dalle(self):
        """Gera uma imagem com DALL-E."""
        self.ensure_one()
        
        # Implementação simplificada. Em produção, use a API do DALL-E.
        if not self.enrichment_id or not self.enrichment_id.product_id:
            raise UserError(_("Enriquecimento ou produto não encontrado"))
        
        try:
            # Gerar prompt para DALL-E
            product = self.enrichment_id.product_id
            prompt = f"Uma imagem profissional e realista de {product.name}"
            
            if product.description:
                # Adicionar detalhes da descrição
                prompt += f", {product.description[:200]}"
            
            # Adicionar estilo
            prompt += ", fundo branco, iluminação profissional, alta qualidade, fotografia de produto"
            
            # Atualizar prompt
            self.write({
                'prompt_used': prompt,
                'generation_params': '{"model": "dall-e-3", "size": "1024x1024", "quality": "standard"}'
            })
            
            # Em produção, chamar a API do DALL-E aqui
            # Por enquanto, apenas simular com uma imagem de placeholder
            placeholder_url = "https://placehold.co/1024x1024/FFFFFF/333333?text=Imagem+Simulada"
            self.write({
                'image_url': placeholder_url
            })
            self._fetch_image_from_url()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sucesso'),
                    'message': _('Imagem gerada com sucesso (simulação)'),
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
                    'message': _('Falha ao gerar imagem: %s') % str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
    
    def action_search_stock_images(self):
        """Busca imagens em bancos de imagens."""
        self.ensure_one()
        
        # Implementação simplificada. Em produção, use APIs de bancos de imagens.
        if not self.enrichment_id or not self.enrichment_id.product_id:
            raise UserError(_("Enriquecimento ou produto não encontrado"))
        
        try:
            # Simular busca de imagens
            product = self.enrichment_id.product_id
            
            # Atualizar fonte
            self.write({
                'source': 'stock'
            })
            
            # Em produção, chamar APIs de bancos de imagens aqui
            # Por enquanto, apenas simular com uma imagem de placeholder
            placeholder_url = "https://placehold.co/1024x1024/EFEFEF/333333?text=Imagem+de+Banco"
            self.write({
                'image_url': placeholder_url
            })
            self._fetch_image_from_url()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sucesso'),
                    'message': _('Imagem de banco encontrada (simulação)'),
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
                    'message': _('Falha ao buscar imagem: %s') % str(e),
                    'sticky': True,
                    'type': 'danger',
                }
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
                    'message': _('Esta imagem não está associada a nenhum produto.'),
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
    
    def action_view_enrichment(self):
        """Abre a vista do enriquecimento relacionado."""
        self.ensure_one()
        
        if not self.enrichment_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aviso'),
                    'message': _('Esta imagem não está associada a nenhum enriquecimento.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        return {
            'name': _('Enriquecimento'),
            'view_mode': 'form',
            'res_model': 'product.enrichment',
            'res_id': self.enrichment_id.id,
            'type': 'ir.actions.act_window',
            'context': {'create': False}
        }
