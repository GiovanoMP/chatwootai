# -*- coding: utf-8 -*-

"""
Exemplo de como outros módulos Odoo podem obter credenciais do ai_credentials_manager.
"""

import json
import requests
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SemanticProductDescription(models.Model):
    """
    Exemplo de modelo que usa credenciais do ai_credentials_manager.
    """
    _name = 'semantic.product.description'
    _description = 'Descrição Semântica de Produto'

    name = fields.Char(string='Nome', related='product_id.name', store=True)
    product_id = fields.Many2one('product.product', string='Produto', required=True)
    description = fields.Text(string='Descrição', required=True)
    
    # Campos de status
    generation_status = fields.Selection([
        ('not_generated', 'Não Gerado'),
        ('generating', 'Gerando'),
        ('generated', 'Gerado'),
        ('error', 'Erro')
    ], string='Status de Geração', default='not_generated')
    
    last_generation = fields.Datetime(string='Última Geração')
    error_message = fields.Text(string='Mensagem de Erro')
    
    def generate_description(self):
        """
        Gera uma descrição semântica para o produto usando o sistema de IA.
        """
        self.ensure_one()
        
        try:
            # Atualizar status
            self.write({
                'generation_status': 'generating',
                'error_message': False
            })
            
            # Obter credenciais do ai_credentials_manager
            credentials = self._get_ai_credentials()
            
            if not credentials:
                raise ValueError("Credenciais não encontradas")
            
            # Preparar payload
            payload = {
                'source': 'semantic_product_description',
                'event': 'generate_description',
                'account_id': credentials.get('odoo_db'),
                'product': {
                    'id': self.product_id.id,
                    'name': self.product_id.name,
                    'default_code': self.product_id.default_code,
                    'categ_id': self.product_id.categ_id.name,
                    'list_price': self.product_id.list_price,
                    'description': self.product_id.description or '',
                    'description_sale': self.product_id.description_sale or '',
                }
            }
            
            # Adicionar credenciais ao payload
            payload['credentials'] = {
                'token': credentials.get('token')
            }
            
            # Obter URL da API a partir das configurações
            api_url = self.env['ir.config_parameter'].sudo().get_param('semantic_product_description.api_url', 'http://localhost:8000/api/semantic_product_description/generate')
            
            # Enviar requisição para a API
            headers = {'Content-Type': 'application/json'}
            response = requests.post(api_url, data=json.dumps(payload), headers=headers, timeout=30)
            
            # Verificar resposta
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    # Atualizar descrição e status
                    self.write({
                        'description': result.get('description'),
                        'generation_status': 'generated',
                        'last_generation': fields.Datetime.now()
                    })
                    
                    _logger.info(f"Descrição gerada com sucesso para o produto {self.product_id.name}")
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Sucesso',
                            'message': 'Descrição gerada com sucesso',
                            'sticky': False,
                            'type': 'success'
                        }
                    }
                else:
                    # Atualizar status
                    self.write({
                        'generation_status': 'error',
                        'error_message': result.get('error', 'Erro desconhecido')
                    })
                    
                    _logger.error(f"Erro ao gerar descrição: {result.get('error')}")
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Erro',
                            'message': f"Erro ao gerar descrição: {result.get('error')}",
                            'sticky': True,
                            'type': 'danger'
                        }
                    }
            else:
                # Atualizar status
                self.write({
                    'generation_status': 'error',
                    'error_message': f"Erro HTTP {response.status_code}: {response.text}"
                })
                
                _logger.error(f"Erro HTTP {response.status_code} ao gerar descrição: {response.text}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Erro',
                        'message': f"Erro HTTP {response.status_code} ao gerar descrição",
                        'sticky': True,
                        'type': 'danger'
                    }
                }
                
        except Exception as e:
            # Atualizar status
            self.write({
                'generation_status': 'error',
                'error_message': str(e)
            })
            
            _logger.exception(f"Exceção ao gerar descrição: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erro',
                    'message': f"Exceção ao gerar descrição: {str(e)}",
                    'sticky': True,
                    'type': 'danger'
                }
            }
    
    def _get_ai_credentials(self):
        """
        Obtém as credenciais do ai_credentials_manager.
        """
        # Buscar registro de credenciais
        credentials_manager = self.env['ai.credentials.manager'].search([], limit=1)
        
        if not credentials_manager:
            _logger.error("Nenhum registro de credenciais encontrado")
            return None
        
        # Obter credenciais
        return credentials_manager.get_credentials()
