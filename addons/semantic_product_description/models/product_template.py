# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
import re
import time
import os

# Configuração avançada de logs
_logger = logging.getLogger(__name__)

# Definir um formato mais detalhado para os logs
log_format = '%(asctime)s [%(levelname)s] [%(name)s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

# Verificar se existe um diretório de logs e criar se necessário
log_dir = '/var/log/odoo'
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
    except Exception as e:
        pass  # Ignorar erros de permissão

# Tentar configurar um handler de arquivo para logs específicos do módulo
try:
    file_handler = logging.FileHandler(os.path.join(log_dir, 'semantic_product_description.log'))
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    _logger.addHandler(file_handler)
except Exception as e:
    _logger.warning(f"Não foi possível configurar log em arquivo: {str(e)}")

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos para descrição inteligente
    semantic_description = fields.Text(
        string='Descrição do Produto',
        help='Descrição concisa e estruturada do produto para busca por IA'
    )

    ai_generated_description = fields.Text(
        string='Descrição Gerada por IA',
        help='Descrição gerada automaticamente pela IA com base nos metadados do produto. Você pode editar este texto conforme necessário.'
    )

    key_features = fields.Text(
        string='Principais Características',
        help='Lista de características principais do produto, uma por linha'
    )

    use_cases = fields.Text(
        string='Como Este Produto Pode Ser Usado',
        help='Cenários de uso comuns para este produto, uma por linha'
    )

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

    # Campo adicional para tags personalizadas
    product_tags = fields.Char(
        string='Tags do Produto',
        help='Tags separadas por vírgula (ex: pequeno, vermelho, promoção)'
    )

    # Campo para controle de sincronização com busca vetorial
    semantic_sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('synced', 'Sincronizado'),
        ('needs_update', 'Atualização Necessária')
    ], string='Status de Sincronização',
       default='not_synced',
       help='Status de sincronização com o sistema de busca vetorial')

    semantic_vector_id = fields.Char(
        string='ID do Vetor',
        readonly=True,
        help='ID do vetor no banco de dados vetorial'
    )

    @api.model
    def generate_semantic_description(self):
        """Gera automaticamente uma descrição inteligente baseada nos metadados do produto usando IA."""
        _logger.info(f"Iniciando geração de descrição inteligente para {len(self)} produtos")
        start_time = time.time()

        for product in self:
            try:
                _logger.info(f"Processando produto ID {product.id}: {product.name}")

                # Chamar o MCP-Odoo para gerar a descrição
                description = self._call_mcp_generate_description(product.id)

                if description:
                    # Gerar características principais automaticamente se o campo estiver vazio
                    key_features_text = None
                    if not product.key_features:
                        key_features_text = self._generate_key_features(product)

                    # Atualizar o produto
                    values = {
                        'ai_generated_description': description,
                        'semantic_description_last_update': fields.Datetime.now(),
                        'semantic_description_verified': False,
                        'semantic_sync_status': 'needs_update'
                    }

                    # Adicionar características principais apenas se o campo estiver vazio
                    if key_features_text:
                        values['key_features'] = key_features_text

                    product.write(values)
                    _logger.info(f"Descrição semântica gerada com sucesso para o produto {product.id} - {product.name}")
                else:
                    _logger.warning(f"Não foi possível gerar descrição para o produto {product.id} - {product.name}")

            except Exception as e:
                _logger.error(f"Erro ao gerar descrição semântica para o produto {product.id} - {product.name}: {str(e)}")

        # Calcular tempo total de processamento
        elapsed_time = time.time() - start_time
        _logger.info(f"Geração de descrições semânticas concluída em {elapsed_time:.2f} segundos")

    def _call_mcp_generate_description(self, product_id):
        """Chama o MCP-Odoo para gerar uma descrição para o produto."""
        try:
            import requests
            import json

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
                'product_id': product_id
            }

            # Fazer a requisição ao MCP-Odoo
            _logger.info(f"Chamando MCP-Odoo para gerar descrição para o produto {product_id}")
            response = requests.post(
                f"{mcp_url}/tools/generate_product_description",
                headers=headers,
                json=payload,
                timeout=30  # Timeout de 30 segundos
            )

            # Verificar resposta
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('description')
                else:
                    _logger.error(f"Erro do MCP-Odoo: {result.get('error')}")
            else:
                _logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")

            return None
        except Exception as e:
            _logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
            return None

    def _generate_key_features(self, product):
        """Gera características principais automaticamente."""
        key_features_list = []

        # Adicionar categoria como característica
        category = product.categ_id.name if product.categ_id else ""
        if category:
            key_features_list.append(f"Categoria: {category}")

        # Adicionar preço como característica
        if hasattr(product, 'list_price'):
            currency_symbol = product.currency_id.symbol if hasattr(product, 'currency_id') else 'R$'
            key_features_list.append(f"Preço: {currency_symbol} {product.list_price:.2f}")

        # Adicionar disponibilidade como característica
        if hasattr(product, 'qty_available') and product.qty_available is not None:
            status = "Em estoque" if product.qty_available > 0 else "Fora de estoque"
            key_features_list.append(f"Disponibilidade: {status}")

        # Adicionar peso como característica
        if hasattr(product, 'weight') and product.weight:
            key_features_list.append(f"Peso: {product.weight} kg")

        # Adicionar variantes como características
        for attr_line in product.attribute_line_ids:
            attr_name = attr_line.attribute_id.name
            attr_values = ", ".join([v.name for v in attr_line.value_ids])
            key_features_list.append(f"{attr_name}: {attr_values}")

        # Formatar características principais
        return "\n".join([f"- {feature}" for feature in key_features_list])

    def verify_semantic_description(self):
        """Marca a descrição semântica como verificada."""
        self.ensure_one()
        self.write({
            'semantic_description_verified': True,
            'semantic_description_last_update': fields.Datetime.now(),
            'semantic_sync_status': 'needs_update'
        })
        _logger.info(f"Descrição semântica verificada para o produto {self.id} - {self.name}")

    def sync_with_ai(self):
        """Sincroniza o produto com o sistema de IA."""
        self.ensure_one()
        try:
            # Marcar como verificado
            self.write({
                'semantic_description_verified': True,
                'semantic_description_last_update': fields.Datetime.now()
            })

            # Chamar o MCP-Odoo para sincronizar
            result = self._call_mcp_sync_product(self.id)

            if result and result.get('success'):
                # Atualizar o ID do vetor
                self.write({
                    'semantic_vector_id': result.get('vector_id'),
                    'semantic_sync_status': 'synced'
                })
                _logger.info(f"Produto {self.id} - {self.name} sincronizado com sucesso")
                return True
            else:
                error_msg = result.get('error') if result else "Erro desconhecido"
                _logger.error(f"Erro ao sincronizar produto {self.id} - {self.name}: {error_msg}")
                self.write({'semantic_sync_status': 'needs_update'})
                return False
        except Exception as e:
            _logger.error(f"Exceção ao sincronizar produto {self.id} - {self.name}: {str(e)}")
            self.write({'semantic_sync_status': 'needs_update'})
            return False

    def _call_mcp_sync_product(self, product_id):
        """Chama o MCP-Odoo para sincronizar um produto com o banco de dados vetorial."""
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
                'description': self.ai_generated_description or self.semantic_description
            }

            # Fazer a requisição ao MCP-Odoo
            _logger.info(f"Chamando MCP-Odoo para sincronizar produto {product_id}")
            response = requests.post(
                f"{mcp_url}/tools/sync_product_to_vector_db",
                headers=headers,
                json=payload,
                timeout=30  # Timeout de 30 segundos
            )

            # Verificar resposta
            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            _logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
            return None

    def get_tags_list(self):
        """Retorna lista de tags do produto."""
        self.ensure_one()
        if not self.product_tags:
            return []
        return [tag.strip() for tag in self.product_tags.split(',') if tag.strip()]

    def get_key_features_list(self):
        """Retorna lista de características principais do produto."""
        self.ensure_one()
        if not self.key_features:
            return []

        features = []
        for line in self.key_features.split('\n'):
            # Remover marcadores de lista e espaços em branco
            clean_line = re.sub(r'^[\s\-\*•]+', '', line).strip()
            if clean_line:
                features.append(clean_line)

        return features

    def get_use_cases_list(self):
        """Retorna lista de casos de uso do produto."""
        self.ensure_one()
        if not self.use_cases:
            return []

        cases = []
        for line in self.use_cases.split('\n'):
            # Remover marcadores de lista e espaços em branco
            clean_line = re.sub(r'^[\s\-\*•]+', '', line).strip()
            if clean_line:
                cases.append(clean_line)

        return cases

    def get_semantic_metadata(self):
        """
        Retorna todos os metadados semânticos do produto em um formato estruturado,
        adequado para indexação em banco de dados vetorial.
        """
        self.ensure_one()

        metadata = {
            'id': self.id,
            'name': self.name,
            'semantic_description': self.semantic_description or '',
            'key_features': self.get_key_features_list(),
            'use_cases': self.get_use_cases_list(),
            'tags': self.get_tags_list(),
            'verified': self.semantic_description_verified,
            'last_update': self.semantic_description_last_update and fields.Datetime.to_string(self.semantic_description_last_update) or '',
            'category_id': self.categ_id.id if self.categ_id else None,
            'category_name': self.categ_id.name if self.categ_id else '',
            'list_price': float(self.list_price) if hasattr(self, 'list_price') else 0.0,
            'currency': self.currency_id.name if hasattr(self, 'currency_id') else 'BRL',
            'default_code': self.default_code or '',
            'barcode': self.barcode if hasattr(self, 'barcode') else '',
            'active': self.active,
            'sale_ok': self.sale_ok,
            'purchase_ok': self.purchase_ok,
            'description_sale': self.description_sale or '',
            'type': self.type,
            'uom_name': self.uom_id.name if hasattr(self, 'uom_id') else '',
            'weight': float(self.weight) if hasattr(self, 'weight') else 0.0,
        }

        # Adicionar atributos e variantes
        metadata['attributes'] = []
        for attr_line in self.attribute_line_ids:
            attr_values = [{'id': v.id, 'name': v.name} for v in attr_line.value_ids]
            metadata['attributes'].append({
                'attribute_id': attr_line.attribute_id.id,
                'attribute_name': attr_line.attribute_id.name,
                'values': attr_values
            })

        # Adicionar variantes
        metadata['variants'] = []
        for variant in self.product_variant_ids:
            variant_data = {
                'id': variant.id,
                'name': variant.name,
                'default_code': variant.default_code or '',
                'barcode': variant.barcode if hasattr(variant, 'barcode') else '',
                'combination': []
            }

            # Adicionar combinação de atributos
            if hasattr(variant, 'attribute_value_ids'):
                for attr_val in variant.attribute_value_ids:
                    variant_data['combination'].append({
                        'attribute_id': attr_val.attribute_id.id,
                        'attribute_name': attr_val.attribute_id.name,
                        'value_id': attr_val.id,
                        'value_name': attr_val.name
                    })

            metadata['variants'].append(variant_data)

        return metadata

    @api.model
    def generate_all_semantic_descriptions(self):
        """Gera descrições semânticas para todos os produtos ativos."""
        _logger.info("Iniciando geração em massa de descrições semânticas")
        start_time = time.time()

        # Buscar produtos ativos
        products = self.search([('active', '=', True)])
        count = len(products)
        _logger.info(f"Encontrados {count} produtos ativos para processamento")

        # Processar produtos em lotes
        processed = 0
        errors = 0

        for i, product in enumerate(products, 1):
            try:
                _logger.debug(f"Processando produto {i}/{count}: {product.name} (ID: {product.id})")
                product.generate_semantic_description()
                processed += 1

                # Log de progresso a cada 10 produtos ou 10%
                log_interval = max(10, int(count * 0.1))
                if i % log_interval == 0 or i == count:
                    elapsed = time.time() - start_time
                    eta = (elapsed / i) * (count - i) if i > 0 else 0
                    _logger.info(f"Progresso: {i}/{count} produtos processados ({(i/count)*100:.1f}%) - Tempo decorrido: {elapsed:.1f}s - ETA: {eta:.1f}s")
            except Exception as e:
                errors += 1
                _logger.error(f"Erro ao processar produto {product.id}: {str(e)}")

        # Resumo final
        total_time = time.time() - start_time
        _logger.info(f"Geração de descrições semânticas concluída em {total_time:.2f} segundos")
        _logger.info(f"Resumo: {processed} produtos processados com sucesso, {errors} erros")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Descrições Semânticas',
                'message': f'Geração concluída para {count} produtos.',
                'sticky': False,
                'type': 'success'
            }
        }
