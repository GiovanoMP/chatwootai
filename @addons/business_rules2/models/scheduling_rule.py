# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class BusinessSchedulingRule2(models.Model):
    _name = 'business.scheduling.rule2'
    _description = 'Regra de Agendamento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char(string='Nome da Regra', required=True, tracking=True)
    description = fields.Text(string='Descrição', tracking=True)
    business_rule_id = fields.Many2one('business.rules2', string='Regra de Negócio', required=True, ondelete='cascade')

    sequence = fields.Integer(string='Ordem de Exibição', default=10,
                              help='Controla a ordem em que as regras aparecem na lista (números menores aparecem primeiro)',
                              tracking=True)

    # Tipo de serviço para agendamento
    service_type = fields.Selection([
        ('consultation', 'Consulta/Atendimento'),
        ('maintenance', 'Manutenção/Reparo'),
        ('delivery', 'Entrega'),
        ('installation', 'Instalação'),
        ('event', 'Evento'),
        ('other', 'Outro')
    ], string='Tipo de Serviço', default='consultation', required=True, tracking=True)

    service_type_other = fields.Char(string='Outro Tipo de Serviço',
                                    help='Especifique o tipo de serviço se selecionou "Outro"',
                                    tracking=True)

    # Duração do serviço
    duration = fields.Float(string='Tempo de Atendimento (horas)', default=1.0, required=True,
                           help='Quanto tempo dura cada atendimento/serviço (ex: 1.0 = 1 hora, 0.5 = 30 minutos)',
                           tracking=True)

    # Intervalo mínimo entre agendamentos
    min_interval = fields.Float(string='Intervalo Entre Atendimentos (horas)', default=0.0,
                               help='Tempo mínimo entre um atendimento e outro (ex: 0.25 = 15 minutos de preparação)',
                               tracking=True)

    # Antecedência mínima e máxima para agendamento
    min_advance_time = fields.Integer(string='Agendar com Antecedência Mínima (horas)', default=24,
                                     help='Com quantas horas de antecedência, no mínimo, o cliente deve agendar (ex: 24 = 1 dia antes)',
                                     tracking=True)
    max_advance_time = fields.Integer(string='Agendar com Antecedência Máxima (dias)', default=30,
                                     help='Com quantos dias de antecedência, no máximo, o cliente pode agendar (ex: 30 = até 1 mês antes)',
                                     tracking=True)

    # Dias disponíveis para agendamento
    monday_available = fields.Boolean(string='Segunda-feira', default=True, tracking=True)
    tuesday_available = fields.Boolean(string='Terça-feira', default=True, tracking=True)
    wednesday_available = fields.Boolean(string='Quarta-feira', default=True, tracking=True)
    thursday_available = fields.Boolean(string='Quinta-feira', default=True, tracking=True)
    friday_available = fields.Boolean(string='Sexta-feira', default=True, tracking=True)
    saturday_available = fields.Boolean(string='Sábado', default=False, tracking=True)
    sunday_available = fields.Boolean(string='Domingo', default=False, tracking=True)

    # Horários disponíveis
    morning_start = fields.Float(string='Início da Manhã', default=8.0, tracking=True)
    morning_end = fields.Float(string='Fim da Manhã', default=12.0, tracking=True)
    afternoon_start = fields.Float(string='Início da Tarde', default=13.0, tracking=True)
    afternoon_end = fields.Float(string='Fim da Tarde', default=18.0, tracking=True)
    has_lunch_break = fields.Boolean(string='Intervalo para Almoço', default=True, tracking=True)

    # Horários especiais para sábado e domingo
    saturday_morning_start = fields.Float(string='Início da Manhã (Sábado)', default=8.0, tracking=True)
    saturday_morning_end = fields.Float(string='Fim da Manhã (Sábado)', default=12.0, tracking=True)
    saturday_afternoon_start = fields.Float(string='Início da Tarde (Sábado)', default=0.0, tracking=True)
    saturday_afternoon_end = fields.Float(string='Fim da Tarde (Sábado)', default=0.0, tracking=True)
    saturday_has_afternoon = fields.Boolean(string='Atendimento à Tarde (Sábado)', default=False, tracking=True)

    sunday_morning_start = fields.Float(string='Início da Manhã (Domingo)', default=8.0, tracking=True)
    sunday_morning_end = fields.Float(string='Fim da Manhã (Domingo)', default=12.0, tracking=True)
    sunday_afternoon_start = fields.Float(string='Início da Tarde (Domingo)', default=0.0, tracking=True)
    sunday_afternoon_end = fields.Float(string='Fim da Tarde (Domingo)', default=0.0, tracking=True)
    sunday_has_afternoon = fields.Boolean(string='Atendimento à Tarde (Domingo)', default=False, tracking=True)

    # Informações adicionais
    cancellation_policy = fields.Text(string='Política de Cancelamento',
                                     help='Descreva a política de cancelamento para agendamentos')

    rescheduling_policy = fields.Text(string='Política de Reagendamento',
                                     help='Descreva a política de reagendamento')

    required_information = fields.Text(string='Informações Necessárias',
                                      help='Informações que o cliente precisa fornecer ao agendar')

    confirmation_instructions = fields.Text(string='Instruções de Confirmação',
                                          help='Instruções enviadas ao cliente após confirmação do agendamento')

    active = fields.Boolean(default=True, string='Ativo')
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, esta regra será incluída no sistema de IA')

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'description', 'service_type', 'service_type_other', 'duration',
            'min_interval', 'min_advance_time', 'max_advance_time',
            'monday_available', 'tuesday_available', 'wednesday_available',
            'thursday_available', 'friday_available', 'saturday_available', 'sunday_available',
            'morning_start', 'morning_end', 'afternoon_start', 'afternoon_end',
            'has_lunch_break', 'saturday_morning_start', 'saturday_morning_end',
            'saturday_afternoon_start', 'saturday_afternoon_end', 'saturday_has_afternoon',
            'sunday_morning_start', 'sunday_morning_end', 'sunday_afternoon_start',
            'sunday_afternoon_end', 'sunday_has_afternoon', 'cancellation_policy',
            'rescheduling_policy', 'required_information', 'confirmation_instructions',
            'active', 'visible_in_ai'
        ]

        result = super(BusinessSchedulingRule2, self).write(vals)

        # Verificar se algum campo relevante foi alterado
        if any(field in vals for field in sync_fields):
            # Atualizar a data da última sincronização da regra principal
            for record in self:
                if record.business_rule_id:
                    record.business_rule_id.write({'last_sync_date': False})

        return result

    def toggle_active(self):
        """Alternar o status ativo/inativo da regra"""
        for record in self:
            record.active = not record.active
