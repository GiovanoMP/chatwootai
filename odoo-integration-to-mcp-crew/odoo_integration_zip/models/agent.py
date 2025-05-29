# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
import uuid
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class UniversalAgent(models.Model):
    _name = 'odoo.integration.agent'
    _description = 'Agente Universal de IA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(required=True, default="Agente Universal", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Usuário Relacionado', tracking=True)
    
    # Configurações
    model_version = fields.Char(string="Versão do Modelo", default="1.0", tracking=True)
    temperature = fields.Float(string="Temperatura", default=0.7, tracking=True)
    max_tokens = fields.Integer(string="Máximo de Tokens", default=1024, tracking=True)
    
    # Estatísticas
    total_interactions = fields.Integer(string="Total de Interações", compute='_compute_statistics')
    success_rate = fields.Float(string="Taxa de Sucesso (%)", compute='_compute_statistics')
    
    # Histórico
    interaction_ids = fields.One2many('odoo.integration.interaction', 'agent_id', string="Histórico de Interações")
    
    # Relações
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)
    
    @api.depends('interaction_ids', 'interaction_ids.state')
    def _compute_statistics(self):
        for record in self:
            interactions = record.interaction_ids
            record.total_interactions = len(interactions)
            
            if record.total_interactions > 0:
                successful = len(interactions.filtered(lambda i: i.state == 'completed'))
                record.success_rate = (successful / record.total_interactions) * 100
            else:
                record.success_rate = 0.0
    
    def process_command(self, command, context=None):
        """
        Processa um comando em linguagem natural.
        
        Args:
            command: Texto do comando
            context: Contexto adicional (opcional)
            
        Returns:
            Resultado do processamento
        """
        # Cria registro de interação
        interaction = self.env['odoo.integration.interaction'].create({
            'agent_id': self.id,
            'user_id': self.env.user.id,
            'command': command,
            'context_data': json.dumps(context) if context else '{}',
            'state': 'processing',
        })
        
        try:
            # Analisa o comando
            intent, entities = self._analyze_command(command, context)
            
            # Executa a ação correspondente
            result = self._execute_action(intent, entities, context)
            
            # Atualiza a interação
            interaction.write({
                'intent': intent,
                'entities': json.dumps(entities),
                'result': json.dumps(result),
                'state': 'completed',
            })
            
            return result
        except Exception as e:
            # Registra erro
            interaction.write({
                'state': 'error',
                'result': str(e),
            })
            _logger.error("Erro ao processar comando '%s': %s", command, str(e))
            raise
    
    def _analyze_command(self, command, context):
        """
        Analisa um comando para determinar intenção e entidades.
        """
        # Conecta ao MCP-Crew para processamento de linguagem natural
        mcp_crew = self.env['odoo.integration.connector'].search(
            [('connector_type', '=', 'mcp_crew'), ('active', '=', True)],
            limit=1
        )
        
        if not mcp_crew:
            raise ValidationError(_("Nenhum conector MCP-Crew ativo encontrado"))
        
        # Envia comando para análise
        result = mcp_crew.send_request({
            'action': 'analyze_command',
            'command': command,
            'context': context,
        })
        
        return result.get('intent'), result.get('entities', {})
    
    def _execute_action(self, intent, entities, context):
        """
        Executa a ação correspondente à intenção detectada.
        """
        # Mapeia intenções para métodos
        intent_mapping = {
            'create_product': self._action_create_product,
            'update_price': self._action_update_price,
            'check_stock': self._action_check_stock,
            'create_promotion': self._action_create_promotion,
            'answer_question': self._action_answer_question,
            'sync_data': self._action_sync_data,
            # Mais mapeamentos...
        }
        
        # Verifica se a intenção é suportada
        if intent not in intent_mapping:
            return {
                'success': False,
                'message': _("Ainda não sei como %s.") % intent,
            }
        
        # Executa a ação
        action_method = intent_mapping[intent]
        return action_method(entities, context)
    
    # Implementações de ações específicas
    def _action_create_product(self, entities, context):
        """Cria um novo produto"""
        try:
            # Extrai informações do produto
            name = entities.get('product_name')
            if not name:
                return {
                    'success': False,
                    'message': _("Nome do produto não especificado"),
                }
                
            # Valores padrão
            vals = {
                'name': name,
                'type': 'product',
            }
            
            # Adiciona outros campos se disponíveis
            if 'price' in entities:
                vals['list_price'] = float(entities['price'])
                
            if 'description' in entities:
                vals['description'] = entities['description']
                
            if 'category' in entities:
                category = self.env['product.category'].search([('name', 'ilike', entities['category'])], limit=1)
                if category:
                    vals['categ_id'] = category.id
            
            # Cria o produto
            product = self.env['product.product'].create(vals)
            
            return {
                'success': True,
                'message': _("Produto '%s' criado com sucesso") % name,
                'product_id': product.id,
            }
        except Exception as e:
            _logger.error("Erro ao criar produto: %s", str(e))
            return {
                'success': False,
                'message': _("Erro ao criar produto: %s") % str(e),
            }
        
    def _action_update_price(self, entities, context):
        """Atualiza preço de produto(s)"""
        try:
            # Extrai informações
            product_name = entities.get('product_name')
            price = entities.get('price')
            
            if not product_name or not price:
                return {
                    'success': False,
                    'message': _("Nome do produto ou preço não especificado"),
                }
                
            # Busca produto(s)
            products = self.env['product.product'].search([('name', 'ilike', product_name)])
            
            if not products:
                return {
                    'success': False,
                    'message': _("Nenhum produto encontrado com o nome '%s'") % product_name,
                }
                
            # Atualiza preço
            products.write({'list_price': float(price)})
            
            return {
                'success': True,
                'message': _("%d produto(s) atualizado(s) com o preço %s") % (len(products), price),
                'product_ids': products.ids,
            }
        except Exception as e:
            _logger.error("Erro ao atualizar preço: %s", str(e))
            return {
                'success': False,
                'message': _("Erro ao atualizar preço: %s") % str(e),
            }
    
    def _action_check_stock(self, entities, context):
        """Verifica estoque de produto(s)"""
        # Implementação básica
        return {
            'success': True,
            'message': _("Função de verificação de estoque será implementada em breve"),
        }
        
    def _action_create_promotion(self, entities, context):
        """Cria uma promoção"""
        # Implementação básica
        return {
            'success': True,
            'message': _("Função de criação de promoção será implementada em breve"),
        }
        
    def _action_answer_question(self, entities, context):
        """Responde a uma pergunta"""
        # Implementação básica
        return {
            'success': True,
            'message': _("Função de resposta a perguntas será implementada em breve"),
        }
        
    def _action_sync_data(self, entities, context):
        """Sincroniza dados com plataformas externas"""
        # Implementação básica
        return {
            'success': True,
            'message': _("Função de sincronização de dados será implementada em breve"),
        }


class AgentInteraction(models.Model):
    _name = 'odoo.integration.interaction'
    _description = 'Interação com Agente'
    _order = 'create_date desc'
    
    agent_id = fields.Many2one('odoo.integration.agent', string='Agente', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Usuário', required=True)
    command = fields.Text(string='Comando', required=True)
    intent = fields.Char(string='Intenção Detectada')
    entities = fields.Text(string='Entidades Detectadas')
    context_data = fields.Text(string='Dados de Contexto')
    result = fields.Text(string='Resultado')
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('error', 'Erro'),
    ], string='Estado', default='draft')
    
    create_date = fields.Datetime(string='Data de Criação', readonly=True)
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.create_date.strftime('%Y-%m-%d %H:%M:%S')} - {record.command[:30]}"
            if len(record.command) > 30:
                name += "..."
            result.append((record.id, name))
        return result
