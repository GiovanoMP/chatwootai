# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging
import yaml

_logger = logging.getLogger(__name__)

class ConfigViewer(models.TransientModel):
    _name = 'config.viewer'
    _description = 'Visualizador de Configurações'

    tenant_id = fields.Char(string='ID do Tenant', required=True)
    domain = fields.Char(string='Domínio', required=True, default='retail')
    config_type = fields.Selection([
        ('config', 'Configuração'),
        ('credentials', 'Credenciais'),
        ('crews', 'Crews')
    ], string='Tipo de Configuração', required=True, default='config')
    yaml_content = fields.Text(string='Conteúdo YAML', readonly=True)
    json_data = fields.Text(string='Dados JSON', readonly=True)

    def action_view_config(self):
        """Visualiza a configuração do microserviço."""
        self.ensure_one()

        # Importar o cliente do microserviço
        from .config_service import ConfigServiceClient

        # Criar uma instância do cliente
        client = ConfigServiceClient(self.env)

        # Verificar se o microserviço está disponível
        if not client.health_check():
            raise UserError(_("O microserviço de configuração não está disponível."))

        # Obter a configuração
        config_data = client.get_config(self.tenant_id, self.domain, self.config_type)

        if not config_data:
            raise UserError(_("Configuração não encontrada."))

        # Atualizar os campos
        self.yaml_content = config_data.get('yaml_content', '')
        self.json_data = json.dumps(config_data.get('json_data', {}), indent=2)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'config.viewer',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_check_config(self):
        """Verifica se a configuração existe no microserviço."""
        self.ensure_one()

        # Importar o cliente do microserviço
        from .config_service import ConfigServiceClient

        # Criar uma instância do cliente
        client = ConfigServiceClient(self.env)

        # Verificar se o microserviço está disponível
        if not client.health_check():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': _('O microserviço de configuração não está disponível.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }

        # Obter a configuração
        config_data = client.get_config(self.tenant_id, self.domain, self.config_type)

        if not config_data:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aviso'),
                    'message': _('Configuração não encontrada no microserviço.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }

        # Verificar se a configuração existe no sistema de arquivos
        import os
        config_file = os.path.join("config", "domains", self.domain, self.tenant_id, f"{self.config_type}.yaml")
        file_exists = os.path.exists(config_file)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Verificação Concluída'),
                'message': _(
                    'Configuração encontrada no microserviço. '
                    'Versão: %(version)s. '
                    'Última atualização: %(updated_at)s. '
                    'Arquivo local: %(file_exists)s.'
                ) % {
                    'version': config_data.get('version', 'N/A'),
                    'updated_at': config_data.get('updated_at', 'N/A'),
                    'file_exists': _('Existe') if file_exists else _('Não existe')
                },
                'sticky': False,
                'type': 'success',
            }
        }

class MappingViewer(models.TransientModel):
    _name = 'mapping.viewer'
    _description = 'Visualizador de Mapeamento Chatwoot'

    yaml_content = fields.Text(string='Conteúdo YAML', readonly=True)
    json_data = fields.Text(string='Dados JSON', readonly=True)

    def action_view_mapping(self):
        """Visualiza o mapeamento Chatwoot do microserviço."""
        self.ensure_one()

        # Importar o cliente do microserviço
        from .config_service import ConfigServiceClient

        # Criar uma instância do cliente
        client = ConfigServiceClient(self.env)

        # Verificar se o microserviço está disponível
        if not client.health_check():
            raise UserError(_("O microserviço de configuração não está disponível."))

        # Obter o mapeamento
        mapping_data = client.get_mapping()

        if not mapping_data:
            raise UserError(_("Mapeamento não encontrado."))

        # Atualizar os campos
        self.yaml_content = yaml.dump(mapping_data, default_flow_style=False)
        self.json_data = json.dumps(mapping_data, indent=2)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mapping.viewer',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_check_mapping(self):
        """Verifica se o mapeamento existe no microserviço."""
        self.ensure_one()

        # Importar o cliente do microserviço
        from .config_service import ConfigServiceClient

        # Criar uma instância do cliente
        client = ConfigServiceClient(self.env)

        # Verificar se o microserviço está disponível
        if not client.health_check():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': _('O microserviço de configuração não está disponível.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }

        # Obter o mapeamento
        mapping_data = client.get_mapping()

        if not mapping_data:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aviso'),
                    'message': _('Mapeamento não encontrado no microserviço.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }

        # Verificar se o mapeamento existe no sistema de arquivos
        import os
        mapping_file = os.path.join("config", "chatwoot_mapping.yaml")
        file_exists = os.path.exists(mapping_file)

        # Contar o número de contas e caixas de entrada
        accounts_count = len(mapping_data.get('accounts', {}))
        inboxes_count = len(mapping_data.get('inboxes', {}))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Verificação Concluída'),
                'message': _(
                    'Mapeamento encontrado no microserviço. '
                    'Contas: %(accounts_count)s. '
                    'Caixas de entrada: %(inboxes_count)s. '
                    'Arquivo local: %(file_exists)s.'
                ) % {
                    'accounts_count': accounts_count,
                    'inboxes_count': inboxes_count,
                    'file_exists': _('Existe') if file_exists else _('Não existe')
                },
                'sticky': False,
                'type': 'success',
            }
        }
