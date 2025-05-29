# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
import requests
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class MCPCrewConnector(models.Model):
    _inherit = 'odoo.integration.connector'
    
    # Campos específicos para MCP-Crew
    crew_endpoint = fields.Char(string="Endpoint da Crew", help="Endpoint específico para operações de crew")
    decision_engine_endpoint = fields.Char(string="Endpoint do Motor de Decisão", help="Endpoint para o motor de decisão inteligente")
    
    # Configurações do motor de decisão
    use_decision_engine = fields.Boolean(string="Usar Motor de Decisão", default=True)
    decision_weights = fields.Text(string="Pesos de Decisão", 
                                  default='''{
                                      "content": 0.4,
                                      "context": 0.3,
                                      "rules": 0.3,
                                      "content_weights": {
                                          "intent": 0.5,
                                          "entities": 0.3,
                                          "sentiment": 0.2
                                      },
                                      "context_weights": {
                                          "channel": 0.4,
                                          "history": 0.4,
                                          "metadata": 0.2
                                      }
                                  }''')
    
    # Estatísticas específicas
    total_decisions = fields.Integer(string="Total de Decisões", default=0)
    decision_success_rate = fields.Float(string="Taxa de Sucesso de Decisões (%)", compute='_compute_decision_success_rate')
    
    # Relações específicas
    crew_ids = fields.One2many('odoo.integration.crew', 'connector_id', string="Crews")
    
    @api.depends('total_decisions', 'success_count')
    def _compute_decision_success_rate(self):
        for record in self:
            if record.total_decisions > 0:
                record.decision_success_rate = (record.success_count / record.total_decisions) * 100
            else:
                record.decision_success_rate = 0.0
    
    def _connect_mcp_crew(self):
        """
        Implementação específica para conectar ao MCP-Crew.
        """
        try:
            # Verifica se os endpoints estão configurados
            if not self.endpoint:
                raise ValidationError(_("Endpoint principal não configurado"))
            
            if not self.crew_endpoint:
                self.crew_endpoint = self.endpoint + '/crews'
            
            if not self.decision_engine_endpoint:
                self.decision_engine_endpoint = self.endpoint + '/decision'
            
            # Testa conexão com o endpoint principal
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                self.endpoint + '/status',
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                raise ValidationError(_("Falha ao conectar com MCP-Crew: %s") % response.text)
            
            # Testa conexão com o endpoint de crews
            response = requests.get(
                self.crew_endpoint,
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                raise ValidationError(_("Falha ao conectar com endpoint de crews: %s") % response.text)
            
            # Testa conexão com o motor de decisão
            if self.use_decision_engine:
                response = requests.get(
                    self.decision_engine_endpoint + '/status',
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code != 200:
                    raise ValidationError(_("Falha ao conectar com motor de decisão: %s") % response.text)
            
            # Sincroniza crews disponíveis
            self._sync_available_crews()
            
            return True
        except Exception as e:
            _logger.error("Erro ao conectar com MCP-Crew: %s", str(e))
            raise
    
    def _send_request_mcp_crew(self, data):
        """
        Implementação específica para enviar requisição ao MCP-Crew.
        """
        try:
            # Prepara headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Determina endpoint com base na ação
            action = data.get('action', '')
            endpoint = self.endpoint
            
            if action.startswith('crew_'):
                endpoint = self.crew_endpoint
                data['action'] = action[5:]  # Remove prefixo 'crew_'
            elif action.startswith('decision_'):
                endpoint = self.decision_engine_endpoint
                data['action'] = action[9:]  # Remove prefixo 'decision_'
            
            # Adiciona endpoint específico se fornecido
            if 'endpoint' in data:
                endpoint = data.pop('endpoint')
            
            # Envia requisição
            response = requests.post(
                endpoint + '/api',
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Verifica resposta
            if response.status_code != 200:
                error_msg = f"Erro ao enviar requisição para MCP-Crew: {response.text}"
                _logger.error(error_msg)
                raise ValidationError(_(error_msg))
            
            # Atualiza estatísticas se for uma decisão
            if action.startswith('decision_'):
                self.write({
                    'total_decisions': self.total_decisions + 1,
                })
            
            return response.json()
        except Exception as e:
            _logger.error("Erro ao enviar requisição para MCP-Crew: %s", str(e))
            raise
    
    def _sync_available_crews(self):
        """
        Sincroniza as crews disponíveis no MCP-Crew.
        """
        try:
            # Busca crews disponíveis
            result = self._send_request_mcp_crew({
                'action': 'crew_list_crews',
            })
            
            crews = result.get('crews', [])
            _logger.info("Recebidas %d crews do MCP-Crew", len(crews))
            
            # Atualiza crews no Odoo
            for crew_data in crews:
                crew_id = crew_data.get('id')
                
                # Verifica se a crew já existe
                crew = self.env['odoo.integration.crew'].search([
                    ('connector_id', '=', self.id),
                    ('external_id', '=', crew_id),
                ], limit=1)
                
                if crew:
                    # Atualiza crew existente
                    crew.write({
                        'name': crew_data.get('name'),
                        'description': crew_data.get('description'),
                        'specialties': json.dumps(crew_data.get('specialties', [])),
                        'active': crew_data.get('active', True),
                    })
                else:
                    # Cria nova crew
                    self.env['odoo.integration.crew'].create({
                        'connector_id': self.id,
                        'external_id': crew_id,
                        'name': crew_data.get('name'),
                        'description': crew_data.get('description'),
                        'specialties': json.dumps(crew_data.get('specialties', [])),
                        'active': crew_data.get('active', True),
                    })
            
            return True
        except Exception as e:
            _logger.error("Erro ao sincronizar crews disponíveis: %s", str(e))
            raise
    
    def make_decision(self, message, context=None):
        """
        Utiliza o motor de decisão inteligente para determinar qual crew deve processar uma mensagem.
        
        Args:
            message: Texto da mensagem
            context: Contexto adicional (opcional)
            
        Returns:
            Crew selecionada e dados da decisão
        """
        if not self.use_decision_engine:
            # Se o motor de decisão estiver desativado, usa a primeira crew disponível
            crew = self.env['odoo.integration.crew'].search([
                ('connector_id', '=', self.id),
                ('active', '=', True),
            ], limit=1)
            
            if not crew:
                raise ValidationError(_("Nenhuma crew disponível"))
            
            return crew, {'method': 'default'}
        
        try:
            # Prepara dados para o motor de decisão
            decision_data = {
                'action': 'decision_route_message',
                'message': message,
                'context': context or {},
                'weights': json.loads(self.decision_weights),
            }
            
            # Envia requisição para o motor de decisão
            result = self._send_request_mcp_crew(decision_data)
            
            # Busca a crew selecionada
            selected_crew_id = result.get('selected_crew')
            crew = self.env['odoo.integration.crew'].search([
                ('connector_id', '=', self.id),
                ('external_id', '=', selected_crew_id),
            ], limit=1)
            
            if not crew:
                raise ValidationError(_("Crew selecionada não encontrada: %s") % selected_crew_id)
            
            return crew, result
        except Exception as e:
            _logger.error("Erro ao utilizar motor de decisão: %s", str(e))
            raise

class Crew(models.Model):
    _name = 'odoo.integration.crew'
    _description = 'Crew de IA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string="Nome", required=True, tracking=True)
    description = fields.Text(string="Descrição", tracking=True)
    connector_id = fields.Many2one('odoo.integration.connector', string="Conector MCP", required=True, domain=[('connector_type', '=', 'mcp_crew')], tracking=True)
    external_id = fields.Char(string="ID Externo", required=True, tracking=True)
    
    specialties = fields.Text(string="Especialidades", help="Lista de especialidades da crew em formato JSON", tracking=True)
    specialties_list = fields.Char(string="Especialidades", compute='_compute_specialties_list')
    
    active = fields.Boolean(string="Ativo", default=True, tracking=True)
    
    # Estatísticas
    total_requests = fields.Integer(string="Total de Requisições", default=0)
    success_count = fields.Integer(string="Requisições com Sucesso", default=0)
    error_count = fields.Integer(string="Requisições com Erro", default=0)
    
    # Relações
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)
    
    @api.depends('specialties')
    def _compute_specialties_list(self):
        for record in self:
            if record.specialties:
                try:
                    specialties = json.loads(record.specialties)
                    record.specialties_list = ', '.join(specialties)
                except:
                    record.specialties_list = record.specialties
            else:
                record.specialties_list = ''
    
    def send_request(self, data):
        """
        Envia uma requisição para a crew.
        """
        self.ensure_one()
        
        try:
            # Adiciona ID da crew aos dados
            data['crew_id'] = self.external_id
            
            # Adiciona prefixo 'crew_' à ação
            if 'action' in data and not data['action'].startswith('crew_'):
                data['action'] = 'crew_' + data['action']
            
            # Envia requisição via conector
            result = self.connector_id.send_request(data)
            
            # Atualiza estatísticas
            self.write({
                'total_requests': self.total_requests + 1,
                'success_count': self.success_count + 1,
            })
            
            return result
        except Exception as e:
            # Atualiza estatísticas de erro
            self.write({
                'total_requests': self.total_requests + 1,
                'error_count': self.error_count + 1,
            })
            
            _logger.error("Erro ao enviar requisição para crew %s: %s", self.name, str(e))
            raise

class AgentDecisionEngine(models.Model):
    _inherit = 'odoo.integration.agent'
    
    use_decision_engine = fields.Boolean(string="Usar Motor de Decisão", default=True, tracking=True)
    
    def _analyze_command(self, command, context):
        """
        Analisa um comando para determinar intenção e entidades.
        Sobrescreve o método original para usar o motor de decisão.
        """
        # Conecta ao MCP-Crew para processamento de linguagem natural
        mcp_crew = self.env['odoo.integration.connector'].search([
            ('connector_type', '=', 'mcp_crew'), 
            ('active', '=', True)
        ], limit=1)
        
        if not mcp_crew:
            raise ValidationError(_("Nenhum conector MCP-Crew ativo encontrado"))
        
        # Se o motor de decisão estiver ativado, usa-o para determinar a crew
        if self.use_decision_engine and mcp_crew.use_decision_engine:
            try:
                # Usa o motor de decisão para determinar a crew mais adequada
                crew, decision_data = mcp_crew.make_decision(command, context)
                
                # Registra a decisão
                self._log_decision(command, crew, decision_data)
                
                # Envia comando para a crew selecionada
                result = crew.send_request({
                    'action': 'analyze_command',
                    'command': command,
                    'context': context,
                })
                
                return result.get('intent'), result.get('entities', {})
            except Exception as e:
                _logger.error("Erro ao usar motor de decisão: %s. Usando método padrão.", str(e))
                # Em caso de erro, usa o método padrão
        
        # Método padrão (sem motor de decisão)
        result = mcp_crew.send_request({
            'action': 'analyze_command',
            'command': command,
            'context': context,
        })
        
        return result.get('intent'), result.get('entities', {})
    
    def _log_decision(self, command, crew, decision_data):
        """
        Registra uma decisão do motor de decisão.
        """
        self.env['odoo.integration.decision.log'].create({
            'agent_id': self.id,
            'user_id': self.env.user.id,
            'command': command,
            'crew_id': crew.id,
            'decision_method': decision_data.get('method', 'unknown'),
            'decision_data': json.dumps(decision_data),
        })

class DecisionLog(models.Model):
    _name = 'odoo.integration.decision.log'
    _description = 'Log de Decisões'
    _order = 'create_date desc'
    
    agent_id = fields.Many2one('odoo.integration.agent', string='Agente', required=True)
    user_id = fields.Many2one('res.users', string='Usuário', required=True)
    command = fields.Text(string='Comando', required=True)
    crew_id = fields.Many2one('odoo.integration.crew', string='Crew Selecionada', required=True)
    decision_method = fields.Char(string='Método de Decisão')
    decision_data = fields.Text(string='Dados da Decisão')
    
    create_date = fields.Datetime(string='Data de Criação', readonly=True)
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.create_date.strftime('%Y-%m-%d %H:%M:%S')} - {record.crew_id.name}"
            result.append((record.id, name))
        return result
