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

    # Horários disponíveis para agendamento
    monday_available = fields.Boolean(string='Segunda-feira', default=True, tracking=True)
    tuesday_available = fields.Boolean(string='Terça-feira', default=True, tracking=True)
    wednesday_available = fields.Boolean(string='Quarta-feira', default=True, tracking=True)
    thursday_available = fields.Boolean(string='Quinta-feira', default=True, tracking=True)
    friday_available = fields.Boolean(string='Sexta-feira', default=True, tracking=True)
    saturday_available = fields.Boolean(string='Sábado', default=False, tracking=True)
    sunday_available = fields.Boolean(string='Domingo', default=False, tracking=True)

    # Horários para dias de semana (segunda a sexta)
    morning_start = fields.Float(string='Horário de Início', default=8.0, tracking=True,
                                help='Horário de início do atendimento')
    morning_end = fields.Float(string='Fim Manhã', default=12.0, tracking=True,
                              help='Horário de término do atendimento pela manhã')
    afternoon_start = fields.Float(string='Início Tarde', default=14.0, tracking=True,
                                  help='Horário de início do atendimento à tarde')
    afternoon_end = fields.Float(string='Horário de Término', default=18.0, tracking=True,
                                help='Horário de término do atendimento')

    # Intervalo de almoço
    has_lunch_break = fields.Boolean(string='Possui Intervalo', default=True, tracking=True)

    # Horários para sábado
    saturday_morning_start = fields.Float(string='Início Manhã (Sábado)', default=8.0, tracking=True,
                                         help='Horário de início do atendimento no sábado pela manhã')
    saturday_morning_end = fields.Float(string='Fim Manhã (Sábado)', default=12.0, tracking=True,
                                       help='Horário de término do atendimento no sábado pela manhã')
    saturday_afternoon_start = fields.Float(string='Início Tarde (Sábado)', default=0.0, tracking=True,
                                           help='Horário de início do atendimento no sábado à tarde (0 = sem atendimento)')
    saturday_afternoon_end = fields.Float(string='Fim Tarde (Sábado)', default=0.0, tracking=True,
                                         help='Horário de término do atendimento no sábado à tarde (0 = sem atendimento)')

    # Horários para domingo
    sunday_morning_start = fields.Float(string='Início Manhã (Domingo)', default=0.0, tracking=True,
                                       help='Horário de início do atendimento no domingo pela manhã (0 = sem atendimento)')
    sunday_morning_end = fields.Float(string='Fim Manhã (Domingo)', default=0.0, tracking=True,
                                     help='Horário de término do atendimento no domingo pela manhã (0 = sem atendimento)')
    sunday_afternoon_start = fields.Float(string='Início Tarde (Domingo)', default=0.0, tracking=True,
                                         help='Horário de início do atendimento no domingo à tarde (0 = sem atendimento)')
    sunday_afternoon_end = fields.Float(string='Fim Tarde (Domingo)', default=0.0, tracking=True,
                                       help='Horário de término do atendimento no domingo à tarde (0 = sem atendimento)')

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

    # Campos para rastreamento
    create_date = fields.Datetime(string='Data de Criação', readonly=True)
    create_uid = fields.Many2one('res.users', string='Criado por', readonly=True)
    write_date = fields.Datetime(string='Última Atualização', readonly=True)
    write_uid = fields.Many2one('res.users', string='Atualizado por', readonly=True)

    # Status de sincronização com o sistema de IA
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro na Sincronização')
    ], string='Status de Sincronização', default='not_synced', readonly=True)

    @api.onchange('service_type')
    def _onchange_service_type(self):
        """Limpar o campo service_type_other quando o tipo de serviço não for 'other'"""
        if self.service_type != 'other':
            self.service_type_other = False

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
            'saturday_afternoon_start', 'saturday_afternoon_end',
            'sunday_morning_start', 'sunday_morning_end',
            'sunday_afternoon_start', 'sunday_afternoon_end',
            'cancellation_policy', 'rescheduling_policy',
            'required_information', 'confirmation_instructions', 'active'
        ]

        # Verificar se algum campo relevante foi alterado
        if any(field in vals for field in sync_fields):
            # Se o status atual é 'synced', mudar para 'not_synced'
            if self.sync_status == 'synced':
                vals['sync_status'] = 'not_synced'

        return super(BusinessSchedulingRule, self).write(vals)

    def toggle_active(self):
        """Alternar o status ativo/inativo da regra"""
        for record in self:
            record.active = not record.active

    def action_sync_rule(self):
        """Sincronizar esta regra específica com o sistema de IA"""
        self.ensure_one()

        # Chamar o método de sincronização da regra de negócio principal
        if self.business_rule_id:
            return self.business_rule_id.action_sync_with_ai()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Aviso'),
                'message': _('Não foi possível sincronizar a regra. Regra de negócio principal não encontrada.'),
                'sticky': False,
                'type': 'warning',
            }
        }
