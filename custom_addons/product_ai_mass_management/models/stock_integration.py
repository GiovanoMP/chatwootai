# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import base64
import csv
import io
import xlrd
from datetime import datetime

_logger = logging.getLogger(__name__)

class StockIntegration(models.AbstractModel):
    _name = 'product.stock.integration'
    _description = 'Integração com Estoque'
    
    @api.model
    def _get_or_create_ai_channel(self):
        """Obtém ou cria o canal de IA padrão."""
        ai_channel = self.env['product.sales.channel'].search([('code', '=', 'ai_system')], limit=1)
        if not ai_channel:
            ai_channel = self.env['product.sales.channel'].create({
                'name': 'Sistema de IA',
                'code': 'ai_system',
                'active': True,
                'description': 'Canal para integração com sistema de IA'
            })
            _logger.info(f"Canal de IA criado com ID {ai_channel.id}")
        return ai_channel
        
    @api.model
    def auto_sync_new_products(self, product):
        """Sincroniza automaticamente novos produtos do estoque para o sistema de gestão."""
        try:
            # Verificar se o produto já está em algum canal
            if not product.channel_mapping_ids:
                # Obter canal de IA (criar se não existir)
                ai_channel = self._get_or_create_ai_channel()
                
                # Criar mapeamento para o canal de IA
                self.env['product.channel.mapping'].create({
                    'product_id': product.id,
                    'channel_id': ai_channel.id,
                    'specific_price': product.list_price,
                    'use_specific_price': False,
                    'sync_status': 'not_synced'
                })
                
                # Atualizar data de importação
                product.write({
                    'last_import_date': fields.Datetime.now()
                })
                
                _logger.info(f"Produto {product.id} - {product.name} sincronizado automaticamente do estoque")
                
                # Sincronizar com o sistema de IA se configurado
                if hasattr(product, 'sync_with_ai'):
                    product.sync_with_ai()
                
            return True
        except Exception as e:
            _logger.error(f"Erro ao sincronizar automaticamente produto {product.id} - {product.name}: {str(e)}")
            return False

    @api.model
    def sync_from_stock(self, product_ids=None):
        """
        Sincroniza produtos do estoque para o sistema de gestão.
        Se product_ids for fornecido, sincroniza apenas esses produtos.
        Caso contrário, sincroniza todos os produtos ativos no estoque.
        """
        domain = [('active', '=', True)]
        if product_ids:
            domain.append(('id', 'in', product_ids))
        
        products = self.env['product.template'].search(domain)
        
        # Contador para notificação
        success_count = 0
        error_count = 0
        
        for product in products:
            try:
                # Verificar se o produto já está em algum canal
                if not product.channel_mapping_ids:
                    # Obter canal de IA (criar se não existir)
                    ai_channel = self._get_or_create_ai_channel()
                    
                    # Criar mapeamento para o canal de IA
                    self.env['product.channel.mapping'].create({
                        'product_id': product.id,
                        'channel_id': ai_channel.id,
                        'specific_price': product.list_price,
                        'use_specific_price': False,
                        'sync_status': 'not_synced'
                    })
                
                # Atualizar data de importação
                product.write({
                    'last_import_date': fields.Datetime.now()
                })
                
                success_count += 1
                _logger.info(f"Produto {product.id} - {product.name} importado do estoque com sucesso")
            except Exception as e:
                error_count += 1
                _logger.error(f"Erro ao importar produto {product.id} - {product.name} do estoque: {str(e)}")
        
        # Mensagem de resultado
        message = f'{success_count} produtos importados do estoque com sucesso.'
        if error_count > 0:
            message += f' {error_count} produtos com erro.'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Importação do Estoque Concluída',
                'message': message,
                'sticky': False,
                'type': 'success' if error_count == 0 else 'warning'
            }
        }
    
    @api.model
    def sync_to_stock(self, product_ids=None):
        """
        Sincroniza produtos do sistema de gestão para o estoque.
        Se product_ids for fornecido, sincroniza apenas esses produtos.
        Caso contrário, sincroniza todos os produtos com canais.
        """
        domain = [('channel_count', '>', 0)]
        if product_ids:
            domain.append(('id', 'in', product_ids))
        
        products = self.env['product.template'].search(domain)
        
        # Contador para notificação
        success_count = 0
        error_count = 0
        
        for product in products:
            try:
                # Obter preço do canal de IA se disponível
                ai_channel = self._get_or_create_ai_channel()
                ai_mapping = self.env['product.channel.mapping'].search([
                    ('product_id', '=', product.id),
                    ('channel_id', '=', ai_channel.id)
                ], limit=1)
                
                # Atualizar preço no estoque se necessário
                if ai_mapping and ai_mapping.use_specific_price and ai_mapping.specific_price != product.list_price:
                    product.write({
                        'list_price': ai_mapping.specific_price
                    })
                
                # Atualizar data de exportação
                product.write({
                    'last_export_date': fields.Datetime.now()
                })
                
                success_count += 1
                _logger.info(f"Produto {product.id} - {product.name} exportado para o estoque com sucesso")
            except Exception as e:
                error_count += 1
                _logger.error(f"Erro ao exportar produto {product.id} - {product.name} para o estoque: {str(e)}")
        
        # Mensagem de resultado
        message = f'{success_count} produtos exportados para o estoque com sucesso.'
        if error_count > 0:
            message += f' {error_count} produtos com erro.'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Exportação para o Estoque Concluída',
                'message': message,
                'sticky': False,
                'type': 'success' if error_count == 0 else 'warning'
            }
        }
    
    @api.model
    def import_from_stock_file(self, file_data, file_format='excel'):
        """Importa produtos de um arquivo Excel ou JSON para o estoque e sistema de gestão."""
        # Delegar a importação para o novo método
        return self.import_from_file(file_data, file_format)
        
    @api.model
    def import_from_file(self, file_data, file_format, update_existing=True, create_categories=True):
        """Importa produtos de um arquivo Excel ou JSON."""
        try:
            # Delegar a importação para o wizard
            wizard = self.env['stock.import.wizard'].create({
                'file_format': file_format,
                'import_file': file_data,
                'update_existing': update_existing,
                'create_categories': create_categories
            })
            
            return wizard.action_import()
        
        except Exception as e:
            _logger.error(f"Erro ao importar produtos de arquivo: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro na Importação'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
        
    @api.model
    def import_from_stock_file_original(self, file_data, file_format='csv'):
        """
        Importa produtos de um arquivo CSV ou Excel para o estoque e sistema de gestão.
        """
        # Decodificar arquivo
        data = base64.b64decode(file_data)
        
        # Contador para notificação
        total_rows = 0
        processed_rows = 0
        success_rows = 0
        error_rows = 0
        
        # Log de importação
        log_lines = []
        log_lines.append(f"Iniciando importação em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        try:
            # Processar arquivo CSV
            if file_format == 'csv':
                result = self._process_import_csv(data, log_lines)
            # Processar arquivo Excel
            else:
                result = self._process_import_excel(data, log_lines)
            
            total_rows = result.get('total_rows', 0)
            processed_rows = result.get('processed_rows', 0)
            success_rows = result.get('success_rows', 0)
            error_rows = result.get('error_rows', 0)
            
            # Atualizar log
            log_lines.append(f"Importação concluída em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            log_lines.append(f"Total de linhas: {total_rows}")
            log_lines.append(f"Linhas processadas: {processed_rows}")
            log_lines.append(f"Sucessos: {success_rows}")
            log_lines.append(f"Erros: {error_rows}")
            
            # Mensagem de resultado
            message = f'{success_rows} produtos importados com sucesso.'
            if error_rows > 0:
                message += f' {error_rows} produtos com erro.'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Importação Concluída',
                    'message': message,
                    'sticky': False,
                    'type': 'success' if error_rows == 0 else 'warning'
                }
            }
            
        except Exception as e:
            log_lines.append(f"Erro fatal: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erro na Importação',
                    'message': f'Erro ao importar arquivo: {str(e)}',
                    'sticky': False,
                    'type': 'danger'
                }
            }
    
    def _process_import_csv(self, data, log_lines):
        """Processa a importação de um arquivo CSV."""
        # Decodificar dados CSV
        file_input = io.StringIO(data.decode('utf-8'))
        reader = csv.reader(file_input, delimiter=',', quotechar='"')
        
        # Ler cabeçalho
        header = next(reader)
        
        # Contar linhas
        file_input.seek(0)
        total_rows = sum(1 for _ in reader) - 1  # Subtrair cabeçalho
        
        # Voltar ao início e pular cabeçalho
        file_input.seek(0)
        next(reader)
        
        # Mapear colunas
        column_mapping = self._get_column_mapping(header)
        
        # Contadores
        processed_rows = 0
        success_rows = 0
        error_rows = 0
        
        # Obter canal de IA
        ai_channel = self._get_or_create_ai_channel()
        
        # Processar linhas
        for row_num, row in enumerate(reader, start=2):  # Começar de 2 para contar o cabeçalho
            try:
                # Preparar valores
                vals = {}
                for field, col_idx in column_mapping.items():
                    if col_idx >= 0 and col_idx < len(row):
                        vals[field] = row[col_idx]
                
                # Criar ou atualizar produto
                product = self._create_or_update_product(vals)
                
                # Criar mapeamento para o canal de IA se não existir
                if product:
                    self._ensure_channel_mapping(product, ai_channel, vals)
                    success_rows += 1
                
            except Exception as e:
                log_lines.append(f"Erro na linha {row_num}: {str(e)}")
                error_rows += 1
            
            processed_rows += 1
        
        return {
            'total_rows': total_rows,
            'processed_rows': processed_rows,
            'success_rows': success_rows,
            'error_rows': error_rows
        }
    
    def _process_import_excel(self, data, log_lines):
        """Processa a importação de um arquivo Excel."""
        # Ler arquivo Excel
        book = xlrd.open_workbook(file_contents=data)
        sheet = book.sheet_by_index(0)
        
        # Ler cabeçalho
        header = [sheet.cell_value(0, col) for col in range(sheet.ncols)]
        total_rows = sheet.nrows - 1  # Subtrair cabeçalho
        
        # Mapear colunas
        column_mapping = self._get_column_mapping(header)
        
        # Contadores
        processed_rows = 0
        success_rows = 0
        error_rows = 0
        
        # Obter canal de IA
        ai_channel = self._get_or_create_ai_channel()
        
        # Processar linhas
        for row_num in range(1, sheet.nrows):  # Começar de 1 para pular o cabeçalho
            try:
                # Preparar valores
                vals = {}
                for field, col_idx in column_mapping.items():
                    if col_idx >= 0 and col_idx < sheet.ncols:
                        vals[field] = sheet.cell_value(row_num, col_idx)
                
                # Criar ou atualizar produto
                product = self._create_or_update_product(vals)
                
                # Criar mapeamento para o canal de IA se não existir
                if product:
                    self._ensure_channel_mapping(product, ai_channel, vals)
                    success_rows += 1
                
            except Exception as e:
                log_lines.append(f"Erro na linha {row_num + 1}: {str(e)}")
                error_rows += 1
            
            processed_rows += 1
        
        return {
            'total_rows': total_rows,
            'processed_rows': processed_rows,
            'success_rows': success_rows,
            'error_rows': error_rows
        }
    
    def _get_column_mapping(self, header):
        """Mapeia as colunas do arquivo para os campos do modelo."""
        # Mapeamento padrão de colunas
        mapping = {
            'default_code': -1,
            'name': -1,
            'list_price': -1,
            'standard_price': -1,
            'barcode': -1,
            'categ_id': -1,
            'type': -1,
            'uom_id': -1,
            'description': -1,
            'description_sale': -1,
            'weight': -1,
            'volume': -1,
            'sale_ok': -1,
            'purchase_ok': -1,
            'active': -1,
            'channel_price': -1,
        }
        
        # Mapear colunas do arquivo para campos do modelo
        for col_idx, col_name in enumerate(header):
            col_name = col_name.strip().lower()
            
            if col_name in ('default_code', 'código', 'code', 'sku', 'referência', 'reference'):
                mapping['default_code'] = col_idx
            elif col_name in ('name', 'nome', 'produto', 'product'):
                mapping['name'] = col_idx
            elif col_name in ('list_price', 'preço de venda', 'preço', 'price', 'sales price'):
                mapping['list_price'] = col_idx
            elif col_name in ('standard_price', 'custo', 'cost', 'preço de custo'):
                mapping['standard_price'] = col_idx
            elif col_name in ('barcode', 'código de barras', 'ean13', 'upc'):
                mapping['barcode'] = col_idx
            elif col_name in ('categ_id', 'categoria', 'category'):
                mapping['categ_id'] = col_idx
            elif col_name in ('type', 'tipo'):
                mapping['type'] = col_idx
            elif col_name in ('uom_id', 'unidade', 'unit', 'uom'):
                mapping['uom_id'] = col_idx
            elif col_name in ('description', 'descrição', 'desc'):
                mapping['description'] = col_idx
            elif col_name in ('description_sale', 'descrição de venda', 'sales description'):
                mapping['description_sale'] = col_idx
            elif col_name in ('weight', 'peso'):
                mapping['weight'] = col_idx
            elif col_name in ('volume'):
                mapping['volume'] = col_idx
            elif col_name in ('sale_ok', 'pode ser vendido', 'can be sold'):
                mapping['sale_ok'] = col_idx
            elif col_name in ('purchase_ok', 'pode ser comprado', 'can be purchased'):
                mapping['purchase_ok'] = col_idx
            elif col_name in ('active', 'ativo'):
                mapping['active'] = col_idx
            elif col_name in ('channel_price', 'preço no canal', 'preço específico', 'specific price'):
                mapping['channel_price'] = col_idx
        
        # Verificar campos obrigatórios
        if mapping['default_code'] == -1 and mapping['name'] == -1:
            raise UserError(_('O arquivo deve conter pelo menos uma coluna para identificar o produto (Código ou Nome).'))
        
        return mapping
    
    def _create_or_update_product(self, vals):
        """Cria ou atualiza um produto com os valores fornecidos."""
        product = None
        
        # Buscar produto existente
        if 'default_code' in vals and vals['default_code']:
            product = self.env['product.template'].search([
                ('default_code', '=', vals['default_code'])
            ], limit=1)
        
        if not product and 'name' in vals and vals['name']:
            product = self.env['product.template'].search([
                ('name', '=', vals['name'])
            ], limit=1)
        
        # Preparar valores para criação/atualização
        product_vals = self._prepare_product_values(vals)
        
        # Se não encontrou produto e tem dados suficientes, criar novo
        if not product and 'name' in vals and vals['name']:
            product = self.env['product.template'].create(product_vals)
            _logger.info(f"Produto criado: {product.name} (ID: {product.id})")
        
        # Se encontrou produto, atualizar
        elif product:
            product.write(product_vals)
            _logger.info(f"Produto atualizado: {product.name} (ID: {product.id})")
        
        # Atualizar data de importação
        if product:
            product.last_import_date = fields.Datetime.now()
        
        return product
    
    def _prepare_product_values(self, vals):
        """Prepara os valores para criação/atualização de produto."""
        product_vals = {}
        
        # Mapear valores para campos do produto
        if 'name' in vals and vals['name']:
            product_vals['name'] = vals['name']
        
        if 'default_code' in vals and vals['default_code']:
            product_vals['default_code'] = vals['default_code']
        
        if 'list_price' in vals and vals['list_price']:
            try:
                product_vals['list_price'] = float(vals['list_price'])
            except (ValueError, TypeError):
                pass
        
        if 'standard_price' in vals and vals['standard_price']:
            try:
                product_vals['standard_price'] = float(vals['standard_price'])
            except (ValueError, TypeError):
                pass
        
        if 'barcode' in vals and vals['barcode']:
            product_vals['barcode'] = vals['barcode']
        
        if 'description' in vals and vals['description']:
            product_vals['description'] = vals['description']
        
        if 'description_sale' in vals and vals['description_sale']:
            product_vals['description_sale'] = vals['description_sale']
        
        if 'weight' in vals and vals['weight']:
            try:
                product_vals['weight'] = float(vals['weight'])
            except (ValueError, TypeError):
                pass
        
        if 'volume' in vals and vals['volume']:
            try:
                product_vals['volume'] = float(vals['volume'])
            except (ValueError, TypeError):
                pass
        
        if 'sale_ok' in vals:
            product_vals['sale_ok'] = vals['sale_ok'] in ('True', 'true', '1', 'Yes', 'yes', 'Sim', 'sim', True, 1)
        
        if 'purchase_ok' in vals:
            product_vals['purchase_ok'] = vals['purchase_ok'] in ('True', 'true', '1', 'Yes', 'yes', 'Sim', 'sim', True, 1)
        
        if 'active' in vals:
            product_vals['active'] = vals['active'] in ('True', 'true', '1', 'Yes', 'yes', 'Sim', 'sim', True, 1)
        
        # Processar categoria se fornecida
        if 'categ_id' in vals and vals['categ_id']:
            category = self.env['product.category'].search([
                ('name', '=', vals['categ_id'])
            ], limit=1)
            
            if not category:
                category = self.env['product.category'].create({
                    'name': vals['categ_id']
                })
            
            product_vals['categ_id'] = category.id
        
        # Processar unidade de medida se fornecida
        if 'uom_id' in vals and vals['uom_id']:
            uom = self.env['uom.uom'].search([
                ('name', '=', vals['uom_id'])
            ], limit=1)
            
            if uom:
                product_vals['uom_id'] = uom.id
        
        # Processar tipo de produto se fornecido
        if 'type' in vals and vals['type']:
            type_mapping = {
                'consumable': 'consu',
                'consumível': 'consu',
                'service': 'service',
                'serviço': 'service',
                'stockable': 'product',
                'estocável': 'product',
                'product': 'product',
                'produto': 'product'
            }
            
            product_type = type_mapping.get(vals['type'].lower(), 'product')
            product_vals['type'] = product_type
        
        return product_vals
    
    def _ensure_channel_mapping(self, product, channel, vals=None):
        """Garante que o produto tenha um mapeamento para o canal especificado."""
        # Buscar mapeamento existente
        mapping = self.env['product.channel.mapping'].search([
            ('product_id', '=', product.id),
            ('channel_id', '=', channel.id)
        ], limit=1)
        
        # Determinar preço específico
        specific_price = product.list_price
        use_specific_price = False
        
        if vals and 'channel_price' in vals and vals['channel_price']:
            try:
                specific_price = float(vals['channel_price'])
                use_specific_price = True
            except (ValueError, TypeError):
                pass
        
        # Se não existe, criar
        if not mapping:
            mapping = self.env['product.channel.mapping'].create({
                'product_id': product.id,
                'channel_id': channel.id,
                'specific_price': specific_price,
                'use_specific_price': use_specific_price,
                'sync_status': 'not_synced'
            })
        # Se existe, atualizar apenas se tiver preço específico
        elif use_specific_price:
            mapping.write({
                'specific_price': specific_price,
                'use_specific_price': True,
                'sync_status': 'needs_update'
            })
        
        return mapping
    
    def _get_or_create_ai_channel(self):
        """Obtém ou cria o canal de IA."""
        ai_channel = self.env['product.sales.channel'].search([
            ('code', '=', 'ai_system')
        ], limit=1)
        
        if not ai_channel:
            ai_channel = self.env['product.sales.channel'].create({
                'name': 'Sistema de IA',
                'code': 'ai_system',
                'description': 'Canal para o sistema de IA',
                'price_multiplier': 1.0,
                'auto_sync': True,
                'color': 1
            })
        
        return ai_channel
