# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class CompanyService(models.Model):
    _name = 'company.service'
    _description = 'Empresa e Serviços'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nome da Empresa', required=True, tracking=True)
    description = fields.Text('Descrição', tracking=True)

    # Status de sincronização
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Processando'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro')
    ], string='Status de Sincronização', default='not_synced', readonly=True, tracking=True)
    last_sync = fields.Datetime('Última Sincronização', readonly=True)
    error_message = fields.Text('Mensagem de Erro', readonly=True)

    # Informações da Empresa
    street = fields.Char('Endereço', tracking=True)
    street2 = fields.Char('Complemento', tracking=True)
    city = fields.Char('Cidade', tracking=True)
    state = fields.Char('Estado', tracking=True)
    zip = fields.Char('CEP', tracking=True)
    country = fields.Char('País', tracking=True)
    share_address = fields.Boolean('Compartilhar endereço com clientes', default=True, tracking=True)

    # Canais Habilitados (campos computados baseados nas configurações)
    channel_whatsapp = fields.Boolean('Canal WhatsApp', compute='_compute_enabled_channels', store=False)

    # Serviços Habilitados (campos computados baseados nas configurações)
    enable_sales = fields.Boolean('Vendas de Produtos e Serviços', compute='_compute_enabled_services', store=False)
    enable_scheduling = fields.Boolean('Agendamentos', compute='_compute_enabled_services', store=False)
    enable_delivery = fields.Boolean('Delivery', compute='_compute_enabled_services', store=False)
    enable_support = fields.Boolean('Suporte ao Cliente', compute='_compute_enabled_services', store=False)

    # Configurações de Atendimento
    greeting_message = fields.Text('Saudação Inicial', tracking=True, default='')

    # Estilo de Comunicação e Personalidade
    tone = fields.Selection([
        ('friendly', 'Amigável'),
        ('polite', 'Educado'),
        ('professional', 'Profissional'),
        ('technical', 'Técnico')
    ], string='Tom de Comunicação', default='friendly', tracking=True,
       help='Define o tom que o agente usará na comunicação')

    voice = fields.Selection([
        ('welcoming', 'Acolhedor'),
        ('energetic', 'Energético'),
        ('calm', 'Calmo'),
        ('objective', 'Objetivo')
    ], string='Voz do Agente', default='welcoming', tracking=True,
       help='Define a personalidade da voz do agente')

    formality = fields.Selection([
        ('informal', 'Informal'),
        ('moderate', 'Moderado'),
        ('formal', 'Formal')
    ], string='Nível de Formalidade', default='moderate', tracking=True,
       help='Define o nível de formalidade na comunicação')

    emoji_usage = fields.Selection([
        ('none', 'Não Usar'),
        ('minimal', 'Uso Mínimo'),
        ('moderate', 'Uso Moderado')
    ], string='Uso de Emojis', default='none', tracking=True,
       help='Define a frequência de uso de emojis pelo agente')

    # Uso do nome do cliente
    use_name_in_greeting = fields.Boolean('Chamar o cliente pelo nome na saudação inicial', default=True, tracking=True,
                                        help='Se marcado, o agente chamará o cliente pelo nome na saudação inicial')
    
    name_usage_frequency = fields.Selection([
        ('minimal', 'Mínimo'),
        ('moderate', 'Moderado'),
        ('frequent', 'Frequente')
    ], string='Frequência de uso do nome do cliente', default='moderate', tracking=True,
       help='Define com que frequência o agente usará o nome do cliente durante a conversa')

    # Horário de Funcionamento
    monday = fields.Boolean('Segunda-feira', default=True, tracking=True)
    tuesday = fields.Boolean('Terça-feira', default=True, tracking=True)
    wednesday = fields.Boolean('Quarta-feira', default=True, tracking=True)
    thursday = fields.Boolean('Quinta-feira', default=True, tracking=True)
    friday = fields.Boolean('Sexta-feira', default=True, tracking=True)
    saturday = fields.Boolean('Sábado', default=False, tracking=True)
    sunday = fields.Boolean('Domingo', default=False, tracking=True)
    
    opening_time = fields.Float('Horário de Abertura', default=8.0, tracking=True)
    closing_time = fields.Float('Horário de Fechamento', default=18.0, tracking=True)
    
    inform_business_hours = fields.Boolean('Informar horário de funcionamento', default=True, tracking=True,
                                         help='Se marcado, o agente informará o horário de funcionamento quando solicitado')

    # Promoções
    inform_promotions = fields.Boolean('Informar promoções no início da conversa', default=False, tracking=True,
                                     help='Se marcado, o agente informará sobre promoções ativas no início da conversa')

    # Site e Redes Sociais
    website_url = fields.Char('Site da Empresa', tracking=True)
    website_mention = fields.Boolean('Mencionar site ao finalizar conversa', default=False, tracking=True)
    facebook_url = fields.Char('Página do Facebook', tracking=True)
    facebook_mention = fields.Boolean('Mencionar Facebook ao finalizar conversa', default=False, tracking=True)
    instagram_url = fields.Char('Perfil do Instagram', tracking=True)
    instagram_mention = fields.Boolean('Mencionar Instagram ao finalizar conversa', default=False, tracking=True)

    # Finalização de Conversa
    farewell_message = fields.Char('Mensagem de Despedida', default='', tracking=True)
    use_farewell = fields.Boolean('Permitir ao agente informar o Site/Redes Sociais ao finalizar', default=False, tracking=True,
                                 help='Se marcado, o agente poderá mencionar o site e redes sociais da empresa ao finalizar a conversa')
    request_rating = fields.Boolean('Solicitar ao Cliente avaliação sobre o atendimento', default=False, tracking=True,
                                   help='Se marcado, o agente solicitará uma avaliação do atendimento ao finalizar a conversa')
    rating_request_message = fields.Char('Mensagem de Solicitação de Avaliação', default='', tracking=True)

    @api.depends('name')  # Dependência fictícia para garantir que seja recalculado
    def _compute_enabled_channels(self):
        """Calcula os canais habilitados com base nas configurações do sistema."""
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        for record in self:
            record.channel_whatsapp = IrConfigParam.get_param('company_services.channel_whatsapp', 'True').lower() == 'true'

    @api.depends('name')  # Dependência fictícia para garantir que seja recalculado
    def _compute_enabled_services(self):
        """Calcula os serviços habilitados com base nas configurações do sistema."""
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        for record in self:
            record.enable_sales = IrConfigParam.get_param('company_services.enable_sales', 'False').lower() == 'true'
            record.enable_scheduling = IrConfigParam.get_param('company_services.enable_scheduling', 'False').lower() == 'true'
            record.enable_delivery = IrConfigParam.get_param('company_services.enable_delivery', 'False').lower() == 'true'
            record.enable_support = IrConfigParam.get_param('company_services.enable_support', 'False').lower() == 'true'

    @api.onchange('use_farewell')
    def _onchange_use_farewell(self):
        """Atualiza os campos de menção de redes sociais com base no campo use_farewell."""
        if self.website_url:
            self.website_mention = self.use_farewell
        if self.facebook_url:
            self.facebook_mention = self.use_farewell
        if self.instagram_url:
            self.instagram_mention = self.use_farewell

    @api.onchange('website_url', 'facebook_url', 'instagram_url')
    def _onchange_social_urls(self):
        """Atualiza os campos de menção quando os URLs são alterados."""
        if self.use_farewell:
            self.website_mention = bool(self.website_url)
            self.facebook_mention = bool(self.facebook_url)
            self.instagram_mention = bool(self.instagram_url)

    @api.model
    def create(self, vals):
        """Sobrescreve o método create para garantir que só exista um registro."""
        if self.search_count([]) >= 1:
            raise ValidationError(_("Só é permitido um registro de Empresa e Serviços."))
        return super(CompanyService, self).create(vals)

    def action_sync_to_config_service(self):
        """Sincroniza os dados com o serviço de configuração."""
        self.ensure_one()

        try:
            # Atualizar status
            self.write({
                'sync_status': 'syncing',
                'error_message': False
            })

            # Obter o account_id e token da empresa
            IrConfigParam = self.env['ir.config_parameter'].sudo()
            account_id = IrConfigParam.get_param('company_services.account_id', False)
            security_token = IrConfigParam.get_param('company_services.security_token', False)

            if not account_id:
                raise ValidationError(_("ID da Conta não configurado. Configure nas Configurações do módulo."))

            if not security_token:
                raise ValidationError(_("Token de Segurança não configurado. Configure nas Configurações do módulo."))

            # Atualizar status para sucesso (em um cenário real, isso seria feito após a sincronização bem-sucedida)
            self.write({
                'sync_status': 'synced',
                'last_sync': fields.Datetime.now(),
                'error_message': False
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sincronização Concluída'),
                    'message': _('Os dados foram sincronizados com sucesso.'),
                    'sticky': False,
                    'type': 'success',
                }
            }

        except Exception as e:
            # Atualizar status para erro
            self.write({
                'sync_status': 'error',
                'error_message': str(e)
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro na Sincronização'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }
