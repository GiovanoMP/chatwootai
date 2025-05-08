# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import requests
from datetime import datetime

_logger = logging.getLogger(__name__)

class BusinessRules(models.Model):
    _name = 'business.rules'
    _description = 'Regras de Negócio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nome da Empresa', required=True, tracking=True)

    # Canais online da empresa
    website = fields.Char(string='Site da Empresa', tracking=True)
    mention_website_at_end = fields.Boolean(string='Mencionar site ao finalizar conversa', default=False, tracking=True,
                                          help='Se marcado, o agente mencionará o site da empresa ao finalizar a conversa')

    facebook_url = fields.Char(string='Página do Facebook', tracking=True,
                              help='URL completa da página do Facebook (ex: https://www.facebook.com/suaempresa)')
    mention_facebook_at_end = fields.Boolean(string='Mencionar Facebook ao finalizar conversa', default=False, tracking=True,
                                           help='Se marcado, o agente mencionará a página do Facebook ao finalizar a conversa')

    instagram_url = fields.Char(string='Perfil do Instagram', tracking=True,
                               help='URL completa do perfil do Instagram (ex: https://www.instagram.com/suaempresa)')
    mention_instagram_at_end = fields.Boolean(string='Mencionar Instagram ao finalizar conversa', default=False, tracking=True,
                                            help='Se marcado, o agente mencionará o perfil do Instagram ao finalizar a conversa')

    description = fields.Text(string='Descrição da Empresa', tracking=True)
    company_values = fields.Text(string='Valores da Marca', tracking=True,
                                help='Descreva os principais valores que sua marca representa')

    # Endereço da empresa
    street = fields.Char(string='Endereço', tracking=True)
    street2 = fields.Char(string='Complemento', tracking=True)
    city = fields.Char(string='Cidade', tracking=True)
    state = fields.Char(string='Estado', tracking=True)
    zip = fields.Char(string='CEP', tracking=True)
    country = fields.Char(string='País', default='Brasil', tracking=True)
    share_address = fields.Boolean(string='Permitir ao agente informar o endereço quando solicitado',
                                  default=True, tracking=True,
                                  help='Se marcado, o agente poderá informar o endereço da empresa quando o cliente solicitar')

    # Configurações de Atendimento
    greeting_message = fields.Text(string='Saudação Inicial', tracking=True,
                                  help='Como o agente deve cumprimentar os clientes')
    communication_style = fields.Selection([
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('friendly', 'Amigável'),
        ('technical', 'Técnico')
    ], string='Estilo de Comunicação', default='friendly', tracking=True)

    emoji_usage = fields.Selection([
        ('none', 'Não Usar'),
        ('moderate', 'Uso Moderado'),
        ('frequent', 'Uso Frequente')
    ], string='Uso de Emojis', default='moderate', tracking=True)

    # Horário de funcionamento
    business_hours_start = fields.Float(string='Horário de Início', default=8.0, tracking=True)
    business_hours_end = fields.Float(string='Horário de Término', default=18.0, tracking=True)

    # Intervalo de almoço
    lunch_break_start = fields.Float(string='Início do Intervalo', default=12.0, tracking=True)
    lunch_break_end = fields.Float(string='Fim do Intervalo', default=13.0, tracking=True)
    has_lunch_break = fields.Boolean(string='Possui Intervalo', default=True, tracking=True)

    # Dias de funcionamento
    monday = fields.Boolean(string='Segunda-feira', default=True, tracking=True)
    tuesday = fields.Boolean(string='Terça-feira', default=True, tracking=True)
    wednesday = fields.Boolean(string='Quarta-feira', default=True, tracking=True)
    thursday = fields.Boolean(string='Quinta-feira', default=True, tracking=True)
    friday = fields.Boolean(string='Sexta-feira', default=True, tracking=True)
    saturday = fields.Boolean(string='Sábado', default=False, tracking=True)
    sunday = fields.Boolean(string='Domingo', default=False, tracking=True)

    # Horários especiais para sábado e domingo
    saturday_hours_start = fields.Float(string='Início Sábado', default=8.0, tracking=True)
    saturday_hours_end = fields.Float(string='Término Sábado', default=12.0, tracking=True)
    sunday_hours_start = fields.Float(string='Início Domingo', default=8.0, tracking=True)
    sunday_hours_end = fields.Float(string='Término Domingo', default=12.0, tracking=True)

    # Área de Negócio
    business_area = fields.Selection([
        ('retail', 'Varejo/Loja Física'),
        ('ecommerce', 'E-commerce/Loja Virtual'),
        ('healthcare', 'Saúde/Clínica/Consultório'),
        ('education', 'Educação'),
        ('manufacturing', 'Indústria'),
        ('services', 'Prestador de Serviços'),
        ('restaurant', 'Restaurante/Pizzaria'),
        ('financial', 'Serviços Financeiros'),
        ('technology', 'Tecnologia'),
        ('hospitality', 'Hotelaria'),
        ('real_estate', 'Imobiliário'),
        ('other', 'Outro')
    ], string='Área de Negócio', required=True, tracking=True)

    business_area_other = fields.Char(string='Outra Área de Negócio', tracking=True)

    # Regras e Sincronização
    rule_ids = fields.One2many('business.rule.item', 'business_rule_id', string='Regras de Negócio')
    temporary_rule_ids = fields.One2many('business.temporary.rule', 'business_rule_id', string='Regras Temporárias e Promoções')
    scheduling_rule_ids = fields.One2many('business.scheduling.rule', 'business_rule_id', string='Regras de Agendamento')
    inform_promotions_at_start = fields.Boolean(string='Informar Promoções e Regras Temporárias no início da conversa', default=False, tracking=True,
                                              help='Se marcado, o agente informará sobre promoções e regras temporárias ativas no início da conversa com o cliente')

    # Documentos de Suporte ao Cliente
    support_document_ids = fields.Many2many(
        'business.support.document',
        'business_rule_support_doc_rel',
        'business_rule_id',
        'document_id',
        string='Documentos de Suporte',
        help='Documentos relacionados ao suporte ao cliente',
        context={'active_test': False}  # Incluir documentos inativos
    )

    # Serviços de Atendimento Habilitados
    use_business_rules = fields.Boolean('Vendas de Produtos e Serviços', default=True,
                                      help="Habilita consultas sobre produtos, preços e condições de venda")
    use_scheduling_rules = fields.Boolean('Agendamentos', default=False,
                                        help="Habilita consultas sobre agendamentos e horários disponíveis")
    use_delivery_rules = fields.Boolean('Delivery', default=False,
                                      help="Habilita consultas sobre entregas, prazos e condições")
    use_support_documents = fields.Boolean('Suporte ao Cliente', default=False,
                                         help="Habilita consultas sobre documentos de suporte e FAQ")

    last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Sincronizando...'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro na Sincronização')
    ], string='Status de Sincronização', default='not_synced', readonly=True)

    active = fields.Boolean(default=True, string='Ativo')
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, esta regra será incluída no sistema de IA')
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)

    # Contagem de regras ativas
    active_permanent_rules_count = fields.Integer(compute='_compute_active_rules_count', string='Regras de Negócio Ativas')
    active_temporary_rules_count = fields.Integer(compute='_compute_active_rules_count', string='Promoções e Regras Temporárias Ativas')

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'description', 'company_values', 'business_area', 'business_area_other',
            'website', 'facebook_url', 'instagram_url', 'mention_website_at_end',
            'mention_facebook_at_end', 'mention_instagram_at_end',
            'greeting_message', 'communication_style', 'emoji_usage',
            'business_hours_start', 'business_hours_end', 'has_lunch_break',
            'lunch_break_start', 'lunch_break_end',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'saturday_hours_start', 'saturday_hours_end', 'sunday_hours_start', 'sunday_hours_end',
            'street', 'street2', 'city', 'state', 'zip', 'country', 'share_address',
            'inform_promotions_at_start', 'visible_in_ai',
            'use_business_rules', 'use_scheduling_rules', 'use_delivery_rules', 'use_support_documents'
        ]

        # Se a regra está sendo marcada como não disponível no IA, marcar para sincronização
        if 'visible_in_ai' in vals and vals['visible_in_ai'] is False:
            vals['sync_status'] = 'not_synced'

        # Verificar se algum campo relevante foi alterado
        elif any(field in vals for field in sync_fields):
            # Se o status atual é 'synced', mudar para 'not_synced'
            if self.sync_status == 'synced':
                vals['sync_status'] = 'not_synced'

        return super(BusinessRules, self).write(vals)

    @api.depends('rule_ids', 'temporary_rule_ids')
    def _compute_active_rules_count(self):
        for record in self:
            record.active_permanent_rules_count = len(record.rule_ids.filtered(lambda r: r.active))

            # Contar apenas regras temporárias ativas e dentro do período de validade
            now = fields.Datetime.now()
            active_temp_rules = record.temporary_rule_ids.filtered(
                lambda r: r.active and
                (not r.date_start or r.date_start <= now) and
                (not r.date_end or r.date_end >= now)
            )
            record.active_temporary_rules_count = len(active_temp_rules)

    @api.onchange('business_area')
    def _onchange_business_area(self):
        """Carregar regras padrão com base na área de negócio selecionada"""
        if self.business_area:
            # Aqui carregaríamos regras padrão da área selecionada
            # Implementação completa será feita posteriormente
            template = self.env['business.template'].search([('model_type', '=', self.business_area)], limit=1)
            if template:
                self.greeting_message = template.default_greeting
                # Outras configurações padrão podem ser carregadas aqui

    def action_sync_with_ai(self):
        """Sincronizar regras e metadados com o sistema de IA"""
        self.ensure_one()

        # Atualizar status para 'sincronizando'
        try:
            # Usar savepoint para evitar problemas de serialização
            with self.env.cr.savepoint():
                self.write({'sync_status': 'syncing'})
            self.env.cr.commit()  # Commit imediato para atualizar a UI
        except Exception as e:
            _logger.error(f"Erro ao atualizar status para 'syncing': {e}")
            # Continuar mesmo se falhar a atualização de status

        try:
            # Importar o controlador
            from ..controllers.sync_controller import BusinessRulesSyncController

            # Criar uma instância do controlador
            controller = BusinessRulesSyncController()

            # 1. Primeiro sincronizar os metadados da empresa
            _logger.info(f"Iniciando sincronização de metadados para a regra de negócio {self.id}")
            metadata_result = controller.sync_company_metadata(self.id, env=self.env)

            if not metadata_result or not metadata_result.get('success'):
                _logger.warning(f"Falha na sincronização de metadados: {metadata_result.get('error', 'Erro desconhecido')}")
                # Continuar mesmo se a sincronização de metadados falhar
            else:
                _logger.info("Metadados da empresa sincronizados com sucesso")

            # 2. Depois sincronizar as regras de negócio
            _logger.info(f"Iniciando sincronização de regras para a regra de negócio {self.id}")
            rules_result = controller.sync_business_rules(self.id, env=self.env)

            # 3. Sincronizar regras de agendamento
            _logger.info(f"Iniciando sincronização de regras de agendamento para a regra de negócio {self.id}")
            scheduling_result = controller.sync_scheduling_rules(self.id, env=self.env)

            if not scheduling_result or not scheduling_result.get('success'):
                _logger.warning(f"Falha na sincronização de regras de agendamento: {scheduling_result.get('error', 'Erro desconhecido')}")
                # Continuar mesmo se a sincronização de regras de agendamento falhar
            else:
                _logger.info("Regras de agendamento sincronizadas com sucesso")

            # Verificar resultado da sincronização de regras
            if rules_result and rules_result.get('success'):
                try:
                    # Usar savepoint para evitar problemas de serialização
                    with self.env.cr.savepoint():
                        self.write({
                            'last_sync_date': fields.Datetime.now(),
                            'sync_status': 'synced'
                        })
                except Exception as status_error:
                    _logger.error(f"Erro ao atualizar status para 'synced': {status_error}")
                    # Tentar novamente com retry
                    try:
                        # Atualizar novamente após um pequeno delay
                        import time
                        time.sleep(0.5)
                        with self.env.cr.savepoint():
                            self.write({
                                'last_sync_date': fields.Datetime.now(),
                                'sync_status': 'synced'
                            })
                    except Exception as retry_error:
                        _logger.error(f"Falha no retry ao atualizar status: {retry_error}")

                # Mensagem de sucesso com detalhes
                rules_count = rules_result.get('rules_count', 0)
                vectorized_count = rules_result.get('vectorized_rules', 0)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _(f'Sincronizadas {rules_count} regras, {vectorized_count} vetorizadas. Metadados da empresa também foram sincronizados.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                # Atualizar status para erro
                self.write({
                    'last_sync_date': fields.Datetime.now(),
                    'sync_status': 'error'
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': _(f'Erro ao sincronizar regras: {rules_result.get("error", "Erro desconhecido")}'),
                        'sticky': True,
                        'type': 'danger',
                    }
                }

        except Exception as e:
            # Em caso de erro, atualizar status
            self.write({
                'last_sync_date': fields.Datetime.now(),
                'sync_status': 'error'
            })

            _logger.error("Erro ao sincronizar regras: %s", str(e))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro na Sincronização'),
                    'message': _(f'Erro ao sincronizar: {str(e)}'),
                    'sticky': True,
                    'type': 'danger',
                }
            }

    def action_view_active_rules(self):
        """Abrir dashboard de regras ativas"""
        self.ensure_one()
        return {
            'name': _('Regras Ativas'),
            'type': 'ir.actions.act_window',
            'res_model': 'business.rules.dashboard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_business_rule_id': self.id}
        }

    # Método action_scrape_website removido pois não é mais necessário

    def action_view_customer_support(self):
        """Abre a visualização de suporte ao cliente."""
        self.ensure_one()
        return {
            'name': _('Suporte ao Cliente'),
            'type': 'ir.actions.act_window',
            'res_model': 'business.support.document',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.support_document_ids.ids)],
            'context': {
                'default_business_rule_id': self.id,
                'active_test': False  # Mostrar registros inativos
            }
        }

    def action_upload_documents(self):
        """Abrir wizard para upload de documentos"""
        self.ensure_one()
        return {
            'name': _('Adicionar Documento de Suporte'),
            'type': 'ir.actions.act_window',
            'res_model': 'business.document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_business_rule_id': self.id}
        }

    def action_add_service_config(self):
        """Abre um formulário para adicionar configurações de atendimento"""
        self.ensure_one()
        # Como as configurações de atendimento são campos do próprio modelo business.rules,
        # vamos apenas abrir o formulário atual em modo de edição
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'business.rules',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'mode': 'edit'},
            'context': {'active_tab': 'service_config'}
        }

    def action_sync_support_documents(self):
        """Sincroniza os documentos de suporte com o sistema de IA."""
        self.ensure_one()
        try:
            # Verificar se há documentos selecionados
            if not self.support_document_ids:
                _logger.warning("Nenhum documento selecionado encontrado para sincronização")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Aviso'),
                        'message': _('Nenhum documento selecionado para sincronização.'),
                        'sticky': False,
                        'type': 'warning'
                    }
                }

            # Ordenar documentos por data de criação (mais recente primeiro)
            sorted_docs = self.support_document_ids.sorted(key=lambda r: r.create_date or fields.Datetime.now(), reverse=True)

            # Informar quantos documentos estão ativos e inativos
            active_count = len(self.support_document_ids.filtered(lambda r: r.active))
            inactive_count = len(self.support_document_ids) - active_count
            _logger.info(f"Documentos selecionados: {len(self.support_document_ids)} (Ativos: {active_count}, Inativos: {inactive_count})")

            # Sincronizar todos os documentos selecionados
            if len(sorted_docs) > 1:
                _logger.info(f"Encontrados {len(sorted_docs)} documentos selecionados para sincronização")
                # Não limitar mais a apenas um documento
                _logger.info(f"Sincronizando todos os {len(sorted_docs)} documentos selecionados")

            # Chamar o MCP-Odoo para sincronizar documentos
            result = self._call_mcp_sync_support_docs()

            if result and result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _('Documentos sincronizados com sucesso.'),
                        'sticky': False,
                        'type': 'success'
                    }
                }
            else:
                error_msg = result.get('error') if result else "Erro desconhecido"
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Falha na Sincronização'),
                        'message': error_msg,
                        'sticky': False,
                        'type': 'danger'
                    }
                }
        except Exception as e:
            _logger.error("Erro ao sincronizar documentos de suporte: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger'
                }
            }

    def _call_mcp_sync_support_docs(self):
        """Chama o MCP-Odoo para sincronizar documentos de suporte."""
        try:
            import requests

            # Obter configurações do MCP-Odoo
            IrConfigParam = self.env['ir.config_parameter'].sudo()
            mcp_url = IrConfigParam.get_param('business_rules.mcp_url', 'http://localhost:8000')
            mcp_token = IrConfigParam.get_param('business_rules.mcp_token', '')
            account_id = IrConfigParam.get_param('business_rules.account_id', 'account_1')

            # Preparar a requisição
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
            }

            # Enviar apenas os documentos selecionados (independente de estarem ativos ou não)
            docs_data = []

            # Verificar se há documentos
            if self.support_document_ids:
                # Ordenar documentos por data de criação (mais recente primeiro)
                sorted_docs = self.support_document_ids.sorted(
                    key=lambda r: r.create_date or fields.Datetime.now(), reverse=True
                )

                # Enviar todos os documentos selecionados (apenas os ativos serão processados pelo sistema de IA)
                _logger.info(f"Enviando {len(sorted_docs)} documentos selecionados para sincronização")

                # Adicionar todos os documentos selecionados (com informação de status)
                for doc in sorted_docs:
                    _logger.info(f"Adicionando documento: {doc.name} (ID: {doc.id}, Ativo: {doc.active}, Visível no IA: {doc.visible_in_ai})")
                    docs_data.append({
                        'id': doc.id,
                        'name': doc.name,
                        'document_type': doc.document_type,
                        'content': doc.content,
                        'active': doc.active,  # Incluir status de ativação
                        'visible_in_ai': doc.visible_in_ai,  # Incluir status de visibilidade no IA
                        'create_date': fields.Datetime.to_string(doc.create_date) if doc.create_date else '',
                    })

            payload = {
                'account_id': account_id,
                'business_rule_id': self.id,
                'documents': docs_data
            }

            # Fazer a requisição ao MCP-Odoo
            _logger.info(f"Chamando MCP-Odoo para sincronizar documentos de suporte para a regra de negócio {self.id}")
            response = requests.post(
                f"{mcp_url}/api/v1/business-rules/sync-support-documents",
                headers=headers,
                params={"account_id": account_id},  # Adicionar account_id como parâmetro de query
                json=payload,
                timeout=30  # Timeout de 30 segundos
            )

            # Verificar resposta
            if response.status_code == 200:
                result = response.json()

                # Atualizar status de sincronização dos documentos
                if result.get('synced_docs'):
                    for doc_id in result['synced_docs']:
                        try:
                            doc = self.env['business.support.document'].browse(int(doc_id))
                            if doc:
                                # Usar savepoint para evitar problemas de serialização
                                with self.env.cr.savepoint():
                                    doc.write({'sync_status': 'synced'})
                        except Exception as doc_update_error:
                            _logger.error(f"Erro ao atualizar status do documento {doc_id}: {doc_update_error}")

                # Atualizar o status de sincronização da regra de negócio
                try:
                    # Usar savepoint para evitar problemas de serialização
                    with self.env.cr.savepoint():
                        self.write({
                            'last_sync_date': fields.Datetime.now(),
                            'sync_status': 'synced'
                        })
                except Exception as rule_update_error:
                    _logger.error(f"Erro ao atualizar status da regra de negócio: {rule_update_error}")

                return result
            else:
                _logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")
                return {'success': False, 'error': f"Erro {response.status_code}: {response.text}"}
        except Exception as e:
            _logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
            return {'success': False, 'error': str(e)}

    def action_view_business_rules(self):
        """Visualiza as regras de negócio no Sistema de IA"""
        self.ensure_one()

        # Obter URL base e token de autenticação
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        mcp_url = IrConfigParam.get_param('business_rules.mcp_url', 'http://localhost:8000')
        account_id = IrConfigParam.get_param('business_rules.account_id', 'account_1')

        # Construir URL para visualização
        url = f"{mcp_url}/api/v1/business-rules/view?account_id={account_id}"

        # Abrir URL em nova janela
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_view_temporary_rules(self):
        """Visualiza as regras temporárias no Sistema de IA"""
        self.ensure_one()

        # Obter URL base e token de autenticação
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        mcp_url = IrConfigParam.get_param('business_rules.mcp_url', 'http://localhost:8000')
        account_id = IrConfigParam.get_param('business_rules.account_id', 'account_1')

        # Construir URL para visualização
        url = f"{mcp_url}/api/v1/business-rules/view-temporary-rules?account_id={account_id}"

        # Abrir URL em nova janela
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_sync_scheduling_rules(self):
        """Sincroniza apenas as regras de agendamento com o sistema de IA"""
        self.ensure_one()

        # Atualizar status para 'sincronizando'
        try:
            # Usar savepoint para evitar problemas de serialização
            with self.env.cr.savepoint():
                self.write({'sync_status': 'syncing'})
            self.env.cr.commit()  # Commit imediato para atualizar a UI
        except Exception as e:
            _logger.error(f"Erro ao atualizar status para 'syncing': {e}")
            # Continuar mesmo se falhar a atualização de status

        try:
            # Importar o controlador
            from ..controllers.sync_controller import BusinessRulesSyncController

            # Criar uma instância do controlador
            controller = BusinessRulesSyncController()

            # Sincronizar regras de agendamento
            _logger.info(f"Iniciando sincronização de regras de agendamento para a regra de negócio {self.id}")
            result = controller.sync_scheduling_rules(self.id, env=self.env)

            # Verificar resultado da sincronização
            if result and result.get('success'):
                try:
                    # Usar savepoint para evitar problemas de serialização
                    with self.env.cr.savepoint():
                        self.write({
                            'last_sync_date': fields.Datetime.now(),
                            'sync_status': 'synced'
                        })
                except Exception as status_error:
                    _logger.error(f"Erro ao atualizar status para 'synced': {status_error}")

                # Mensagem de sucesso com detalhes
                rules_count = result.get('rules_count', 0)
                vectorized_count = result.get('vectorized_rules', 0)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _(f'Sincronizadas {rules_count} regras de agendamento, {vectorized_count} vetorizadas.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                # Atualizar status para erro
                self.write({
                    'last_sync_date': fields.Datetime.now(),
                    'sync_status': 'error'
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro na Sincronização'),
                        'message': _(f'Erro ao sincronizar regras de agendamento: {result.get("error", "Erro desconhecido")}'),
                        'sticky': True,
                        'type': 'danger',
                    }
                }

        except Exception as e:
            # Em caso de erro, atualizar status
            self.write({
                'last_sync_date': fields.Datetime.now(),
                'sync_status': 'error'
            })

            _logger.error("Erro ao sincronizar regras de agendamento: %s", str(e))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro na Sincronização'),
                    'message': _(f'Erro ao sincronizar: {str(e)}'),
                    'sticky': True,
                    'type': 'danger',
                }
            }

    def action_view_scheduling_rules(self):
        """Visualiza as regras de agendamento no Sistema de IA"""
        self.ensure_one()

        # Obter URL base e token de autenticação
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        mcp_url = IrConfigParam.get_param('business_rules.mcp_url', 'http://localhost:8000')
        account_id = IrConfigParam.get_param('business_rules.account_id', 'account_1')

        # Construir URL para visualização
        url = f"{mcp_url}/api/v1/business-rules/view-scheduling-rules?account_id={account_id}"

        # Abrir URL em nova janela
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_view_support_documents(self):
        """Visualiza os documentos de suporte no Sistema de IA"""
        self.ensure_one()

        # Obter URL base e token de autenticação
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        mcp_url = IrConfigParam.get_param('business_rules.mcp_url', 'http://localhost:8000')
        account_id = IrConfigParam.get_param('business_rules.account_id', 'account_1')

        # Construir URL para visualização
        url = f"{mcp_url}/api/v1/business-rules/view-support-documents?account_id={account_id}"

        # Abrir URL em nova janela
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_view_company_metadata(self):
        """Visualiza os metadados da empresa no Sistema de IA"""
        self.ensure_one()

        # Obter URL base e token de autenticação
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        mcp_url = IrConfigParam.get_param('business_rules.mcp_url', 'http://localhost:8000')
        account_id = IrConfigParam.get_param('business_rules.account_id', 'account_1')

        # Construir URL para visualização
        url = f"{mcp_url}/api/v1/business-rules/view-company-metadata?account_id={account_id}"

        # Abrir URL em nova janela
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
