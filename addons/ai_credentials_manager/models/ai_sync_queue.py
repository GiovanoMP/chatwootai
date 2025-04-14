# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json
import requests
import time
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class AISyncQueue(models.Model):
    _name = 'ai.sync.queue'
    _description = 'Fila de Sincronização com IA'
    _order = 'create_date DESC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Nome', compute='_compute_name', store=True)
    credential_id = fields.Many2one('ai.system.credentials', string='Credencial', 
                                   required=True, ondelete='cascade', tracking=True)
    module = fields.Selection([
        ('business_rules', 'Regras de Negócio'),
        ('semantic_product', 'Descrição Semântica de Produtos'),
        ('product_ai_mass_management', 'Gerenciamento em Massa de Produtos'),
        ('custom', 'Personalizado')
    ], string='Módulo de Origem', required=True, tracking=True)
    module_custom = fields.Char('Módulo Personalizado', tracking=True)
    operation = fields.Selection([
        ('sync', 'Sincronização'),
        ('generate', 'Geração'),
        ('search', 'Busca'),
        ('custom', 'Personalizada')
    ], string='Operação', required=True, tracking=True)
    operation_custom = fields.Char('Operação Personalizada', tracking=True)
    data = fields.Text('Dados', help="Dados em formato JSON", tracking=True)
    state = fields.Selection([
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('done', 'Concluído'),
        ('failed', 'Falha')
    ], string='Estado', default='pending', tracking=True)
    retry_count = fields.Integer('Tentativas', default=0, tracking=True)
    max_retries = fields.Integer('Máximo de Tentativas', default=3)
    next_retry = fields.Datetime('Próxima Tentativa')
    result = fields.Text('Resultado', readonly=True)
    error_message = fields.Text('Mensagem de Erro', readonly=True)
    
    # Campos relacionados
    account_id = fields.Char(related='credential_id.account_id', string='ID da Conta', store=True)
    
    @api.depends('module', 'module_custom', 'operation', 'operation_custom', 'create_date')
    def _compute_name(self):
        for record in self:
            module = record.module_custom if record.module == 'custom' else dict(record._fields['module'].selection).get(record.module)
            operation = record.operation_custom if record.operation == 'custom' else dict(record._fields['operation'].selection).get(record.operation)
            date = record.create_date or datetime.now()
            record.name = f"{module} - {operation} ({date.strftime('%d/%m/%Y %H:%M')})"
    
    def action_retry(self):
        """Força uma nova tentativa de processamento."""
        self.ensure_one()
        if self.state in ['failed', 'pending']:
            self.write({
                'state': 'pending',
                'next_retry': fields.Datetime.now(),
                'error_message': False
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Operação Agendada'),
                    'message': _('A operação foi agendada para processamento imediato.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Operação Inválida'),
                'message': _('Apenas operações com falha ou pendentes podem ser reagendadas.'),
                'sticky': False,
                'type': 'warning',
            }
        }
    
    def action_cancel(self):
        """Cancela uma operação pendente."""
        self.ensure_one()
        if self.state == 'pending':
            self.write({
                'state': 'failed',
                'error_message': 'Cancelado pelo usuário'
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Operação Cancelada'),
                    'message': _('A operação foi cancelada com sucesso.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Operação Inválida'),
                'message': _('Apenas operações pendentes podem ser canceladas.'),
                'sticky': False,
                'type': 'warning',
            }
        }
    
    @api.model
    def process_queue(self):
        """Processa a fila de sincronização (chamado pelo agendador)."""
        # Buscar operações pendentes com próxima tentativa no passado ou não definida
        now = fields.Datetime.now()
        pending_ops = self.search([
            ('state', '=', 'pending'),
            '|',
            ('next_retry', '<=', now),
            ('next_retry', '=', False)
        ], limit=10)
        
        for op in pending_ops:
            try:
                # Marcar como processando
                op.write({'state': 'processing'})
                self.env.cr.commit()  # Commit imediato para evitar bloqueios
                
                # Obter credenciais
                creds = op.credential_id
                if not creds or not creds.active:
                    raise UserError(_("Credenciais inválidas ou inativas"))
                
                # Obter URL do sistema de IA
                ai_url = creds.get_ai_system_url()
                if not ai_url:
                    raise UserError(_("URL do sistema de IA não configurada"))
                
                # Preparar dados
                data = json.loads(op.data) if op.data else {}
                
                # Adicionar metadados
                if 'metadata' not in data:
                    data['metadata'] = {}
                
                data['metadata'].update({
                    'account_id': creds.account_id,
                    'module': op.module_custom if op.module == 'custom' else op.module,
                    'operation': op.operation_custom if op.operation == 'custom' else op.operation,
                })
                
                # Determinar endpoint
                endpoint = f"{ai_url}/api/v1/{op.module}"
                if op.operation != 'sync':
                    endpoint += f"/{op.operation}"
                
                # Enviar requisição
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {creds.token}"
                }
                
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=data,
                    timeout=60  # Timeout de 60 segundos
                )
                
                # Verificar resposta
                if response.status_code == 200:
                    result = response.json()
                    op.write({
                        'state': 'done',
                        'result': json.dumps(result, indent=2),
                        'error_message': False
                    })
                else:
                    # Falha na requisição
                    error_msg = f"Erro HTTP {response.status_code}: {response.text}"
                    self._handle_failure(op, error_msg)
                
            except Exception as e:
                self._handle_failure(op, str(e))
    
    def _handle_failure(self, op, error_msg):
        """Trata falhas no processamento."""
        retry_count = op.retry_count + 1
        
        if retry_count <= op.max_retries:
            # Calcular próxima tentativa com backoff exponencial
            delay_minutes = 5 * (2 ** (retry_count - 1))  # 5, 10, 20, 40, ...
            next_retry = fields.Datetime.now() + timedelta(minutes=delay_minutes)
            
            op.write({
                'state': 'pending',
                'retry_count': retry_count,
                'next_retry': next_retry,
                'error_message': error_msg
            })
            _logger.warning(f"Falha no processamento da operação {op.id}. Tentativa {retry_count}/{op.max_retries}. Próxima tentativa em {delay_minutes} minutos. Erro: {error_msg}")
        else:
            # Máximo de tentativas atingido
            op.write({
                'state': 'failed',
                'error_message': f"Máximo de tentativas atingido. Último erro: {error_msg}"
            })
            _logger.error(f"Falha definitiva no processamento da operação {op.id} após {retry_count} tentativas. Erro: {error_msg}")
    
    @api.model
    def create_sync_operation(self, credential_id, module, operation, data=None):
        """Cria uma nova operação de sincronização."""
        if isinstance(credential_id, str):
            # Se for passado o account_id em vez do ID da credencial
            creds = self.env['ai.system.credentials'].search([('account_id', '=', credential_id)], limit=1)
            if not creds:
                raise UserError(_("Credencial não encontrada para account_id: %s") % credential_id)
            credential_id = creds.id
        
        # Criar operação
        values = {
            'credential_id': credential_id,
            'module': module,
            'operation': operation,
            'data': json.dumps(data) if data else '{}',
            'state': 'pending',
            'next_retry': fields.Datetime.now()
        }
        
        # Adicionar campos personalizados se necessário
        if module == 'custom':
            if not data or 'module_custom' not in data:
                raise UserError(_("Campo 'module_custom' é obrigatório para módulo personalizado"))
            values['module_custom'] = data['module_custom']
        
        if operation == 'custom':
            if not data or 'operation_custom' not in data:
                raise UserError(_("Campo 'operation_custom' é obrigatório para operação personalizada"))
            values['operation_custom'] = data['operation_custom']
        
        return self.create(values)
