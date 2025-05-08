# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class BusinessTemplate(models.Model):
    _name = 'business.template'
    _description = 'Templates de Modelo de Negócio'
    
    name = fields.Char(string='Nome do Template', required=True)
    model_type = fields.Selection([
        ('restaurant', 'Restaurante/Pizzaria'),
        ('ecommerce', 'E-commerce/Loja Virtual'),
        ('clinic', 'Clínica/Consultório'),
        ('retail', 'Loja Física'),
        ('service', 'Prestador de Serviços'),
        ('other', 'Outro')
    ], string='Tipo de Modelo', required=True)
    
    description = fields.Text(string='Descrição')
    default_greeting = fields.Text(string='Saudação Padrão')
    default_communication_style = fields.Selection([
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('friendly', 'Amigável'),
        ('technical', 'Técnico')
    ], string='Estilo de Comunicação Padrão', default='friendly')
    
    default_emoji_usage = fields.Selection([
        ('none', 'Não Usar'),
        ('moderate', 'Uso Moderado'),
        ('frequent', 'Uso Frequente')
    ], string='Uso de Emojis Padrão', default='moderate')
    
    default_business_hours_start = fields.Float(string='Horário de Início Padrão', default=8.0)
    default_business_hours_end = fields.Float(string='Horário de Término Padrão', default=18.0)
    default_business_days = fields.Char(string='Dias de Funcionamento Padrão', default='Segunda a Sexta')
    
    # Regras padrão para este modelo de negócio
    default_rule_ids = fields.One2many('business.template.rule', 'template_id', string='Regras Padrão')
    
    active = fields.Boolean(default=True, string='Ativo')
    
    def action_apply_template(self, business_rule_id):
        """Aplicar este template a uma regra de negócio específica"""
        business_rule = self.env['business.rules'].browse(business_rule_id)
        if business_rule:
            # Atualizar configurações básicas
            business_rule.write({
                'greeting_message': self.default_greeting,
                'communication_style': self.default_communication_style,
                'emoji_usage': self.default_emoji_usage,
                'business_hours_start': self.default_business_hours_start,
                'business_hours_end': self.default_business_hours_end,
                'business_days': self.default_business_days,
            })
            
            # Criar regras padrão
            for template_rule in self.default_rule_ids:
                self.env['business.rule.item'].create({
                    'business_rule_id': business_rule.id,
                    'name': template_rule.name,
                    'description': template_rule.description,
                    'priority': template_rule.priority,
                    'active': True,
                })
            
            return True
        return False

class BusinessTemplateRule(models.Model):
    _name = 'business.template.rule'
    _description = 'Regra Padrão de Template'
    _order = 'priority, id'
    
    name = fields.Char(string='Nome da Regra', required=True)
    description = fields.Text(string='Descrição', required=True)
    template_id = fields.Many2one('business.template', string='Template', required=True, ondelete='cascade')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Importante'),
        ('2', 'Crítica')
    ], string='Prioridade', default='0', required=True)
    
    active = fields.Boolean(default=True, string='Ativo')
