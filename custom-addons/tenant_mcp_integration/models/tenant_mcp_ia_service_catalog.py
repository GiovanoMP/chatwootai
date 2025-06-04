# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class TenantMcpIaServiceCatalog(models.Model):
    _name = 'tenant_mcp.ia.service.catalog'
    _description = 'Catálogo de Serviços de IA para Integração MCP'
    _log_access = False
    _rec_name = 'display_name' # Usaremos um campo calculado para o nome de exibição

    module_id = fields.Many2one(
        'ir.module.module', 
        string='Módulo Odoo Base', 
        required=True, 
        ondelete='cascade', 
        index=True,
        help="O módulo Odoo que fornece este serviço de IA."
    )
    # Campos relacionados ao módulo Odoo original para referência
    original_module_name = fields.Char(related='module_id.name', string="Nome Original do Módulo", store=False, readonly=True)
    summary = fields.Char(related='module_id.summary', store=False, readonly=True)
    author = fields.Char(related='module_id.author', store=False, readonly=True)
    category_id = fields.Many2one(related='module_id.category_id', store=False, readonly=True)
    state = fields.Selection(related='module_id.state', string="Status do Módulo", store=False, readonly=True)
    
    is_ia_service_available = fields.Boolean(
        string='Serviço de IA Disponível?', 
        default=False,
        tracking=True,
        help="Se marcado, indica que este módulo Odoo oferece um serviço de IA documentado e pronto para ser utilizado pelo MCP-CREW."
    )
    ia_service_name = fields.Char(
        string="Nome do Serviço de IA", 
        tracking=True,
        help="Nome amigável e descritivo para o serviço de IA oferecido por este módulo (ex: Otimizador de Descrição de Produto)."
    )
    ia_service_description = fields.Text(
        string="Descrição do Serviço de IA",
        help="Descrição detalhada do que o serviço de IA faz, seus benefícios e casos de uso."
    )
    api_endpoint_details = fields.Text(
        string="Detalhes dos Endpoints da API",
        help="Informações sobre os endpoints da API expostos por este serviço, padrões de URL, métodos, etc. (informativo)."
    )
    technical_notes = fields.Text(
        string='Notas Técnicas Internas',
        help="Notas técnicas sobre a implementação ou configuração deste serviço de IA."
    )

    display_name = fields.Char(string="Nome de Exibição", compute='_compute_display_name', store=False)

    _sql_constraints = [
        ('module_id_uniq', 'unique (module_id)', 'Já existe um registro de serviço de IA para este módulo Odoo.')
    ]

    @api.depends('ia_service_name', 'original_module_name', 'is_ia_service_available')
    def _compute_display_name(self):
        for record in self:
            if record.is_ia_service_available and record.ia_service_name:
                record.display_name = record.ia_service_name
            else:
                record.display_name = record.original_module_name

    @api.model
    def synchronize_modules(self):
        """Cria ou atualiza registros no catálogo de serviços de IA para todos os módulos instaláveis."""
        all_modules = self.env['ir.module.module'].search([])
        # Usamos original_module_name para garantir que estamos comparando com o campo correto
        # ou melhor, usamos module_id diretamente que é o link
        
        existing_catalog_entries = self.search_read([('module_id', 'in', all_modules.ids)], ['module_id'])
        existing_module_ids = [entry['module_id'][0] for entry in existing_catalog_entries]

        modules_to_create = []
        for module in all_modules:
            if module.id not in existing_module_ids:
                modules_to_create.append({
                    'module_id': module.id,
                    # Valores padrão podem ser definidos aqui se necessário,
                    # mas geralmente o usuário os preencherá após a sincronização.
                    # 'is_ia_service_available': False, # Por padrão, não está disponível até ser configurado
                })
        
        if modules_to_create:
            self.create(modules_to_create)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sincronização Concluída'),
                'message': _('Catálogo de Serviços de IA atualizado com os módulos Odoo.'),
                'type': 'success',
                'sticky': False,
            }
        }
