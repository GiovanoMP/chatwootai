# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BusinessTemplate(models.Model):
    _name = 'business.template2'
    _description = 'Template de Regras de Negócio'

    name = fields.Char(string='Nome do Template', required=True)
    description = fields.Text(string='Descrição')
    
    model_type = fields.Selection([
        ('restaurant', 'Restaurante/Pizzaria'),
        ('ecommerce', 'E-commerce/Loja Virtual'),
        ('clinic', 'Clínica/Consultório'),
        ('retail', 'Loja Física'),
        ('service', 'Prestador de Serviços'),
        ('other', 'Outro')
    ], string='Tipo de Negócio', required=True)
    
    default_greeting = fields.Text(string='Saudação Padrão')
    
    # Regras padrão para este template
    rule_ids = fields.One2many('business.template.rule2', 'template_id', string='Regras Padrão')
    
    # Regras de agendamento padrão para este template
    scheduling_rule_ids = fields.One2many('business.template.scheduling2', 'template_id', string='Regras de Agendamento Padrão')
    
    active = fields.Boolean(default=True, string='Ativo')
    
    def apply_template(self, business_rule_id):
        """Aplicar este template a uma regra de negócio"""
        self.ensure_one()
        
        business_rule = self.env['business.rules2'].browse(business_rule_id)
        if not business_rule.exists():
            return False
        
        # Aplicar regras padrão
        for template_rule in self.rule_ids:
            self.env['business.rule.item2'].create({
                'name': template_rule.name,
                'description': template_rule.description,
                'rule_type': template_rule.rule_type,
                'business_rule_id': business_rule.id,
                'active': True,
                'visible_in_ai': True
            })
        
        # Aplicar regras de agendamento padrão
        for template_scheduling in self.scheduling_rule_ids:
            self.env['business.scheduling.rule2'].create({
                'name': template_scheduling.name,
                'description': template_scheduling.description,
                'service_type': template_scheduling.service_type,
                'duration': template_scheduling.duration,
                'business_rule_id': business_rule.id,
                'active': True,
                'visible_in_ai': True
            })
        
        return True

class BusinessTemplateRule2(models.Model):
    _name = 'business.template.rule2'
    _description = 'Regra de Template'
    
    name = fields.Char(string='Nome da Regra', required=True)
    description = fields.Text(string='Descrição', required=True)
    template_id = fields.Many2one('business.template2', string='Template', required=True, ondelete='cascade')
    
    rule_type = fields.Selection([
        ('general', 'Geral'),
        ('product', 'Produto'),
        ('service', 'Serviço'),
        ('delivery', 'Entrega'),
        ('payment', 'Pagamento'),
        ('return', 'Devolução'),
        ('other', 'Outro')
    ], string='Tipo de Regra', default='general', required=True)

class BusinessTemplateScheduling2(models.Model):
    _name = 'business.template.scheduling2'
    _description = 'Regra de Agendamento de Template'
    
    name = fields.Char(string='Nome da Regra', required=True)
    description = fields.Text(string='Descrição')
    template_id = fields.Many2one('business.template2', string='Template', required=True, ondelete='cascade')
    
    service_type = fields.Selection([
        ('consultation', 'Consulta/Atendimento'),
        ('maintenance', 'Manutenção/Reparo'),
        ('delivery', 'Entrega'),
        ('installation', 'Instalação'),
        ('event', 'Evento'),
        ('other', 'Outro')
    ], string='Tipo de Serviço', default='consultation', required=True)
    
    duration = fields.Float(string='Tempo de Atendimento (horas)', default=1.0, required=True)
