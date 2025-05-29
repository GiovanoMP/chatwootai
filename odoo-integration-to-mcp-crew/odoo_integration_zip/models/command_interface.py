# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class CommandInterface(models.Model):
    _name = 'odoo.integration.command.interface'
    _description = 'Interface de Comando IA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string="Nome", default="Interface de Comando", required=True)
    agent_id = fields.Many2one('odoo.integration.agent', string='Agente', required=True)
    user_id = fields.Many2one('res.users', string='Usuário', default=lambda self: self.env.user.id)
    
    # Configurações
    show_suggestions = fields.Boolean(string="Mostrar Sugestões", default=True)
    show_history = fields.Boolean(string="Mostrar Histórico", default=True)
    max_history = fields.Integer(string="Máximo de Histórico", default=10)
    
    # Histórico de comandos
    command_history_ids = fields.One2many('odoo.integration.command', 'interface_id', string="Histórico de Comandos")
    
    # Sugestões de comandos
    suggestion_ids = fields.One2many('odoo.integration.command.suggestion', 'interface_id', string="Sugestões de Comandos")
    
    # Relações
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)
    
    def send_command(self, command_text):
        """
        Envia um comando para o agente.
        
        Args:
            command_text: Texto do comando
            
        Returns:
            Comando criado
        """
        self.ensure_one()
        
        if not command_text:
            raise ValidationError(_("O comando não pode estar vazio"))
        
        # Cria o comando
        command = self.env['odoo.integration.command'].create({
            'interface_id': self.id,
            'user_id': self.user_id.id,
            'agent_id': self.agent_id.id,
            'command': command_text,
            'state': 'draft',
        })
        
        # Processa o comando
        command.send()
        
        return command
    
    def get_history(self):
        """
        Obtém o histórico de comandos.
        
        Returns:
            Lista de comandos
        """
        self.ensure_one()
        
        return self.command_history_ids.sorted(lambda c: c.create_date, reverse=True)[:self.max_history]
    
    def get_suggestions(self):
        """
        Obtém sugestões de comandos.
        
        Returns:
            Lista de sugestões
        """
        self.ensure_one()
        
        if not self.show_suggestions:
            return []
        
        return self.suggestion_ids.sorted(lambda s: s.sequence)
    
    def update_suggestions(self):
        """
        Atualiza as sugestões de comandos com base no histórico e contexto.
        """
        self.ensure_one()
        
        # Remove sugestões antigas
        self.suggestion_ids.unlink()
        
        # Cria sugestões padrão
        suggestions = [
            {
                'name': _("Criar Produto"),
                'command': _("Crie um novo produto chamado [nome] com preço [valor]"),
                'sequence': 10,
            },
            {
                'name': _("Atualizar Preço"),
                'command': _("Atualize o preço do produto [nome] para [valor]"),
                'sequence': 20,
            },
            {
                'name': _("Verificar Estoque"),
                'command': _("Verifique o estoque do produto [nome]"),
                'sequence': 30,
            },
            {
                'name': _("Criar Promoção"),
                'command': _("Crie uma promoção de [percentual]% para os produtos da categoria [categoria]"),
                'sequence': 40,
            },
            {
                'name': _("Sincronizar Dados"),
                'command': _("Sincronize os produtos com o Mercado Livre"),
                'sequence': 50,
            },
        ]
        
        # Cria as sugestões
        for suggestion in suggestions:
            self.env['odoo.integration.command.suggestion'].create({
                'interface_id': self.id,
                'name': suggestion['name'],
                'command': suggestion['command'],
                'sequence': suggestion['sequence'],
            })
        
        return True

class Command(models.Model):
    _name = 'odoo.integration.command'
    _description = 'Comando de IA'
    _order = 'create_date desc'
    
    interface_id = fields.Many2one('odoo.integration.command.interface', string='Interface', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Usuário', required=True)
    agent_id = fields.Many2one('odoo.integration.agent', string='Agente', required=True)
    
    command = fields.Text(string='Comando', required=True)
    response = fields.Text(string='Resposta')
    
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('sent', 'Enviado'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('error', 'Erro'),
    ], string='Estado', default='draft')
    
    create_date = fields.Datetime(string='Data de Criação', readonly=True)
    processed_date = fields.Datetime(string='Data de Processamento')
    
    # Dados adicionais
    intent = fields.Char(string='Intenção Detectada')
    entities = fields.Text(string='Entidades Detectadas')
    result_data = fields.Text(string='Dados do Resultado')
    
    def send(self):
        """
        Envia o comando para processamento.
        """
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError(_("O comando já foi enviado"))
        
        # Atualiza estado
        self.write({
            'state': 'sent',
        })
        
        # Processa em background para não bloquear a interface
        self.with_delay().process()
        
        return True
    
    def process(self):
        """
        Processa o comando (executado em background).
        """
        self.ensure_one()
        
        try:
            # Atualiza estado
            self.write({
                'state': 'processing',
            })
            
            # Obtém contexto da sessão
            context = self.env['odoo.integration.context'].get_context(self.user_id.id)
            
            # Processa comando
            result = self.agent_id.process_command(self.command, json.loads(context.context_data or '{}'))
            
            # Atualiza com resposta
            self.write({
                'response': result.get('message', ''),
                'intent': result.get('intent', ''),
                'entities': json.dumps(result.get('entities', {})),
                'result_data': json.dumps(result),
                'state': 'completed' if result.get('success', False) else 'error',
                'processed_date': fields.Datetime.now(),
            })
            
            return True
        except Exception as e:
            # Registra erro
            self.write({
                'response': str(e),
                'state': 'error',
                'processed_date': fields.Datetime.now(),
            })
            _logger.error("Erro ao processar comando '%s': %s", self.command, str(e))
            return False
    
    def retry(self):
        """
        Tenta processar o comando novamente.
        """
        self.ensure_one()
        
        if self.state not in ['error']:
            raise ValidationError(_("Apenas comandos com erro podem ser reprocessados"))
        
        # Reseta estado
        self.write({
            'state': 'draft',
            'response': False,
            'processed_date': False,
        })
        
        # Envia novamente
        return self.send()

class CommandSuggestion(models.Model):
    _name = 'odoo.integration.command.suggestion'
    _description = 'Sugestão de Comando'
    _order = 'sequence, id'
    
    interface_id = fields.Many2one('odoo.integration.command.interface', string='Interface', required=True, ondelete='cascade')
    name = fields.Char(string='Nome', required=True)
    command = fields.Text(string='Comando', required=True)
    description = fields.Text(string='Descrição')
    sequence = fields.Integer(string='Sequência', default=10)
    
    # Categorização
    category = fields.Selection([
        ('product', 'Produto'),
        ('order', 'Pedido'),
        ('inventory', 'Estoque'),
        ('marketing', 'Marketing'),
        ('sync', 'Sincronização'),
        ('other', 'Outro'),
    ], string='Categoria', default='other')
    
    # Estatísticas
    usage_count = fields.Integer(string='Contagem de Uso', default=0)
    
    def use_suggestion(self):
        """
        Utiliza esta sugestão como comando.
        
        Returns:
            Comando criado
        """
        self.ensure_one()
        
        # Incrementa contagem de uso
        self.write({
            'usage_count': self.usage_count + 1,
        })
        
        # Cria e envia o comando
        return self.interface_id.send_command(self.command)
