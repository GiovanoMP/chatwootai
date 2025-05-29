# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class ContextManager(models.Model):
    _name = 'odoo.integration.context'
    _description = 'Gerenciador de Contexto'
    
    user_id = fields.Many2one('res.users', string='Usuário', required=True)
    context_data = fields.Text(string='Dados de Contexto', default='{}')
    last_update = fields.Datetime(string='Última Atualização')
    
    _sql_constraints = [
        ('unique_user', 'unique(user_id)', 'Já existe um contexto para este usuário'),
    ]
    
    @api.model
    def get_context(self, user_id):
        """
        Obtém ou cria o contexto para um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Registro de contexto
        """
        context = self.search([('user_id', '=', user_id)], limit=1)
        
        if not context:
            context = self.create({
                'user_id': user_id,
                'last_update': fields.Datetime.now(),
            })
        
        return context
    
    def update_context(self, data):
        """
        Atualiza o contexto com novos dados.
        
        Args:
            data: Dicionário com dados a serem atualizados
            
        Returns:
            Contexto atualizado
        """
        self.ensure_one()
        
        try:
            # Carrega contexto atual
            current_context = json.loads(self.context_data or '{}')
            
            # Atualiza com novos dados
            current_context.update(data)
            
            # Salva contexto atualizado
            self.write({
                'context_data': json.dumps(current_context),
                'last_update': fields.Datetime.now(),
            })
            
            return self
        except Exception as e:
            _logger.error("Erro ao atualizar contexto: %s", str(e))
            raise
    
    def clear_context(self):
        """
        Limpa o contexto.
        
        Returns:
            Contexto limpo
        """
        self.ensure_one()
        
        self.write({
            'context_data': '{}',
            'last_update': fields.Datetime.now(),
        })
        
        return self
    
    def get_value(self, key, default=None):
        """
        Obtém um valor específico do contexto.
        
        Args:
            key: Chave a ser buscada
            default: Valor padrão se a chave não existir
            
        Returns:
            Valor da chave ou valor padrão
        """
        self.ensure_one()
        
        try:
            context = json.loads(self.context_data or '{}')
            return context.get(key, default)
        except Exception as e:
            _logger.error("Erro ao obter valor do contexto: %s", str(e))
            return default
    
    def set_value(self, key, value):
        """
        Define um valor específico no contexto.
        
        Args:
            key: Chave a ser definida
            value: Valor a ser armazenado
            
        Returns:
            Contexto atualizado
        """
        self.ensure_one()
        
        try:
            context = json.loads(self.context_data or '{}')
            context[key] = value
            
            self.write({
                'context_data': json.dumps(context),
                'last_update': fields.Datetime.now(),
            })
            
            return self
        except Exception as e:
            _logger.error("Erro ao definir valor no contexto: %s", str(e))
            raise
