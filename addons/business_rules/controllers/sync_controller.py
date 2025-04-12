# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class BusinessRulesSyncController(http.Controller):
    
    @http.route('/business_rules/sync', type='json', auth='user')
    def sync_business_rules(self, business_rule_id):
        """Endpoint para sincronizar regras de negócio com o sistema de IA"""
        try:
            business_rule = request.env['business.rules'].browse(int(business_rule_id))
            if not business_rule.exists():
                return {'success': False, 'error': _('Regra de negócio não encontrada')}
            
            # Coletar todas as regras ativas
            rules_data = self._prepare_rules_data(business_rule)
            
            # Aqui implementaríamos a chamada para o sistema de IA
            # Por enquanto, apenas simulamos a sincronização
            
            # Atualizar o status de sincronização
            business_rule.write({
                'last_sync_date': fields.Datetime.now(),
                'sync_status': 'synced'
            })
            
            return {
                'success': True,
                'message': _('Regras sincronizadas com sucesso'),
                'rules_count': len(rules_data['permanent_rules']) + len(rules_data['temporary_rules'])
            }
            
        except Exception as e:
            _logger.error("Erro ao sincronizar regras de negócio: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    def _prepare_rules_data(self, business_rule):
        """Preparar dados das regras para envio ao sistema de IA"""
        # Informações básicas da empresa
        basic_info = {
            'company_name': business_rule.name,
            'website': business_rule.website,
            'description': business_rule.description,
            'company_values': business_rule.company_values,
            'business_model': business_rule.business_model,
            'greeting_message': business_rule.greeting_message,
            'communication_style': business_rule.communication_style,
            'emoji_usage': business_rule.emoji_usage,
            'business_hours': {
                'start': business_rule.business_hours_start,
                'end': business_rule.business_hours_end,
                'days': business_rule.business_days
            },
            'response_time': business_rule.response_time
        }
        
        # Regras permanentes ativas
        permanent_rules = []
        for rule in business_rule.rule_ids.filtered(lambda r: r.active):
            permanent_rules.append({
                'name': rule.name,
                'description': rule.description,
                'priority': rule.priority,
                'type': rule.rule_type
            })
        
        # Regras temporárias ativas e dentro do período de validade
        now = fields.Datetime.now()
        temporary_rules = []
        for rule in business_rule.temporary_rule_ids.filtered(
            lambda r: r.active and 
            (not r.date_start or r.date_start <= now) and 
            (not r.date_end or r.date_end >= now)
        ):
            temporary_rules.append({
                'name': rule.name,
                'description': rule.description,
                'priority': rule.priority,
                'type': rule.rule_type,
                'date_start': fields.Datetime.to_string(rule.date_start) if rule.date_start else False,
                'date_end': fields.Datetime.to_string(rule.date_end) if rule.date_end else False
            })
        
        return {
            'basic_info': basic_info,
            'permanent_rules': permanent_rules,
            'temporary_rules': temporary_rules
        }
