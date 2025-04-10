# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
import re
import time
import os

# Configuração avançada de logs
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Campos para descrição semântica
    semantic_description = fields.Text(
        string='Descrição do Produto',
        help='Descreva brevemente o produto para melhorar a busca por IA'
    )
    
    key_features = fields.Text(
        string='Principais Características',
        help='Liste as características mais importantes do produto, uma por linha'
    )
    
    use_cases = fields.Text(
        string='Como Este Produto Pode Ser Usado',
        help='Descreva cenários de uso comuns para este produto, um por linha'
    )
    
    semantic_description_last_update = fields.Datetime(
        string='Última Atualização',
        readonly=True,
        help='Data da última atualização da descrição inteligente'
    )
    
    semantic_description_verified = fields.Boolean(
        string='Descrição Verificada',
        default=False,
        help='Indica se a descrição foi verificada por um humano'
    )
    
    # Campo para tags personalizadas
    product_tags = fields.Char(
        string='Variações e Características Adicionais',
        help='Adicione características como cor, tamanho, material, etc. separadas por vírgula'
    )
    
    # Campo para controle de sincronização com busca vetorial
    semantic_sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('synced', 'Sincronizado'),
        ('needs_update', 'Atualização Necessária')
    ], string='Status de Sincronização', 
       default='not_synced',
       help='Status de sincronização com o sistema de busca inteligente')
    
    semantic_vector_id = fields.Char(
        string='ID do Vetor',
        readonly=True,
        help='ID do vetor no banco de dados de busca'
    )
    
    @api.model
    def generate_semantic_description(self):
        """Gera automaticamente uma descrição inteligente baseada nos metadados do produto."""
        _logger.info(f"Iniciando geração de descrição inteligente para {len(self)} produtos")
        start_time = time.time()
        
        for product in self:
            try:
                _logger.info(f"Processando produto ID {product.id}: {product.name}")
                # Coletar metadados disponíveis
                name = product.name
                category = product.categ_id.name if product.categ_id else ""
                
                # Iniciar a descrição
                description_parts = [f"{name} é um produto da categoria {category}."]
                
                # Adicionar descrição de venda se disponível
                if product.description_sale:
                    # Limpar HTML se presente
                    clean_description = re.sub(r'<.*?>', '', product.description_sale)
                    description_parts.append(clean_description)
                
                # Adicionar informações de preço
                if hasattr(product, 'list_price'):
                    currency_symbol = product.currency_id.symbol if hasattr(product, 'currency_id') else 'R$'
                    description_parts.append(f"Preço de venda: {currency_symbol} {product.list_price:.2f}.")
                
                # Adicionar informações de estoque se disponíveis
                if hasattr(product, 'qty_available') and product.qty_available is not None:
                    status = "Em estoque" if product.qty_available > 0 else "Fora de estoque"
                    description_parts.append(f"Status de estoque: {status}.")
                
                # Adicionar atributos e variantes
                variant_descriptions = []
                for attr_line in product.attribute_line_ids:
                    attr_name = attr_line.attribute_id.name
                    attr_values = ", ".join([v.name for v in attr_line.value_ids])
                    variant_descriptions.append(f"{attr_name}: {attr_values}")
                
                if variant_descriptions:
                    description_parts.append("Disponível com as seguintes variações: " + "; ".join(variant_descriptions) + ".")
                
                # Adicionar tags personalizadas
                if product.product_tags:
                    tags = [tag.strip() for tag in product.product_tags.split(',') if tag.strip()]
                    if tags:
                        description_parts.append("Características adicionais: " + ", ".join(tags) + ".")
                
                # Adicionar código de barras se disponível
                if hasattr(product, 'barcode') and product.barcode:
                    description_parts.append(f"Código de barras: {product.barcode}.")
                
                # Adicionar código interno se disponível
                if product.default_code:
                    description_parts.append(f"Código interno: {product.default_code}.")
                
                # Adicionar unidade de medida
                if hasattr(product, 'uom_id') and product.uom_id:
                    description_parts.append(f"Unidade de medida: {product.uom_id.name}.")
                
                # Adicionar peso se disponível
                if hasattr(product, 'weight') and product.weight:
                    description_parts.append(f"Peso: {product.weight} kg.")
                
                # Adicionar dimensões se disponíveis
                dimensions = []
                if hasattr(product, 'length') and product.length:
                    dimensions.append(f"comprimento: {product.length} cm")
                if hasattr(product, 'width') and product.width:
                    dimensions.append(f"largura: {product.width} cm")
                if hasattr(product, 'height') and product.height:
                    dimensions.append(f"altura: {product.height} cm")
                
                if dimensions:
                    description_parts.append("Dimensões: " + ", ".join(dimensions) + ".")
                
                # Juntar tudo em uma descrição coesa
                semantic_description = " ".join(description_parts)
                
                # Gerar características principais automaticamente
                key_features_list = []
                
                # Adicionar categoria como característica
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
                key_features_text = "\n".join([f"- {feature}" for feature in key_features_list])
                
                # Gerar casos de uso genéricos baseados na categoria
                use_cases_list = []
                if category:
                    if 'móvel' in category.lower() or 'mesa' in category.lower() or 'cadeira' in category.lower():
                        use_cases_list = [
                            "Ideal para decoração de ambientes residenciais",
                            "Perfeito para escritórios e espaços de trabalho",
                            "Ótima opção para ambientes corporativos"
                        ]
                    elif 'roupa' in category.lower() or 'vestuário' in category.lower():
                        use_cases_list = [
                            "Ideal para uso diário",
                            "Perfeito para ocasiões especiais",
                            "Ótima opção para presentes"
                        ]
                    elif 'eletrônico' in category.lower() or 'tecnologia' in category.lower():
                        use_cases_list = [
                            "Ideal para uso profissional",
                            "Perfeito para uso doméstico",
                            "Ótima opção para estudantes"
                        ]
                    else:
                        use_cases_list = [
                            "Ideal para uso diário",
                            "Perfeito para presentes",
                            "Ótima opção para diversos ambientes"
                        ]
                
                # Formatar casos de uso
                use_cases_text = "\n".join([f"- {use_case}" for use_case in use_cases_list])
                
                # Atualizar o produto
                values = {
                    'semantic_description': semantic_description,
                    'semantic_description_last_update': fields.Datetime.now(),
                    'semantic_description_verified': False,
                    'semantic_sync_status': 'needs_update'
                }
                
                # Adicionar características principais apenas se o campo estiver vazio
                if not product.key_features:
                    values['key_features'] = key_features_text
                
                # Adicionar casos de uso apenas se o campo estiver vazio
                if not product.use_cases:
                    values['use_cases'] = use_cases_text
                
                product.write(values)
                
                _logger.info(f"Descrição inteligente gerada com sucesso para o produto {product.id} - {product.name}")
                
            except Exception as e:
                _logger.error(f"Erro ao gerar descrição inteligente para o produto {product.id} - {product.name}: {str(e)}")
        
        # Calcular tempo total de processamento
        elapsed_time = time.time() - start_time
        _logger.info(f"Geração de descrições inteligentes concluída em {elapsed_time:.2f} segundos")
    
    def verify_semantic_description(self):
        """Marca a descrição inteligente como verificada."""
        self.ensure_one()
        self.write({
            'semantic_description_verified': True,
            'semantic_description_last_update': fields.Datetime.now(),
            'semantic_sync_status': 'needs_update'
        })
        _logger.info(f"Descrição inteligente verificada para o produto {self.id} - {self.name}")
    
    def sync_with_ai(self):
        """Marca o produto para sincronização com o sistema de IA."""
        self.ensure_one()
        self.write({
            'semantic_sync_status': 'needs_update'
        })
        _logger.info(f"Produto {self.id} - {self.name} marcado para sincronização com IA")
    
    def fetch_image_online(self):
        """Busca imagem do produto online."""
        self.ensure_one()
        # Esta função será implementada no futuro
        # Por enquanto, apenas registramos a intenção
        _logger.info(f"Solicitação para buscar imagem online para o produto {self.id} - {self.name}")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Busca de Imagem',
                'message': 'Esta funcionalidade será implementada em uma versão futura.',
                'sticky': False,
                'type': 'warning'
            }
        }
    
    def fetch_barcode_info(self):
        """Busca informações do produto a partir do código de barras."""
        self.ensure_one()
        # Esta função será implementada no futuro
        # Por enquanto, apenas registramos a intenção
        _logger.info(f"Solicitação para buscar informações a partir do código de barras para o produto {self.id} - {self.name}")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Busca por Código de Barras',
                'message': 'Esta funcionalidade será implementada em uma versão futura.',
                'sticky': False,
                'type': 'warning'
            }
        }
    
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
    
    @api.model
    def generate_all_semantic_descriptions(self):
        """Gera descrições inteligentes para todos os produtos ativos."""
        _logger.info("Iniciando geração em massa de descrições inteligentes")
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
        _logger.info(f"Geração de descrições inteligentes concluída em {total_time:.2f} segundos")
        _logger.info(f"Resumo: {processed} produtos processados com sucesso, {errors} erros")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Descrições Inteligentes',
                'message': f'Geração concluída para {processed} produtos. {errors} erros encontrados.',
                'sticky': False,
                'type': 'success' if errors == 0 else 'warning'
            }
        }
