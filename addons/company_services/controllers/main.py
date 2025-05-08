# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class CompanyServicesController(http.Controller):
    
    @http.route('/company-services/webhook', type='json', auth='public', csrf=False)
    def webhook(self, **kwargs):
        """
        Webhook para receber notificações do serviço de configuração.
        
        Este endpoint permite que o serviço de configuração notifique o Odoo
        sobre alterações nas configurações.
        """
        try:
            # Obter dados da requisição
            data = request.jsonrequest
            
            # Verificar token de segurança
            security_token = request.httprequest.headers.get('X-Security-Token')
            if not security_token:
                return {'success': False, 'error': 'Token de segurança não fornecido'}
            
            # Verificar se o token é válido
            IrConfigParam = request.env['ir.config_parameter'].sudo()
            stored_token = IrConfigParam.get_param('company_services.security_token', '')
            
            if not stored_token or security_token != stored_token:
                return {'success': False, 'error': 'Token de segurança inválido'}
            
            # Processar a notificação
            account_id = data.get('account_id')
            event_type = data.get('event_type')
            
            if not account_id or not event_type:
                return {'success': False, 'error': 'Dados incompletos'}
            
            # Verificar se o account_id corresponde ao configurado
            configured_account_id = IrConfigParam.get_param('company_services.account_id', '')
            if account_id != configured_account_id:
                return {'success': False, 'error': 'ID da conta não corresponde'}
            
            # Processar diferentes tipos de eventos
            if event_type == 'config_updated':
                # Atualizar status de sincronização
                company_service = request.env['company.service'].sudo().search([], limit=1)
                if company_service:
                    company_service.write({
                        'sync_status': 'synced',
                        'last_sync': fields.Datetime.now(),
                        'error_message': False
                    })
                
                return {'success': True, 'message': 'Notificação processada com sucesso'}
            else:
                return {'success': False, 'error': f'Tipo de evento desconhecido: {event_type}'}
            
        except Exception as e:
            _logger.error(f"Erro ao processar webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
