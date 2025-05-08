# -*- coding: utf-8 -*-

from odoo import models, api
import requests
import logging

_logger = logging.getLogger(__name__)

class CompanySyncService(models.AbstractModel):
    _name = 'company.sync.service'
    _description = 'Serviço de Sincronização de Empresa e Serviços'
    
    def _get_config_service_url_and_key(self):
        """Obtém a URL e a chave API do serviço de configuração."""
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        url = IrConfigParam.get_param('company_services.config_service_url', '')
        api_key = IrConfigParam.get_param('company_services.config_service_api_key', 'development-api-key')
        
        return url, api_key
    
    def sync_company_data(self, yaml_content, account_id, security_token):
        """Sincroniza dados da empresa com o serviço de configuração."""
        url, api_key = self._get_config_service_url_and_key()
        if not url:
            return {'success': False, 'error': 'URL do serviço de configuração não configurada'}
        
        # Construir o endpoint específico para company_services
        endpoint = f"{url}/company-services/{account_id}/metadata"
        
        # Preparar headers
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'X-Security-Token': security_token  # Incluir token de segurança no header
        }
        
        # Preparar payload
        payload = {
            'yaml_content': yaml_content
        }
        
        _logger.info(f"Enviando dados da empresa para o config-service: URL={endpoint}")
        
        # Fazer a requisição
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in (200, 201):
                _logger.info(f"Dados da empresa sincronizados com sucesso: {account_id}")
                return {'success': True, 'message': 'Dados sincronizados com sucesso'}
            else:
                _logger.error(f"Erro ao sincronizar dados da empresa: {response.status_code} - {response.text}")
                return {'success': False, 'error': f"Erro na API: {response.status_code} - {response.text}"}
        except Exception as e:
            _logger.error(f"Erro ao sincronizar dados da empresa: {str(e)}")
            return {'success': False, 'error': str(e)}
