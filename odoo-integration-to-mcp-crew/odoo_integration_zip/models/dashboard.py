# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class MCPDashboard(models.Model):
    _name = 'odoo.integration.dashboard'
    _description = 'Dashboard MCP'
    
    name = fields.Char(required=True)
    dashboard_type = fields.Selection([
        ('overview', 'Visão Geral'),
        ('sales', 'Vendas'),
        ('inventory', 'Estoque'),
        ('customer', 'Cliente'),
        ('custom', 'Personalizado'),
    ], required=True)
    
    connector_ids = fields.Many2many('odoo.integration.connector', string='Conectores')
    config_data = fields.Text(string="Configurações Adicionais")
    
    # Widgets configurados
    widget_ids = fields.One2many('odoo.integration.dashboard.widget', 'dashboard_id', string="Widgets")
    
    # Relações
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)
    
    def get_dashboard_data(self):
        """
        Obtém dados para o dashboard.
        """
        self.ensure_one()
        
        result = {
            'name': self.name,
            'type': self.dashboard_type,
            'widgets': [],
        }
        
        # Coleta dados de cada widget
        for widget in self.widget_ids:
            widget_data = widget.get_widget_data()
            result['widgets'].append(widget_data)
        
        return result

class DashboardWidget(models.Model):
    _name = 'odoo.integration.dashboard.widget'
    _description = 'Widget de Dashboard'
    _order = 'sequence, id'
    
    name = fields.Char(required=True)
    dashboard_id = fields.Many2one('odoo.integration.dashboard', required=True, ondelete='cascade')
    widget_type = fields.Selection([
        ('kpi', 'KPI'),
        ('chart', 'Gráfico'),
        ('table', 'Tabela'),
        ('list', 'Lista'),
    ], required=True)
    
    sequence = fields.Integer(string="Sequência", default=10)
    size_x = fields.Integer(string="Largura", default=1)
    size_y = fields.Integer(string="Altura", default=1)
    
    # Configuração específica por tipo
    config_data = fields.Text(string="Configurações do Widget")
    
    # Fonte de dados
    data_source = fields.Selection([
        ('connector', 'Conector'),
        ('odoo', 'Odoo'),
        ('custom', 'Consulta Personalizada'),
    ], required=True)
    connector_id = fields.Many2one('odoo.integration.connector', string="Conector")
    model_id = fields.Many2one('ir.model', string="Modelo")
    query = fields.Text(string="Consulta SQL")
    
    # Atualização
    auto_refresh = fields.Boolean(string="Atualização Automática", default=False)
    refresh_interval = fields.Integer(string="Intervalo de Atualização (segundos)", default=300)
    
    def get_widget_data(self):
        """
        Obtém dados para o widget.
        """
        self.ensure_one()
        
        # Estrutura básica
        result = {
            'id': self.id,
            'name': self.name,
            'type': self.widget_type,
            'size': {
                'x': self.size_x,
                'y': self.size_y,
            },
            'config': json.loads(self.config_data or '{}'),
        }
        
        # Obtém dados conforme a fonte
        if self.data_source == 'connector':
            result['data'] = self._get_connector_data()
        elif self.data_source == 'odoo':
            result['data'] = self._get_odoo_data()
        elif self.data_source == 'custom':
            result['data'] = self._get_custom_data()
        
        return result
    
    def _get_connector_data(self):
        """
        Obtém dados do conector MCP.
        """
        if not self.connector_id:
            return {'error': 'Nenhum conector especificado'}
            
        try:
            # Implementação específica por tipo de widget
            if self.widget_type == 'kpi':
                return self._get_connector_kpi_data()
            elif self.widget_type == 'chart':
                return self._get_connector_chart_data()
            elif self.widget_type == 'table':
                return self._get_connector_table_data()
            elif self.widget_type == 'list':
                return self._get_connector_list_data()
            else:
                return {'error': f'Tipo de widget não suportado: {self.widget_type}'}
        except Exception as e:
            _logger.error("Erro ao obter dados do conector para widget %s: %s", self.name, str(e))
            return {'error': str(e)}
    
    def _get_connector_kpi_data(self):
        """
        Obtém dados KPI do conector.
        """
        config = json.loads(self.config_data or '{}')
        kpi_type = config.get('kpi_type', 'sales')
        
        # Solicita dados KPI do conector
        result = self.connector_id.send_request({
            'action': 'get_kpi',
            'kpi_type': kpi_type,
        })
        
        return result
    
    def _get_connector_chart_data(self):
        """
        Obtém dados de gráfico do conector.
        """
        config = json.loads(self.config_data or '{}')
        chart_type = config.get('chart_type', 'line')
        period = config.get('period', 'month')
        
        # Solicita dados de gráfico do conector
        result = self.connector_id.send_request({
            'action': 'get_chart_data',
            'chart_type': chart_type,
            'period': period,
        })
        
        return result
    
    def _get_connector_table_data(self):
        """
        Obtém dados de tabela do conector.
        """
        config = json.loads(self.config_data or '{}')
        table_type = config.get('table_type', 'products')
        limit = config.get('limit', 10)
        
        # Solicita dados de tabela do conector
        result = self.connector_id.send_request({
            'action': 'get_table_data',
            'table_type': table_type,
            'limit': limit,
        })
        
        return result
    
    def _get_connector_list_data(self):
        """
        Obtém dados de lista do conector.
        """
        config = json.loads(self.config_data or '{}')
        list_type = config.get('list_type', 'recent_orders')
        limit = config.get('limit', 5)
        
        # Solicita dados de lista do conector
        result = self.connector_id.send_request({
            'action': 'get_list_data',
            'list_type': list_type,
            'limit': limit,
        })
        
        return result
    
    def _get_odoo_data(self):
        """
        Obtém dados de modelos Odoo.
        """
        if not self.model_id:
            return {'error': 'Nenhum modelo especificado'}
            
        try:
            config = json.loads(self.config_data or '{}')
            domain = config.get('domain', [])
            fields = config.get('fields', [])
            limit = config.get('limit', 0)
            order = config.get('order', False)
            
            # Obtém modelo
            model_name = self.model_id.model
            
            # Executa consulta
            records = self.env[model_name].search(domain, limit=limit, order=order)
            
            # Formata resultado conforme tipo de widget
            if self.widget_type == 'kpi':
                return self._format_odoo_kpi(records, config)
            elif self.widget_type == 'chart':
                return self._format_odoo_chart(records, config)
            elif self.widget_type in ['table', 'list']:
                return self._format_odoo_table_list(records, fields)
            else:
                return {'error': f'Tipo de widget não suportado: {self.widget_type}'}
        except Exception as e:
            _logger.error("Erro ao obter dados do Odoo para widget %s: %s", self.name, str(e))
            return {'error': str(e)}
    
    def _format_odoo_kpi(self, records, config):
        """
        Formata registros Odoo como KPI.
        """
        kpi_type = config.get('kpi_type', 'count')
        
        if kpi_type == 'count':
            return {
                'value': len(records),
                'label': self.name,
                'unit': config.get('unit', ''),
            }
        elif kpi_type == 'sum':
            field = config.get('field')
            if not field:
                return {'error': 'Campo não especificado para soma'}
                
            total = sum(records.mapped(field))
            return {
                'value': total,
                'label': self.name,
                'unit': config.get('unit', ''),
            }
        elif kpi_type == 'average':
            field = config.get('field')
            if not field:
                return {'error': 'Campo não especificado para média'}
                
            values = records.mapped(field)
            avg = sum(values) / len(values) if values else 0
            return {
                'value': avg,
                'label': self.name,
                'unit': config.get('unit', ''),
            }
        else:
            return {'error': f'Tipo de KPI não suportado: {kpi_type}'}
    
    def _format_odoo_chart(self, records, config):
        """
        Formata registros Odoo como dados de gráfico.
        """
        chart_type = config.get('chart_type', 'bar')
        x_field = config.get('x_field')
        y_field = config.get('y_field')
        
        if not x_field or not y_field:
            return {'error': 'Campos X e Y não especificados para gráfico'}
            
        # Agrupa dados
        data = {}
        for record in records:
            x_value = record[x_field]
            y_value = record[y_field]
            
            if x_value in data:
                data[x_value] += y_value
            else:
                data[x_value] = y_value
        
        # Formata para gráfico
        return {
            'type': chart_type,
            'labels': list(data.keys()),
            'datasets': [{
                'label': self.name,
                'data': list(data.values()),
            }],
        }
    
    def _format_odoo_table_list(self, records, fields):
        """
        Formata registros Odoo como tabela ou lista.
        """
        if not fields:
            return {'error': 'Campos não especificados para tabela/lista'}
            
        # Prepara cabeçalhos
        headers = []
        for field in fields:
            field_obj = self.env['ir.model.fields'].search([
                ('model_id', '=', self.model_id.id),
                ('name', '=', field),
            ], limit=1)
            
            headers.append(field_obj.field_description if field_obj else field)
        
        # Prepara linhas
        rows = []
        for record in records:
            row = []
            for field in fields:
                row.append(record[field])
            rows.append(row)
        
        return {
            'headers': headers,
            'rows': rows,
        }
    
    def _get_custom_data(self):
        """
        Executa consulta personalizada.
        """
        if not self.query:
            return {'error': 'Nenhuma consulta especificada'}
            
        try:
            # Executa consulta SQL com segurança
            self.env.cr.execute(self.query)
            result = self.env.cr.dictfetchall()
            
            # Formata resultado conforme tipo de widget
            if self.widget_type == 'kpi':
                if not result:
                    return {'error': 'Nenhum resultado retornado pela consulta'}
                    
                # Assume que a consulta retorna um único valor
                return {
                    'value': list(result[0].values())[0],
                    'label': self.name,
                }
            elif self.widget_type == 'chart':
                # Assume formato específico para gráficos
                labels = []
                data = []
                
                for row in result:
                    if len(row) >= 2:
                        labels.append(list(row.values())[0])
                        data.append(list(row.values())[1])
                
                return {
                    'type': 'bar',  # Padrão
                    'labels': labels,
                    'datasets': [{
                        'label': self.name,
                        'data': data,
                    }],
                }
            elif self.widget_type in ['table', 'list']:
                if not result:
                    return {'headers': [], 'rows': []}
                    
                headers = list(result[0].keys())
                rows = []
                
                for row in result:
                    rows.append(list(row.values()))
                
                return {
                    'headers': headers,
                    'rows': rows,
                }
            else:
                return {'error': f'Tipo de widget não suportado: {self.widget_type}'}
        except Exception as e:
            _logger.error("Erro ao executar consulta personalizada para widget %s: %s", self.name, str(e))
            return {'error': str(e)}
