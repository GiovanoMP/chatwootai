# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class BusinessSchedulingRule(models.Model):
    _name = 'business.scheduling.rule'
    _description = 'Regra de Agendamento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char(string='Nome da Regra', required=True, tracking=True)
    description = fields.Text(string='Descrição', tracking=True)
    business_rule_id = fields.Many2one('business.rules', string='Regra de Negócio', required=True, ondelete='cascade')

    sequence = fields.Integer(string='Ordem de Exibição', default=10,
                              help='Controla a ordem em que as regras aparecem na lista (números menores aparecem primeiro)',
                              tracking=True)

    service_type = fields.Selection([
        ('consultation', 'Consulta'),
        ('service', 'Serviço'),
        ('class', 'Aula'),
        ('event', 'Evento'),
        ('other', 'Outro')
    ], string='Tipo de Serviço', default='consultation', required=True, tracking=True)
    
    service_type_other = fields.Char(string='Outro Tipo de Serviço', tracking=True)
    
    # Duração e intervalos
    duration = fields.Float(string='Duração (horas)', default=1.0, required=True, tracking=True)
    min_interval = fields.Float(string='Intervalo Mínimo (horas)', default=0.0, tracking=True,
                               help='Intervalo mínimo entre agendamentos')
    min_advance_time = fields.Integer(string='Antecedência Mínima (horas)', default=24, tracking=True,
                                     help='Antecedência mínima para agendamento')
    max_advance_time = fields.Integer(string='Antecedência Máxima (dias)', default=30, tracking=True,
                                     help='Antecedência máxima para agendamento')
    
    # Dias disponíveis
    monday_available = fields.Boolean(string='Segunda-feira', default=True, tracking=True)
    tuesday_available = fields.Boolean(string='Terça-feira', default=True, tracking=True)
    wednesday_available = fields.Boolean(string='Quarta-feira', default=True, tracking=True)
    thursday_available = fields.Boolean(string='Quinta-feira', default=True, tracking=True)
    friday_available = fields.Boolean(string='Sexta-feira', default=True, tracking=True)
    saturday_available = fields.Boolean(string='Sábado', default=False, tracking=True)
    sunday_available = fields.Boolean(string='Domingo', default=False, tracking=True)
    
    # Horários (Segunda a Sexta)
    morning_start = fields.Float(string='Início da Manhã', default=8.0, tracking=True)
    morning_end = fields.Float(string='Fim da Manhã', default=12.0, tracking=True)
    has_lunch_break = fields.Boolean(string='Intervalo para Almoço', default=True, tracking=True)
    afternoon_start = fields.Float(string='Início da Tarde', default=14.0, tracking=True)
    afternoon_end = fields.Float(string='Fim da Tarde', default=18.0, tracking=True)
    
    # Horários especiais (Sábado)
    saturday_morning_start = fields.Float(string='Início da Manhã (Sábado)', default=9.0, tracking=True)
    saturday_morning_end = fields.Float(string='Fim da Manhã (Sábado)', default=13.0, tracking=True)
    saturday_has_afternoon = fields.Boolean(string='Atendimento à Tarde (Sábado)', default=False, tracking=True)
    saturday_afternoon_start = fields.Float(string='Início da Tarde (Sábado)', default=14.0, tracking=True)
    saturday_afternoon_end = fields.Float(string='Fim da Tarde (Sábado)', default=17.0, tracking=True)
    
    # Horários especiais (Domingo)
    sunday_morning_start = fields.Float(string='Início da Manhã (Domingo)', default=9.0, tracking=True)
    sunday_morning_end = fields.Float(string='Fim da Manhã (Domingo)', default=13.0, tracking=True)
    sunday_has_afternoon = fields.Boolean(string='Atendimento à Tarde (Domingo)', default=False, tracking=True)
    sunday_afternoon_start = fields.Float(string='Início da Tarde (Domingo)', default=14.0, tracking=True)
    sunday_afternoon_end = fields.Float(string='Fim da Tarde (Domingo)', default=17.0, tracking=True)
    
    # Políticas
    cancellation_policy = fields.Text(string='Política de Cancelamento', tracking=True)
    rescheduling_policy = fields.Text(string='Política de Reagendamento', tracking=True)
    required_information = fields.Text(string='Informações Necessárias', tracking=True,
                                      help='Informações que o cliente precisa fornecer ao agendar')
    confirmation_instructions = fields.Text(string='Instruções de Confirmação', tracking=True,
                                          help='Instruções enviadas ao cliente após a confirmação do agendamento')
    
    active = fields.Boolean(default=True, string='Ativo', tracking=True)
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, esta regra será incluída no sistema de IA',
                                  tracking=True)

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização da regra principal"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'description', 'service_type', 'service_type_other', 
            'duration', 'min_interval', 'min_advance_time', 'max_advance_time',
            'monday_available', 'tuesday_available', 'wednesday_available', 
            'thursday_available', 'friday_available', 'saturday_available', 'sunday_available',
            'morning_start', 'morning_end', 'has_lunch_break', 'afternoon_start', 'afternoon_end',
            'saturday_morning_start', 'saturday_morning_end', 'saturday_has_afternoon', 
            'saturday_afternoon_start', 'saturday_afternoon_end',
            'sunday_morning_start', 'sunday_morning_end', 'sunday_has_afternoon', 
            'sunday_afternoon_start', 'sunday_afternoon_end',
            'cancellation_policy', 'rescheduling_policy', 'required_information', 'confirmation_instructions',
            'active', 'visible_in_ai'
        ]

        result = super(BusinessSchedulingRule, self).write(vals)

        # Verificar se algum campo relevante foi alterado
        if any(field in vals for field in sync_fields):
            # Atualizar a data da última sincronização da regra principal
            for record in self:
                if record.business_rule_id:
                    record.business_rule_id.write({
                        'last_sync_date': False,
                        'sync_status': 'not_synced'
                    })

        return result

    def toggle_active(self):
        """Alternar o status ativo/inativo da regra"""
        for record in self:
            record.active = not record.active
