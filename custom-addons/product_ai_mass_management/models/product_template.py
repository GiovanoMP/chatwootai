# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campo para prioridade do produto
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Favorito'),
    ], default='0', string='Favorito', help='Determina a prioridade do produto')

    # Campo para preço específico no sistema de IA
    ai_price = fields.Float(
        string='Preço no Sistema de IA',
        digits='Product Price',
        help='Preço a ser usado no sistema de IA. Se não definido, será usado o preço padrão do produto.'
    )

    ai_price_difference = fields.Float(
        string='Diferença de Preço (%)',
        compute='_compute_price_difference',
        store=True,
        help='Diferença percentual entre o preço padrão e o preço no sistema de IA.'
    )

    # Campos para controle de sincronização
    semantic_sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Sincronizando'),
        ('synced', 'Sincronizado'),
        ('needs_update', 'Atualização Necessária')
    ], string='Status de Sincronização',
       default='not_synced',
       help='Status de sincronização com o sistema de busca vetorial')

    semantic_description_last_update = fields.Datetime(
        string='Última Atualização',
        readonly=True,
        help='Data da última atualização da descrição semântica'
    )

    semantic_description_verified = fields.Boolean(
        string='Descrição Verificada',
        default=False,
        help='Indica se a descrição semântica foi verificada por um humano'
    )

    # Campo para qualidade da descrição
    ai_description_quality = fields.Selection([
        ('none', 'Sem Descrição'),
        ('generated', 'Gerada (Não Verificada)'),
        ('verified', 'Verificada')
    ], string='Qualidade da Descrição',
       compute='_compute_description_quality',
       store=True,
       help='Indica a qualidade da descrição no sistema de IA')

    # Campo para status do preço
    ai_price_status = fields.Selection([
        ('none', 'Sem Preço IA'),
        ('default', 'Igual ao Padrão'),
        ('custom', 'Preço Personalizado')
    ], string='Status do Preço',
       compute='_compute_price_status',
       store=True,
       help='Indica o status do preço no sistema de IA')

    # Campo para popularidade no sistema de IA
    ai_popularity = fields.Selection([
        ('new', 'Novo no Sistema'),
        ('low', 'Baixa Popularidade'),
        ('medium', 'Média Popularidade'),
        ('high', 'Alta Popularidade')
    ], string='Popularidade no Sistema de IA',
       default='new',
       help='Indica a popularidade do produto nas buscas do sistema de IA')

    @api.depends('list_price', 'ai_price')
    def _compute_price_difference(self):
        for product in self:
            if product.list_price and product.ai_price:
                product.ai_price_difference = ((product.ai_price - product.list_price) / product.list_price) * 100
            else:
                product.ai_price_difference = 0

    @api.depends('semantic_description_verified', 'semantic_description')
    def _compute_description_quality(self):
        for product in self:
            if product.semantic_description_verified:
                product.ai_description_quality = 'verified'
            elif product.semantic_description:
                product.ai_description_quality = 'generated'
            else:
                product.ai_description_quality = 'none'

    @api.depends('list_price', 'ai_price')
    def _compute_price_status(self):
        for product in self:
            if not product.ai_price:
                product.ai_price_status = 'none'
            elif abs(product.ai_price - product.list_price) < 0.01:  # Considera igual se a diferença for menor que 1 centavo
                product.ai_price_status = 'default'
            else:
                product.ai_price_status = 'custom'

    # Os demais campos já estão definidos no módulo semantic_product_description

    def action_view_product(self):
        """Abre o formulário do produto para visualização/edição."""
        self.ensure_one()
        return {
            'name': 'Produto',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def sync_with_ai_mass(self):
        """Sincroniza múltiplos produtos com IA de forma inteligente."""
        # Contador para notificação
        success_count = 0
        error_count = 0

        for product in self:
            try:
                # Se já tem descrição enriquecida, usa ela
                if hasattr(product, 'ai_generated_description') and product.ai_generated_description:
                    if hasattr(product, 'sync_with_ai'):
                        product.sync_with_ai()
                else:
                    # Caso contrário, usa sincronização básica
                    minimal_text = f"{product.name} - {product.categ_id.name}"

                    # Preparar payload com preço específico para IA se disponível
                    price = product.ai_price if hasattr(product, 'ai_price') and product.ai_price else product.list_price

                    # Chamar método de sincronização com preço específico
                    self._call_mcp_sync_product_minimal(product.id, minimal_text, price)

                # Atualizar status visual
                if hasattr(product, 'semantic_sync_status'):
                    product.write({
                        'semantic_sync_status': 'synced',
                        'semantic_description_last_update': fields.Datetime.now()
                    })

                _logger.info(f"Produto {product.id} - {product.name} sincronizado com sucesso")
                success_count += 1
            except Exception as e:
                _logger.error(f"Erro ao sincronizar produto {product.id} - {product.name}: {str(e)}")
                error_count += 1

        # Mensagem de resultado
        message = f'{success_count} produtos sincronizados com sucesso.'
        if error_count > 0:
            message += f' {error_count} produtos com erro.'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronização Concluída',
                'message': message,
                'sticky': False,
                'type': 'success' if error_count == 0 else 'warning'
            }
        }

    def generate_descriptions_mass(self):
        """Gera descrições semânticas para múltiplos produtos."""
        # Contador para notificação
        success_count = 0
        error_count = 0

        for product in self:
            try:
                # Obter metadados do produto
                metadata = self._get_product_metadata(product)

                # Chamar o MCP para gerar descrição
                result = self._call_mcp_generate_description(product.id, metadata)

                if result and result.get('description'):
                    # Atualizar a descrição do produto
                    update_vals = {
                        'semantic_description_verified': False,
                        'semantic_sync_status': 'needs_update',
                        'semantic_description_last_update': fields.Datetime.now()
                    }

                    if hasattr(product, 'ai_generated_description'):
                        update_vals['ai_generated_description'] = result.get('description')

                    product.write(update_vals)
                    success_count += 1
                else:
                    error_count += 1

            except Exception as e:
                _logger.error(f"Erro ao gerar descrição para produto {product.id} - {product.name}: {str(e)}")
                error_count += 1

        # Mensagem de resultado
        message = f'{success_count} descrições geradas com sucesso.'
        if error_count > 0:
            message += f' {error_count} produtos com erro.'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Geração de Descrições Concluída',
                'message': message,
                'sticky': False,
                'type': 'success' if error_count == 0 else 'warning'
            }
        }

    def _get_product_metadata(self, product):
        """Extrai metadados do produto para geração de descrição."""
        metadata = {
            'name': product.name,
            'category': product.categ_id.name,
            'price': product.ai_price if hasattr(product, 'ai_price') and product.ai_price else product.list_price,
            'default_code': product.default_code or '',
            'barcode': product.barcode or '',
        }

        # Adicionar atributos se disponíveis
        if hasattr(product, 'attribute_line_ids'):
            attributes = []
            for attr_line in product.attribute_line_ids:
                attr_values = [v.name for v in attr_line.value_ids]
                attributes.append({
                    'name': attr_line.attribute_id.name,
                    'values': attr_values
                })
            metadata['attributes'] = attributes

        # Adicionar descrição existente se disponível
        if product.description or product.description_sale:
            metadata['description'] = product.description or product.description_sale

        return metadata

    def _get_mcp_credentials(self):
        """Obter credenciais do MCP-Odoo do módulo ai_credentials_manager ou dos parâmetros do sistema."""
        # Verificar se o módulo ai_credentials_manager está instalado
        if not self.env['ir.module.module'].sudo().search([('name', '=', 'ai_credentials_manager'), ('state', '=', 'installed')]):
            # Fallback para o método antigo se o módulo não estiver instalado
            mcp_url = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.url', 'http://localhost:8000')
            mcp_token = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.token', '')
            account_id = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.account_id', 'account_2')
            return mcp_url, mcp_token, account_id

        # Obter credenciais do módulo ai_credentials_manager
        try:
            # Obter o account_id baseado no ID da empresa atual
            company_id = self.env.company.id
            account_id = f"account_{company_id}"

            # Buscar credenciais para este account_id
            credentials = self.env['ai.system.credentials'].sudo().search([('account_id', '=', account_id)], limit=1)

            if credentials:
                # Registrar acesso às credenciais
                self.env['ai.credentials.access.log'].sudo().create({
                    'credential_id': credentials.id,
                    'access_time': fields.Datetime.now(),
                    'user_id': self.env.user.id,
                    'ip_address': self.env.context.get('remote_addr', 'N/A'),
                    'operation': 'get_mcp_credentials',
                    'success': True
                })

                # Obter URL do sistema de IA e token
                mcp_url = credentials.get_ai_system_url()
                mcp_token = credentials.token

                return mcp_url, mcp_token, account_id
            else:
                _logger.warning(f"Credenciais não encontradas para account_id {account_id}")
        except Exception as e:
            _logger.error(f"Erro ao obter credenciais do ai_credentials_manager: {str(e)}")

        # Fallback para o método antigo em caso de erro
        mcp_url = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.url', 'http://localhost:8000')
        mcp_token = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.token', '')
        account_id = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.account_id', 'account_2')
        return mcp_url, mcp_token, account_id

    def _call_mcp_generate_description(self, product_id, metadata):
        """Chama o MCP-Odoo para gerar uma descrição semântica."""
        try:
            import requests

            # Obter configurações do MCP-Odoo
            mcp_url, mcp_token, account_id = self._get_mcp_credentials()

            # Preparar a requisição
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
            }

            payload = {
                'account_id': account_id,
                'product_id': product_id,
                'metadata': metadata
            }

            # Fazer a requisição ao MCP-Odoo
            _logger.info(f"Chamando MCP-Odoo para gerar descrição para produto {product_id}")
            response = requests.post(
                f"{mcp_url}/tools/generate_product_description",
                headers=headers,
                json=payload,
                timeout=60  # Timeout de 60 segundos (geração pode demorar mais)
            )

            # Verificar resposta
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result
                else:
                    _logger.error(f"Erro do MCP-Odoo: {result.get('error')}")
            else:
                _logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")

            return None
        except Exception as e:
            _logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
            return None

    def _call_mcp_sync_product_minimal(self, product_id, minimal_text, price=None):
        """Chama o MCP-Odoo para sincronizar um produto com descrição mínima."""
        try:
            import requests

            # Obter configurações do MCP-Odoo
            mcp_url = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.url', 'http://localhost:8000')
            mcp_token = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.token', '')
            account_id = self.env['ir.config_parameter'].sudo().get_param('mcp_odoo.account_id', 'account_2')

            # Preparar a requisição
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
            }

            payload = {
                'account_id': account_id,
                'product_id': product_id,
                'description': minimal_text,
                'is_minimal': True
            }

            # Adicionar preço se fornecido
            if price is not None:
                payload['price'] = price
                payload['is_special_price'] = hasattr(self, 'ai_price') and bool(self.ai_price)

            # Fazer a requisição ao MCP-Odoo
            _logger.info(f"Chamando MCP-Odoo para sincronizar produto {product_id} com descrição mínima")
            response = requests.post(
                f"{mcp_url}/tools/sync_product_to_vector_db",
                headers=headers,
                json=payload,
                timeout=30  # Timeout de 30 segundos
            )

            # Verificar resposta
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Atualizar ID do vetor se o campo existir
                    if hasattr(self, 'semantic_vector_id'):
                        self.write({
                            'semantic_vector_id': result.get('vector_id'),
                            'semantic_sync_status': 'synced'
                        })
                    return True
                else:
                    _logger.error(f"Erro do MCP-Odoo: {result.get('error')}")
            else:
                _logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")

            return False
        except Exception as e:
            _logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
            return False
