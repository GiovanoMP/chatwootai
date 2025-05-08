# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import base64

_logger = logging.getLogger(__name__)

class BusinessSupportDocument(models.Model):
    _name = 'business.support.document'
    _description = 'Documento de Suporte ao Cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Desativar o teste automático de 'active' para este modelo
    # Isso fará com que registros inativos sejam incluídos por padrão
    _active_name = None

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """Sobrescrever método _search para incluir registros inativos por padrão"""
        # Verificar se o contexto já tem active_test definido
        if self._context.get('active_test', True):
            # Criar um novo contexto com active_test=False
            new_context = dict(self._context)
            new_context['active_test'] = False
            self = self.with_context(new_context)

        # Chamar o método original com o novo contexto
        return super(BusinessSupportDocument, self)._search(
            args, offset=offset, limit=limit, order=order,
            count=count, access_rights_uid=access_rights_uid
        )

    name = fields.Char(string='Nome', required=True, tracking=True)
    business_rule_ids = fields.Many2many(
        'business.rules',
        'business_rule_support_doc_rel',
        'document_id',
        'business_rule_id',
        string='Regras de Negócio'
    )

    document_type = fields.Selection([
        ('support', 'Suporte Técnico'),
        ('feedback', 'Feedback'),
        ('question', 'Dúvida'),
        ('suggestion', 'Sugestão'),
        ('other', 'Outro')
    ], string='Tipo de Documento', default='support', required=True, tracking=True)

    content = fields.Text(string='Conteúdo', required=True, tracking=True)

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'business_support_doc_attachment_rel',
        'document_id',
        'attachment_id',
        string='Anexos'
    )

    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Sincronizando...'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro na Sincronização')
    ], string='Status de Sincronização', default='not_synced', tracking=True)

    last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
    vector_id = fields.Char(string='ID do Vetor', readonly=True, help='ID do vetor no banco de dados vetorial')

    active = fields.Boolean(default=True, string='Ativo')
    visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                  help='Se marcado, este documento será incluído no sistema de IA')

    def write(self, vals):
        """Sobrescrever método write para atualizar status de sincronização"""
        # Lista de campos que afetam a sincronização
        sync_fields = [
            'name', 'document_type', 'content', 'business_rule_ids', 'active', 'visible_in_ai'
        ]

        # Se o documento está sendo desativado ou marcado como não visível no IA, marcar para sincronização
        if ('active' in vals and vals['active'] is False) or ('visible_in_ai' in vals and vals['visible_in_ai'] is False):
            action_type = "desativado" if 'active' in vals and vals['active'] is False else "marcado como não visível no IA"
            _logger.info(f"Documento {self.name} (ID: {self.id}) está sendo {action_type}")

            # Não remover das regras de negócio, apenas marcar para sincronização
            for record in self:
                if record.business_rule_ids:
                    _logger.info(f"Marcando regras de negócio associadas ao documento {record.name} (ID: {record.id}) para sincronização")

                    # Para cada regra de negócio, atualizar status de sincronização
                    for business_rule in record.business_rule_ids:
                        # Atualizar status de sincronização da regra de negócio
                        business_rule.write({'sync_status': 'not_synced'})
                        _logger.info(f"Regra de negócio {business_rule.name} (ID: {business_rule.id}) marcada para sincronização")

            # Definir status de sincronização como 'not_synced'
            vals['sync_status'] = 'not_synced'

        # Verificar se algum campo relevante foi alterado
        elif any(field in vals for field in sync_fields):
            # Se o status atual é 'synced', mudar para 'not_synced'
            if self.sync_status == 'synced':
                vals['sync_status'] = 'not_synced'

            # Atualizar o status de sincronização das regras de negócio associadas
            for record in self:
                for business_rule in record.business_rule_ids:
                    if business_rule.sync_status == 'synced':
                        business_rule.write({'sync_status': 'not_synced'})

        return super(BusinessSupportDocument, self).write(vals)

    def action_delete_document(self):
        """Método para excluir permanentemente o documento"""
        self.ensure_one()

        try:
            # Obter informações para log
            doc_name = self.name
            doc_id = self.id

            # Remover o documento das regras de negócio associadas
            if self.business_rule_ids:
                _logger.info(f"Removendo documento {doc_name} (ID: {doc_id}) de {len(self.business_rule_ids)} regras de negócio antes da exclusão")

                # Para cada regra de negócio, remover este documento
                for business_rule in self.business_rule_ids:
                    try:
                        # Usar savepoint para evitar problemas de serialização
                        with self.env.cr.savepoint():
                            # Remover apenas este documento específico
                            business_rule.write({
                                'support_document_ids': [(3, doc_id)]
                            })
                        _logger.info(f"Documento removido da regra de negócio {business_rule.name} (ID: {business_rule.id})")

                        # Atualizar status de sincronização da regra de negócio
                        with self.env.cr.savepoint():
                            business_rule.write({'sync_status': 'not_synced'})
                    except Exception as e:
                        _logger.error(f"Erro ao remover documento da regra de negócio: {e}")

            # Excluir o documento
            self.unlink()

            # Mostrar mensagem de sucesso
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Documento Excluído'),
                    'message': _('O documento foi excluído permanentemente.'),
                    'sticky': False,
                    'type': 'success'
                }
            }
        except Exception as e:
            _logger.error(f"Erro ao excluir documento: {e}")
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

    def unlink(self):
        """Sobrescrever método unlink para remover o documento das regras de negócio antes de excluí-lo"""
        for record in self:
            try:
                # Registrar informações para depuração
                _logger.info(f"Iniciando exclusão permanente do documento {record.name} (ID: {record.id})")

                # 1. Remover das regras de negócio
                if record.business_rule_ids:
                    _logger.info(f"Removendo documento {record.name} (ID: {record.id}) de {len(record.business_rule_ids)} regras de negócio antes da exclusão")

                    # Para cada regra de negócio, remover este documento
                    for business_rule in record.business_rule_ids:
                        try:
                            # Usar savepoint para evitar problemas de serialização
                            with self.env.cr.savepoint():
                                # Remover apenas este documento específico
                                business_rule.write({
                                    'support_document_ids': [(3, record.id)]
                                })
                            _logger.info(f"Documento removido da regra de negócio {business_rule.name} (ID: {business_rule.id})")

                            # Atualizar status de sincronização da regra de negócio
                            with self.env.cr.savepoint():
                                business_rule.write({'sync_status': 'not_synced'})
                        except Exception as e:
                            _logger.error(f"Erro ao remover documento da regra de negócio: {e}")

                # 2. Forçar exclusão do banco de dados usando SQL direto (em último caso)
                # Isso é uma medida extrema para garantir que o documento seja realmente excluído
                try:
                    # Registrar a tentativa de exclusão forçada
                    _logger.info(f"Tentando exclusão forçada do documento {record.name} (ID: {record.id})")

                    # Executar SQL direto para excluir o registro
                    # Isso deve ser usado com cautela, pois ignora as restrições de integridade referencial
                    # Mas como já removemos as referências das regras de negócio, deve ser seguro
                    self.env.cr.execute(f"DELETE FROM business_support_document WHERE id = {record.id}")

                    # Verificar quantas linhas foram afetadas
                    affected_rows = self.env.cr.rowcount
                    _logger.info(f"Exclusão forçada afetou {affected_rows} linhas")

                    # Se a exclusão forçada funcionou, pular a exclusão normal
                    if affected_rows > 0:
                        continue
                except Exception as e:
                    _logger.error(f"Erro na exclusão forçada: {e}")
                    # Continuar com a exclusão normal se a forçada falhar
            except Exception as e:
                _logger.error(f"Erro durante o processo de exclusão: {e}")

        # Chamar o método original para garantir que tudo seja limpo corretamente
        return super(BusinessSupportDocument, self).unlink()

    def action_sync_document(self):
        """Sincronizar documento individual com o sistema de IA"""
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
            # Obter a primeira regra de negócio associada
            business_rule = self.business_rule_ids[0] if self.business_rule_ids else False

            if not business_rule:
                raise UserError(_("Este documento não está associado a nenhuma regra de negócio."))

            # Chamar o método de sincronização da regra de negócio
            result = business_rule._call_mcp_sync_support_docs()

            if result and result.get('success'):
                try:
                    # Usar savepoint para evitar problemas de serialização
                    with self.env.cr.savepoint():
                        self.write({
                            'sync_status': 'synced',
                            'last_sync_date': fields.Datetime.now()
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
                                'sync_status': 'synced',
                                'last_sync_date': fields.Datetime.now()
                            })
                    except Exception as retry_error:
                        _logger.error(f"Falha no retry ao atualizar status: {retry_error}")

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronização Concluída'),
                        'message': _('Documento sincronizado com sucesso.'),
                        'sticky': False,
                        'type': 'success'
                    }
                }
            else:
                error_msg = result.get('error') if result else "Erro desconhecido"
                try:
                    # Usar savepoint para evitar problemas de serialização
                    with self.env.cr.savepoint():
                        self.write({
                            'sync_status': 'error',
                            'last_sync_date': fields.Datetime.now()
                        })
                except Exception as status_error:
                    _logger.error(f"Erro ao atualizar status para 'error': {status_error}")

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
            _logger.error("Erro ao sincronizar documento: %s", str(e))
            try:
                # Usar savepoint para evitar problemas de serialização
                with self.env.cr.savepoint():
                    self.write({
                        'sync_status': 'error',
                        'last_sync_date': fields.Datetime.now()
                    })
            except Exception as status_error:
                _logger.error(f"Erro ao atualizar status para 'error' após exceção: {status_error}")

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
