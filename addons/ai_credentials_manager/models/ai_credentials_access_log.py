# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class AICredentialsAccessLog(models.Model):
    _name = 'ai.credentials.access.log'
    _description = 'Log de Acesso às Credenciais'
    _order = 'access_time DESC'

    credential_id = fields.Many2one('ai.system.credentials', string='Credencial',
                                   required=True, ondelete='cascade')
    access_time = fields.Datetime('Data/Hora do Acesso', required=True, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Usuário', default=lambda self: self.env.user.id)
    ip_address = fields.Char('Endereço IP', help="Endereço IP de onde o acesso foi realizado")
    operation = fields.Selection([
        ('read', 'Leitura'),
        ('create', 'Criação'),
        ('write', 'Modificação'),
        ('unlink', 'Exclusão'),
        ('test_connection', 'Teste de Conexão'),
        ('get_credentials', 'Obtenção de Credenciais'),
        ('sync_to_webhook', 'Sincronização com Webhook'),
        ('sync_to_yaml', 'Sincronização com YAML'),
    ], string='Operação', default='read')
    success = fields.Boolean('Sucesso', default=True)
    error_message = fields.Text('Mensagem de Erro')

    # Apenas administradores podem acessar os logs
    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        if not self.env.user.has_group('base.group_system'):
            if raise_exception:
                raise AccessError(_("Apenas administradores podem acessar os logs de credenciais"))
            return False
        return super(AICredentialsAccessLog, self).check_access_rights(operation, raise_exception)
