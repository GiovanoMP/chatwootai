# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import json

_logger = logging.getLogger(__name__)

class AIChannelMapping(models.Model):
    _name = 'ai.channel.mapping'
    _description = 'Mapeamento de Canais para o Sistema de IA'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nome', compute='_compute_name', store=True)
    chatwoot_account_id = fields.Integer('ID da Conta no Chatwoot', required=True, tracking=True,
                                  help='ID numérico da conta no Chatwoot (ex: 1, 2, 3)')
    chatwoot_inbox_id = fields.Integer('ID da Caixa de Entrada no Chatwoot', tracking=True,
                                     help='ID numérico da caixa de entrada no Chatwoot (opcional)')

    # Usar o mesmo campo de seleção que o modelo ai.system.credentials
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

    business_area_other = fields.Char('Outra Área de Negócio', tracking=True)

    # Referência à credencial
    credential_id = fields.Many2one('ai.system.credentials', string='Credencial',
                                   required=True, ondelete='restrict', tracking=True)
    internal_account_id = fields.Char(related='credential_id.account_id',
                                     string='ID da Conta Interna', store=True, readonly=True)

    is_fallback = fields.Boolean('É Fallback', default=False, tracking=True,
                                help='Se marcado, este mapeamento será usado como fallback quando nenhum outro mapeamento for encontrado')
    sequence = fields.Integer('Sequência', default=10, tracking=True,
                             help='Ordem de prioridade para fallbacks (menor número = maior prioridade)')

    # Campos para números de WhatsApp especiais
    special_whatsapp_number1 = fields.Char('Número WhatsApp Especial 1', tracking=True,
                                          help='Número de WhatsApp que será direcionado para a crew analytics')
    special_whatsapp_number2 = fields.Char('Número WhatsApp Especial 2', tracking=True)
    special_whatsapp_number3 = fields.Char('Número WhatsApp Especial 3', tracking=True)
    special_crew = fields.Selection([
        ('analytics', 'Analytics'),
        ('admin', 'Administração'),
    ], string='Crew Especial', default='analytics', tracking=True,
       help='Crew para a qual as mensagens dos números especiais serão direcionadas')

    active = fields.Boolean('Ativo', default=True, tracking=True)

    # Status de sincronização
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro')
    ], string='Status de Sincronização', default='not_synced', readonly=True, tracking=True)
    last_sync = fields.Datetime('Última Sincronização', readonly=True)
    error_message = fields.Text('Mensagem de Erro', readonly=True)

    _sql_constraints = [
        ('unique_chatwoot_mapping', 'unique(chatwoot_account_id, chatwoot_inbox_id)',
         'Já existe um mapeamento para esta combinação de Conta e Caixa de Entrada do Chatwoot!')
    ]

    @api.depends('chatwoot_account_id', 'chatwoot_inbox_id', 'credential_id', 'business_area')
    def _compute_name(self):
        """Gera automaticamente um nome para o mapeamento."""
        for record in self:
            if record.chatwoot_account_id and record.credential_id:
                # Obter o nome da área de negócio
                business_area_name = dict(self._fields['business_area'].selection).get(record.business_area, '')

                # Gerar nome baseado no account_id do Chatwoot e na área de negócio
                if record.chatwoot_inbox_id:
                    record.name = f"Chatwoot {record.chatwoot_account_id}/{record.chatwoot_inbox_id} → {record.internal_account_id} ({business_area_name})"
                else:
                    record.name = f"Chatwoot {record.chatwoot_account_id} → {record.internal_account_id} ({business_area_name})"
            else:
                record.name = "Novo Mapeamento"

    @api.constrains('credential_id', 'business_area')
    def _check_business_area_consistency(self):
        for record in self:
            if record.business_area != 'other' and record.credential_id.business_area != record.business_area:
                raise ValidationError(_(
                    "A área de negócio selecionada (%s) não corresponde à área de negócio da credencial (%s)."
                ) % (dict(self._fields['business_area'].selection).get(record.business_area),
                     dict(self._fields['business_area'].selection).get(record.credential_id.business_area)))

    def get_domain(self):
        """Obtém o nome do domínio com base na área de negócio."""
        self.ensure_one()
        if self.business_area == 'other':
            return self.business_area_other.lower() if self.business_area_other else 'general'
        return self.business_area.lower()

    def action_sync_mapping(self):
        """Sincroniza o mapeamento com o sistema de IA."""
        self.ensure_one()

        try:
            # Atualizar status
            self.write({
                'sync_status': 'syncing',
                'error_message': False
            })

            # Obter o serviço de configuração
            config_service = self.env['ai.config.service']

            # Sincronizar o mapeamento usando o serviço de configuração
            success = config_service.sync_chatwoot_mapping(
                account_id=self.internal_account_id,
                domain=self.get_domain(),
                chatwoot_account_id=self.chatwoot_account_id,
                chatwoot_inbox_id=self.chatwoot_inbox_id if self.chatwoot_inbox_id else None
            )

            if success:
                # Registrar sincronização bem-sucedida
                self.env['ai.credentials.access.log'].sudo().create({
                    'credential_id': self.credential_id.id,
                    'access_time': fields.Datetime.now(),
                    'ip_address': self.env.context.get('remote_addr', 'N/A'),
                    'operation': 'sync_mapping',
                    'success': True
                })

                # Atualizar status de sincronização
                self.write({
                    'sync_status': 'synced',
                    'last_sync': fields.Datetime.now(),
                    'error_message': False
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização bem-sucedida'),
                        'message': _('O mapeamento foi sincronizado com o sistema de IA.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                # Falha na sincronização
                error_msg = "Falha ao sincronizar mapeamento com o serviço de configuração"

                # Atualizar status de sincronização
                self.write({
                    'sync_status': 'error',
                    'error_message': error_msg
                })

                # Registrar falha
                self.env['ai.credentials.access.log'].sudo().create({
                    'credential_id': self.credential_id.id,
                    'access_time': fields.Datetime.now(),
                    'ip_address': self.env.context.get('remote_addr', 'N/A'),
                    'operation': 'sync_mapping',
                    'success': False,
                    'error_message': error_msg
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Falha na sincronização'),
                        'message': error_msg,
                        'sticky': False,
                        'type': 'danger',
                    }
                }

        except Exception as e:
            # Atualizar status de sincronização
            self.write({
                'sync_status': 'error',
                'error_message': str(e)
            })

            # Registrar falha
            self.env['ai.credentials.access.log'].sudo().create({
                'credential_id': self.credential_id.id,
                'access_time': fields.Datetime.now(),
                'ip_address': self.env.context.get('remote_addr', 'N/A'),
                'operation': 'sync_mapping',
                'success': False,
                'error_message': str(e)
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Falha na sincronização'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }

    @api.model
    def action_sync_all_mappings(self):
        """Sincroniza todos os mapeamentos ativos com o sistema de IA."""
        mappings = self.search([('active', '=', True)])

        success_count = 0
        error_count = 0

        for mapping in mappings:
            try:
                result = mapping.action_sync_mapping()
                if result.get('params', {}).get('type') == 'success':
                    success_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sincronização concluída'),
                'message': _('%s mapeamentos sincronizados com sucesso, %s falhas.') % (success_count, error_count),
                'sticky': False,
                'type': 'info',
            }
        }
