# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SpecialPhone(models.Model):
    _name = 'company.services.special.phone'
    _description = 'Números de Telefone Especiais'
    _order = 'name'

    name = fields.Char(
        string='Nome',
        required=True,
        help="Nome da pessoa ou departamento associado a este número"
    )
    
    phone_number = fields.Char(
        string='Número de Telefone',
        required=True,
        help="Número de telefone no formato internacional (ex: +5511999999999)"
    )
    
    # Permissões especiais
    allow_erp_support = fields.Boolean(
        string='Suporte ao ERP',
        default=False,
        help="Permite que este número receba suporte técnico sobre o ERP"
    )
    
    notes = fields.Text(
        string='Observações',
        help="Observações adicionais sobre este número especial"
    )
    
    _sql_constraints = [
        ('phone_number_uniq', 'unique(phone_number)', 
         'O número de telefone deve ser único!')
    ]
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.phone_number})"
            result.append((record.id, name))
        return result
