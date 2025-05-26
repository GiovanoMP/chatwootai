# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import yaml

_logger = logging.getLogger(__name__)

class CompanyService(models.Model):
    _name = 'company.service'
    _description = 'Empresa e Serviços'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', string='Empresa', required=True, 
                                default=lambda self: self.env.company,
                                tracking=True)
    name = fields.Char('Nome da Empresa', compute='_compute_company_data', 
                      store=True, readonly=False, tracking=True)
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

    # Informações da Empresa (computadas a partir de res.company)
    street = fields.Char('Rua', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    street2 = fields.Char('Complemento', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    city = fields.Char('Cidade', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    state = fields.Char('Estado', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    zip = fields.Char('CEP', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    country = fields.Char('País', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    
    # Informações de contato (computadas a partir de res.company)
    phone = fields.Char('Telefone', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    mobile = fields.Char('Celular', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    email = fields.Char('E-mail', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    website = fields.Char('Website', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    
    # Informações fiscais (computadas a partir de res.company)
    vat = fields.Char('CNPJ/CPF', compute='_compute_company_data', store=True, readonly=False, tracking=True)
    
    # Redes Sociais
    facebook_url = fields.Char('Página do Facebook', tracking=True)
    instagram_url = fields.Char('Perfil do Instagram', tracking=True)
    twitter_url = fields.Char('Perfil do Twitter', tracking=True)
    linkedin_url = fields.Char('Perfil do LinkedIn', tracking=True)
    youtube_url = fields.Char('Canal do YouTube', tracking=True)
    
    # Marketplaces
    mercadolivre_url = fields.Char('Loja no Mercado Livre', tracking=True)
    amazon_url = fields.Char('Loja na Amazon', tracking=True)
    shopee_url = fields.Char('Loja na Shopee', tracking=True)
    
    @api.depends('company_id', 'company_id.partner_id')
    def _compute_company_data(self):
        for record in self:
            if record.company_id:
                # Dados básicos
                record.name = record.company_id.name
                
                # Endereço
                record.street = record.company_id.street
                record.street2 = record.company_id.street2
                record.city = record.company_id.city
                record.state = record.company_id.state_id.name if record.company_id.state_id else False
                record.zip = record.company_id.zip
                record.country = record.company_id.country_id.name if record.company_id.country_id else False
                
                # Contato
                record.phone = record.company_id.phone
                record.mobile = record.company_id.mobile
                record.email = record.company_id.email
                record.website = record.company_id.website
                
                # Informações fiscais
                record.vat = record.company_id.vat
    
    def action_update_company_data(self):
        """Atualiza manualmente os dados da empresa a partir do cadastro na Sprintia."""
        self.ensure_one()
        # Força a recomputação dos campos computados
        self.invalidate_recordset([
            # Dados básicos
            'name', 
            # Endereço
            'street', 'street2', 'city', 'state', 'zip', 'country',
            # Contato
            'phone', 'mobile', 'email', 'website',
            # Informações fiscais
            'vat'
        ])
        self._compute_company_data()
        
        # Mensagem de sucesso
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sucesso!',
                'message': 'Dados da empresa atualizados com sucesso.',
                'type': 'success',
                'sticky': False,
            }
        }
        
    def action_save_company_info(self):
        """Salva explicitamente as informações da empresa no registro atual."""
        self.ensure_one()
        # Força a atualização dos dados da empresa
        self._compute_company_data()
        # Salva o registro explicitamente
        self.write({
            'name': self.name,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'country': self.country,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': self.email,
            'website': self.website,
            'vat': self.vat
        })
        
        # Mensagem de sucesso
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Informações Salvas!',
                'message': 'As informações da empresa foram salvas com sucesso.',
                'type': 'success',
                'sticky': False,
            }
        }

    # Serviços Habilitados (campos computados baseados nas configurações)
    enable_sales = fields.Boolean('Vendas de Produtos e Serviços', compute='_compute_enabled_services', store=False)
    enable_scheduling = fields.Boolean('Agendamentos', compute='_compute_enabled_services', store=False)
    enable_delivery = fields.Boolean('Delivery', compute='_compute_enabled_services', store=False)
    enable_support = fields.Boolean('Suporte ao Cliente', compute='_compute_enabled_services', store=False)

    # Descrições dos serviços (não são mais necessárias como campos, pois usamos texto estático na view)

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

    # Horário de Funcionamento
    start_time = fields.Char('Horário de Início', default='09:00', tracking=True)
    end_time = fields.Char('Horário de Término', default='18:00', tracking=True)
    has_lunch_break = fields.Boolean('Possui Intervalo', default=False, tracking=True)
    lunch_break_start = fields.Char('Início do Intervalo', default='12:00', tracking=True)
    lunch_break_end = fields.Char('Fim do Intervalo', default='13:00', tracking=True)

    # Dias de Funcionamento
    monday = fields.Boolean('Segunda-feira', default=True, tracking=True)
    tuesday = fields.Boolean('Terça-feira', default=True, tracking=True)
    wednesday = fields.Boolean('Quarta-feira', default=True, tracking=True)
    thursday = fields.Boolean('Quinta-feira', default=True, tracking=True)
    friday = fields.Boolean('Sexta-feira', default=True, tracking=True)
    saturday = fields.Boolean('Sábado', default=False, tracking=True)
    saturday_start_time = fields.Char('Início Sábado', default='08:00', tracking=True)
    saturday_end_time = fields.Char('Término Sábado', default='12:00', tracking=True)
    sunday = fields.Boolean('Domingo', default=False, tracking=True)
    sunday_start_time = fields.Char('Início Domingo', default='08:00', tracking=True)
    sunday_end_time = fields.Char('Término Domingo', default='12:00', tracking=True)

    # Menções de Canais Digitais
    website_mention = fields.Boolean('Mencionar site ao finalizar conversa', default=False, tracking=True)
    facebook_mention = fields.Boolean('Mencionar Facebook ao finalizar conversa', default=False, tracking=True)
    instagram_mention = fields.Boolean('Mencionar Instagram ao finalizar conversa', default=False, tracking=True)

    # Finalização de Conversa
    farewell_message = fields.Char('Mensagem de Despedida', default='', tracking=True)
    use_farewell = fields.Boolean('Permitir ao agente informar o Site/Redes Sociais ao finalizar', default=False, tracking=True,
                                 help='Se marcado, o agente poderá mencionar o site e redes sociais da empresa ao finalizar a conversa')
    request_rating = fields.Boolean('Solicitar ao Cliente avaliação sobre o atendimento', default=False, tracking=True,
                                   help='Se marcado, o agente solicitará uma avaliação do atendimento ao finalizar a conversa')
    rating_request_message = fields.Char('Mensagem de Solicitação de Avaliação', default='', tracking=True)
    
    # Opções de Avaliação
    rating_type = fields.Selection([
        ('numeric_1_10', 'Nota de 1 a 10'),
        ('numeric_1_5', 'Nota de 1 a 5'),
        ('stars', 'Estrelas (1 a 5)'),
        ('emoji', 'Emojis (😞 a 😃)'),
        ('text', 'Comentário em texto'),
        ('custom', 'Personalizado')
    ], string='Tipo de Avaliação', default='numeric_1_10', tracking=True,
       help='Define o formato de avaliação que o agente solicitará ao cliente')

    # Informações Adicionais
    share_address = fields.Boolean('Permitir ao agente informar o endereço quando solicitado', default=False, tracking=True,
                                 help='Se marcado, o agente poderá informar o endereço da empresa quando o cliente solicitar')
    inform_promotions = fields.Boolean('Quando estiver em vendas, informar promoções e sugerir produtos', default=False, tracking=True,
                                     help='Se marcado, o agente poderá informar promoções ativas e sugerir produtos relacionados durante conversas de vendas')

    @api.depends('name')  # Dependência fictícia para garantir que seja recalculado
    def _compute_enabled_services(self):
        """Calcula os serviços habilitados com base nas configurações do sistema."""
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        for record in self:
            record.enable_sales = IrConfigParam.get_param('company_services.enable_sales', 'False').lower() == 'true'
            record.enable_scheduling = IrConfigParam.get_param('company_services.enable_scheduling', 'False').lower() == 'true'
            record.enable_delivery = IrConfigParam.get_param('company_services.enable_delivery', 'False').lower() == 'true'
            record.enable_support = IrConfigParam.get_param('company_services.enable_support', 'False').lower() == 'true'

    # O método _compute_service_descriptions foi removido, pois não é mais necessário

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

            # Preparar dados para sincronização
            config_data = self._prepare_config_data(account_id, security_token)

            # Sincronizar com o serviço de configuração
            sync_service = self.env['company.sync.service'].sudo()
            result = sync_service.sync_company_data(config_data, account_id, security_token)

            if result.get('success'):
                self.write({
                    'sync_status': 'synced',
                    'last_sync': fields.Datetime.now()
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _('Dados sincronizados com sucesso.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                self.write({
                    'sync_status': 'error',
                    'error_message': result.get('error', 'Erro desconhecido')
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': result.get('error', 'Erro desconhecido'),
                        'sticky': False,
                        'type': 'danger',
                    }
                }
        except Exception as e:
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

    def _prepare_config_data(self, account_id, security_token):
        """Prepara os dados para sincronização."""
        self.ensure_one()

        # Obter configurações do sistema
        IrConfigParam = self.env['ir.config_parameter'].sudo()

        # Obter configurações de MCP
        mcp_type = IrConfigParam.get_param('company_services.mcp_type', 'odoo')
        mcp_version = IrConfigParam.get_param('company_services.mcp_version', '14.0')

        # Obter configurações de banco de dados
        db_url = IrConfigParam.get_param('company_services.db_url', '')
        # Usar account_id como nome do banco de dados para garantir consistência
        db_name = account_id
        db_user = IrConfigParam.get_param('company_services.db_user', '')
        db_password = IrConfigParam.get_param('company_services.db_password', '')
        db_access_level = IrConfigParam.get_param('company_services.db_access_level', 'read')

        # Preparar dias de funcionamento
        days = []
        if self.monday:
            days.append(0)
        if self.tuesday:
            days.append(1)
        if self.wednesday:
            days.append(2)
        if self.thursday:
            days.append(3)
        if self.friday:
            days.append(4)
        if self.saturday:
            days.append(5)
        if self.sunday:
            days.append(6)

        # Obter serviços habilitados das configurações
        enable_sales = IrConfigParam.get_param('company_services.enable_sales', 'False').lower() == 'true'
        enable_scheduling = IrConfigParam.get_param('company_services.enable_scheduling', 'False').lower() == 'true'
        enable_delivery = IrConfigParam.get_param('company_services.enable_delivery', 'False').lower() == 'true'
        enable_support = IrConfigParam.get_param('company_services.enable_support', 'False').lower() == 'true'

        # Preparar coleções habilitadas
        enabled_collections = []
        if enable_sales:
            enabled_collections.append('products_informations')
        if enable_scheduling:
            enabled_collections.append('scheduling_rules')
        if enable_delivery:
            enabled_collections.append('delivery_rules')
        if enable_support:
            enabled_collections.append('support_documents')

        # Construir o dicionário de configuração com estrutura organizada por módulos
        config_data = {
            'account_id': account_id,
            'security_token': security_token,  # Incluir token de segurança
            'name': self.name,
            'description': self.description or '',
            'version': 1,
            'updated_at': fields.Datetime.now().isoformat(),
            'enabled_modules': ['company_info', 'service_settings', 'enabled_services', 'mcp'],
            'modules': {
                # Módulo de informações da empresa
                'company_info': {
                    'name': self.name,
                    'description': self.description or '',
                    'address': {
                        'street': self.street or '',
                        'street2': self.street2 or '',
                        'city': self.city or '',
                        'state': self.state or '',
                        'zip': self.zip or '',
                        'country': self.country or '',
                        'share_with_customers': self.share_address
                    }
                },
                # Módulo de configurações de atendimento
                'service_settings': {
                    'business_hours': {
                        'days': days,
                        'start_time': self.start_time,
                        'end_time': self.end_time,
                        'has_lunch_break': self.has_lunch_break,
                        'lunch_break_start': self.lunch_break_start,
                        'lunch_break_end': self.lunch_break_end,
                        'saturday_start_time': self.saturday_start_time,
                        'saturday_end_time': self.saturday_end_time
                    },
                    'customer_service': {
                        'greeting_message': self.greeting_message or '',
                        'communication': {
                            'tone': self.tone,
                            'voice': self.voice,
                            'formality': self.formality,
                            'emoji_usage': self.emoji_usage
                        },
                        'farewell': {
                            'message': self.farewell_message or 'Obrigado por entrar em contato!',
                            'enabled': self.use_farewell
                        },
                        'rating_request': {
                            'message': self.rating_request_message or 'Sua opinião é muito importante para nós. Como você avaliaria este atendimento?',
                            'enabled': self.request_rating
                        }
                    },
                    'online_channels': {
                        'website': {
                            'url': self.website_url or False,
                            'mention_at_end': self.website_mention
                        },
                        'facebook': {
                            'url': self.facebook_url or False,
                            'mention_at_end': self.facebook_mention
                        },
                        'instagram': {
                            'url': self.instagram_url or False,
                            'mention_at_end': self.instagram_mention
                        }
                    }
                },
                # Módulo de serviços habilitados
                'enabled_services': {
                    'collections': enabled_collections,
                    'services': {
                        'sales': {
                            'enabled': enable_sales,
                            'promotions': {
                                'inform_at_start': self.inform_promotions
                            }
                        },
                        'scheduling': {
                            'enabled': enable_scheduling
                        },
                        'delivery': {
                            'enabled': enable_delivery
                        },
                        'support': {
                            'enabled': enable_support
                        }
                    }
                },
                # Módulo MCP (Model Communication Protocol)
                'mcp': {
                    'type': mcp_type,
                    'version': mcp_version,
                    'connection': {
                        'url': db_url,
                        'database': db_name,
                        'username': db_user,
                        'password_ref': f"{account_id}_db_pwd",  # Referência à senha
                        'access_level': db_access_level
                    }
                }
            }
        }

        # Para manter compatibilidade com o formato antigo, também incluímos a estrutura antiga
        config_data['enabled_collections'] = enabled_collections
        config_data['company_metadata'] = {
            'company_info': config_data['modules']['company_info'],
            'business_hours': config_data['modules']['service_settings']['business_hours'],
            'customer_service': config_data['modules']['service_settings']['customer_service'],
            'online_channels': config_data['modules']['service_settings']['online_channels'],
            'promotions': config_data['modules']['enabled_services']['services']['sales']['promotions']
        }

        # Adicionar informações de MCP para compatibilidade
        config_data['mcp'] = {
            'type': mcp_type,
            'config': {
                'url': db_url,
                'db': db_name,
                'username': db_user,
                'credential_ref': f"{account_id}_db_pwd"
            }
        }

        return yaml.dump(config_data, default_flow_style=False)
